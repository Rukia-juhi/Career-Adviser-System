# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from models import db, User, Career, Skill, CareerSkillRequirement, UserSkill, Plan, PlanStep, Resource
from datetime import datetime

# ---------- Roadmap helpers (added) ----------
SKILL_RESOURCES = {
    'python': ['Official Python Tutorial', 'Automate the Boring Stuff'],
    'sql': ['SQLBolt', 'Mode SQL Tutorial'],
    'data-structures': ['NeetCode Roadmap', 'CS50 Data Structures'],
    'statistics': ['Khan Academy Stats', 'Think Stats (book)'],
    'algorithms': ['Grokking Algorithms', 'CLRS (chapters 1–4)'],
    'figma': ['Figma Learn', 'Build a UI Kit'],
    'design-principles': ['Laws of UX', 'Refactoring UI'],
}

def build_roadmap(career_title: str, required_skills: list[str], missing_skills: list[str]) -> list[dict]:
    """Return a list of roadmap phases with steps."""
    phases = []

    # 1) Foundations (only for missing skills)
    if missing_skills:
        steps = []
        for s in missing_skills:
            res = " • ".join(SKILL_RESOURCES.get(s.lower(), [])[:2]) or "Pick a beginner resource"
            steps.append(f"Learn the basics of {s} (2–3 weeks). Suggested: {res}.")
        phases.append({'title': 'Foundations', 'steps': steps})

    # 2) Core practice
    core_steps = [f"Do 3–5 medium practice sets for {s}. Summarize notes in a wiki/notion."
                  for s in required_skills]
    phases.append({'title': 'Core Practice', 'steps': core_steps})

    # 3) Projects
    phases.append({'title': 'Projects', 'steps': [
        "Build Project 1: pick a small scoped idea (2 weeks).",
        "Build Project 2: increase scope, add 1 new concept (APIs, auth, charts, etc.).",
        "Write concise READMEs with screenshots; push everything to GitHub."
    ]})

    # 4) Portfolio & Profile
    phases.append({'title': 'Portfolio', 'steps': [
        "Create a clean portfolio page (about, skills, 2 projects, contact).",
        "Polish LinkedIn: headline, summary, skills, project links.",
        "Prepare a 5-minute project walkthrough (story → demo → learning)."
    ]})

    # 5) Apply & Iterate
    phases.append({'title': 'Apply & Iterate', 'steps': [
        "Set a weekly target: 5 tailored applications + 1 coffee chat.",
        "Mock interviews weekly; keep a log of weak areas and revisit notes.",
        "Iterate projects based on feedback; ship small improvements weekly."
    ]})

    return phases
# ---------- end helpers ----------

# keep your original app construction (no static folder required for inline CSS)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=None)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev-secret'  # change for production

db.init_app(app)

# helper to parse comma separated list
def split_csv(value):
    return [s.strip() for s in (value or '').split(',') if s.strip()]

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    # home page
    return render_template('index.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        interests = request.form.get('interests','').strip()
        skills = request.form.get('skills','').strip()
        if not name:
            return "Name required", 400

        user = User(name=name, interests=interests, skills_text=skills)
        db.session.add(user)
        db.session.commit()

        # optional: add normalized UserSkill rows for each skill if they exist in Skill table
        for s in split_csv(skills):
            # try to find matching skill
            sk = Skill.query.filter_by(name=s.lower()).first()
            us = UserSkill(user_id=user.id, skill_id=sk.id if sk else None, name=s, proficiency=None)
            db.session.add(us)
        db.session.commit()

        return redirect(url_for('recommend', user_id=user.id))
    # GET: show create profile page
    return render_template('profile.html')

@app.route('/recommend/<int:user_id>')
def recommend(user_id):
    user = User.query.get_or_404(user_id)

    # get user's skills set (lowercased)
    user_skills = {s.name.lower() for s in user.user_skills if s.name} if user.user_skills else set()
    # fallback to skills_text
    if not user_skills and user.skills_text:
        user_skills = set([x.lower() for x in split_csv(user.skills_text)])

    # simple rule: find careers that share keywords in user's interests OR have overlapping required skills
    interests = split_csv(user.interests)
    interest_lower = [i.lower() for i in interests]

    # collect candidate careers
    candidates = []
    for career in Career.query.all():
        score = 0
        # match by interest keyword in career title
        for it in interest_lower:
            if it in (career.title or '').lower():
                score += 1.0
        # match by overlapping skills
        reqs = [req.skill.name.lower() for req in career.requirements if req.skill and req.skill.name]
        overlap = len(set(reqs) & user_skills)
        score += overlap * 0.8
        if score > 0 or overlap > 0:
            candidates.append((career, reqs, score))

    # if none found, fallback to top careers
    if not candidates:
        candidates = [(c, [req.skill.name for req in c.requirements if req.skill], 0) for c in Career.query.limit(5).all()]

    # sort candidates by score desc
    candidates.sort(key=lambda x: x[2], reverse=True)

    # prepare recs for template (career title + skills list)
    recs = []
    gaps = {}
    roadmaps = {}  # added
    for career, reqs, _ in candidates:
        required_skills = [s for s in reqs]
        recs.append({'career': career.title, 'skills': required_skills})
        missing = [r for r in required_skills if r.lower() not in user_skills]
        gaps[career.title] = missing
        # build roadmap per career (added)
        roadmaps[career.title] = build_roadmap(career.title, required_skills, missing)

    # pass roadmaps to template (template can ignore it if not used)
    return render_template('recommend.html', user=user, recs=recs, gaps=gaps, roadmaps=roadmaps)

@app.route('/save_plan/<int:user_id>', methods=['POST'])
def save_plan(user_id):
    user = User.query.get_or_404(user_id)
    career_title = request.form.get('career') or request.json and request.json.get('career')
    if not career_title:
        return jsonify({'success': False, 'message': 'Career required'}), 400

    # find or create career entry
    career = Career.query.filter(Career.title == career_title).first()
    if career is None:
        career = Career(title=career_title)
        db.session.add(career)
        db.session.commit()

    plan = Plan(user_id=user.id, career_id=career.id, title=f'Roadmap for {career.title}')
    db.session.add(plan)
    db.session.commit()

    # create simple default steps for missing skills
    missing = request.form.getlist('missing') or []  # if client sent missing skills

    # fallback: compute same as recommend route
    if not missing:
        reqs = [req.skill.name.lower() for req in career.requirements if req.skill]
        user_skills = set([s.name.lower() for s in user.user_skills if s.name]) or set([x.lower() for x in split_csv(user.skills_text)])
        missing = [r for r in reqs if r.lower() not in user_skills]

    # Build a roadmap and persist each step (added)
    required = [req.skill.name.lower() for req in career.requirements if req.skill]
    phases = build_roadmap(career.title, required, missing)

    order = 1
    for ph in phases:
        for step in ph['steps']:
            db.session.add(PlanStep(plan_id=plan.id, title=f"{ph['title']}: {step}", sort_order=order))
            order += 1

    # always add a project step (kept from your logic, harmless duplicate of phase if present)
    step = PlanStep(plan_id=plan.id, title='Build a small project to demonstrate skills', sort_order=order)
    db.session.add(step)

    db.session.commit()
    return jsonify({'success': True, 'message': f'Plan saved for {career.title}', 'plan_id': plan.id})

@app.route('/resources')
def resources():
    career_query = request.args.get('career','').strip()
    if career_query:
        career = Career.query.filter(Career.title.ilike(f'%{career_query}%')).first()
        if career:
            # gather resources associated with career or with required skills
            res = set()
            for r in career.resources:
                res.add((r.title, r.url))
            # resources via skills
            for req in career.requirements:
                for r in req.skill.resources:
                    res.add((r.title, r.url))
            out = [{'title': t, 'url': u} for t,u in res]
            return jsonify({'career': career.title, 'resources': out})
        else:
            return jsonify({'career': career_query, 'resources': []})
    # default: return popular resources
    resources = Resource.query.limit(20).all()
    out = [{'title': r.title, 'url': r.url} for r in resources]
    return jsonify({'resources': out})

# simple debug route
@app.route('/debug/users')
def debug_users():
    users = User.query.all()
    return jsonify([{'id':u.id,'name':u.name,'interests':u.interests,'skills_text':u.skills_text} for u in users])

if __name__ == '__main__':
    app.run(debug=True)
