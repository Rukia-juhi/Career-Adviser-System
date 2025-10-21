# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from models import db, User, Career, Skill, CareerSkillRequirement, UserSkill, Plan, PlanStep, Resource
from datetime import datetime
from flask import session, flash
from werkzeug.security import generate_password_hash, check_password_hash


# ----------- NEW: Roadmap helpers (pure read-only) -----------
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
    phases = []
    if missing_skills:
        steps = []
        for s in missing_skills:
            res = " • ".join(SKILL_RESOURCES.get(s.lower(), [])[:2]) or "Pick a beginner resource"
            steps.append(f"Learn the basics of {s} (2–3 weeks). Suggested: {res}.")
        phases.append({'title': 'Foundations', 'steps': steps})
    phases.append({'title': 'Core Practice', 'steps': [
        f"Do 3–5 medium practice sets for {s}. Summarize notes in a wiki/notion." for s in required_skills
    ]})
    phases.append({'title': 'Projects', 'steps': [
        "Build Project 1: pick a small scoped idea (2 weeks).",
        "Build Project 2: increase scope, add 1 new concept (APIs, auth, charts, etc.).",
        "Write concise READMEs with screenshots; push everything to GitHub."
    ]})
    phases.append({'title': 'Portfolio', 'steps': [
        "Create a clean portfolio page (about, skills, 2 projects, contact).",
        "Polish LinkedIn: headline, summary, skills, project links.",
        "Prepare a 5-minute project walkthrough (story → demo → learning)."
    ]})
    phases.append({'title': 'Apply & Iterate', 'steps': [
        "Set a weekly target: 5 tailored applications + 1 coffee chat.",
        "Mock interviews weekly; log weak areas and revisit notes.",
        "Iterate projects based on feedback; ship small improvements weekly."
    ]})
    return phases
# ----------- end roadmap helpers -----------

# keep using templates only (no static folder)
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

# ----------- NEW: IntegrityError handling -----------
from sqlalchemy.exc import IntegrityError

@app.errorhandler(IntegrityError)
def handle_integrity_error(err):
    # ALWAYS rollback a failed transaction so subsequent requests can run
    db.session.rollback()
    # Show a friendly, actionable message in dev
    return (
        "Database integrity error (likely a duplicate or missing required field). "
        "Please go back and try again. Technical detail: "
        + str(err.orig if hasattr(err, 'orig') else err),
        500
    )
# -----------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # 🔒 Require login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get the logged-in user
    user = User.query.get(session['user_id'])
    if not user:
        # Session is stale or user deleted
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        interests = request.form.get('interests', '').strip()
        skills = request.form.get('skills', '').strip()

        if not name:
            return "Name required", 400

        # ✅ Update existing user instead of creating a new one
        user.name = name
        user.interests = interests
        user.skills_text = skills

        db.session.commit()

        # ✅ Update user skills table
        # First, clear old user_skills to avoid duplicates
        UserSkill.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # Then, add new skills
        for s in split_csv(skills):
            sk = Skill.query.filter_by(name=s.lower()).first()
            us = UserSkill(user_id=user.id, skill_id=sk.id if sk else None, name=s)
            try:
                db.session.add(us)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

        return redirect(url_for('recommend', user_id=user.id))

    # GET request: Prefill the form with existing values
    return render_template(
        'profile.html',
        name=user.name or '',
        interests=user.interests or '',
        skills=user.skills_text or ''
    )


@app.route('/recommend/<int:user_id>')
def recommend(user_id):
    # ----------- NEW: defensive rollback -----------
    # If a prior request hit an IntegrityError, make sure this session is clean.
    try:
        db.session.rollback()
    except Exception:
        pass
    # -----------------------------------------------

    user = User.query.get_or_404(user_id)

    # get user's skills set (lowercased)
    user_skills = {s.name.lower() for s in user.skills if s.name} if user.skills else set()
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

    # prepare recs for template (career title + skills list) + roadmap
    recs = []
    gaps = {}
    roadmaps = {}  # NEW
    for career, reqs, _ in candidates:
        required_skills = [s for s in reqs]
        recs.append({'career': career.title, 'skills': required_skills})
        missing = [r for r in required_skills if r.lower() not in user_skills]
        gaps[career.title] = missing
        roadmaps[career.title] = build_roadmap(career.title, required_skills, missing)  # NEW

    return render_template('recommend.html', user=user, recs=recs, gaps=gaps, roadmaps=roadmaps)  # +roadmaps

@app.route('/save_plan/<int:user_id>', methods=['POST'])
def save_plan(user_id):
    user = User.query.get_or_404(user_id)
    career_title = request.form.get('career') or request.json and request.json.get('career')
    if not career_title:
        return jsonify({'success': False, 'message': 'Career required'}), 400

    try:
        # find or create career entry
        career = Career.query.filter(Career.title == career_title).first()
        if career is None:
            career = Career(title=career_title)
            db.session.add(career)
            db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Could not create career: {e.orig}'}), 400

    try:
        plan = Plan(user_id=user.id, career_id=career.id, title=f'Roadmap for {career.title}')
        db.session.add(plan)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        # If you later add a unique constraint for (user_id, career_id), this handles duplicates
        return jsonify({'success': False, 'message': f'Could not create plan: {e.orig}'}), 400

    # create simple default steps for missing skills
    missing = request.form.getlist('missing') or []
    if not missing:
        reqs = [req.skill.name.lower() for req in career.requirements if req.skill]
        user_skills = set([s.name.lower() for s in user.user_skills if s.name]) or set([x.lower() for x in split_csv(user.skills_text)])
        missing = [r for r in reqs if r.lower() not in user_skills]

    # NEW: build & persist roadmap steps
    required = [req.skill.name.lower() for req in career.requirements if req.skill]
    phases = build_roadmap(career.title, required, missing)

    order = 1
    for ph in phases:
        for step in ph['steps']:
            try:
                db.session.add(PlanStep(plan_id=plan.id, title=f"{ph['title']}: {step}", sort_order=order))
                db.session.commit()
                order += 1
            except IntegrityError:
                db.session.rollback()  # skip duplicate step titles/order if any and continue

    # keep your original extra project step (harmless if similar)
    try:
        db.session.add(PlanStep(plan_id=plan.id, title='Build a small project to demonstrate skills', sort_order=order))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    return jsonify({'success': True, 'message': f'Plan saved for {career.title}', 'plan_id': plan.id})

@app.route('/resources')
def resources():
    career_query = request.args.get('career','').strip()
    if career_query:
        career = Career.query.filter(Career.title.ilike(f'%{career_query}%')).first()
        if career:
            res = set()
            for r in career.resources:
                res.add((r.title, r.url))
            for req in career.requirements:
                for r in req.skill.resources:
                    res.add((r.title, r.url))
            out = [{'title': t, 'url': u} for t,u in res]
            return jsonify({'career': career.title, 'resources': out})
        else:
            return jsonify({'career': career_query, 'resources': []})
    resources = Resource.query.limit(20).all()
    out = [{'title': r.title, 'url': r.url} for r in resources]
    return jsonify({'resources': out})

@app.route('/debug/users')
def debug_users():
    users = User.query.all()
    return jsonify([{'id':u.id,'name':u.name,'interests':u.interests,'skills_text':u.skills_text} for u in users])

# -------------------- AUTH ROUTES --------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # check if email exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.')
            flash('Account created successfully! Please log in.', 'success')
            flash('Email already registered. Please log in.', 'error')

            return redirect(url_for('login'))

        # create new user
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for('signup'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.")
            return redirect(url_for('login'))

        hashed_pw = generate_password_hash(password)
        new_user = User(name=name, email=email, password_hash=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please log in.")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('profile'))
        else:
            flash('Invalid email or password. Please try again.')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Pin to localhost:5000 explicitly (no change for linkage)
    app.run(host='127.0.0.1', port=5000, debug=True)
