# seed_db.py
"""
Seed the database with careers, skills, requirements, and a few resources.

Run from the project folder (same place as app.py):
  - Terminal/CMD:   python seed_db.py
  - Spyder IPython: %run seed_db.py
Add --reset to drop & recreate tables first:
  - python seed_db.py --reset
  - %run seed_db.py --reset
"""
import sys
from app import app, db
from models import Skill, Career, CareerSkillRequirement

# Try to import Resource if it exists in your models
try:
    from models import Resource
    HAVE_RESOURCE = True
except Exception:
    HAVE_RESOURCE = False

# ---------- helpers ----------
def get_or_create_skill(name, desc=None):
    s = Skill.query.filter_by(name=name).first()
    if not s:
        s = Skill(name=name, description=desc)
        db.session.add(s)
        db.session.flush()
    return s

def get_or_create_career(title, overview=None):
    c = Career.query.filter_by(title=title).first()
    if not c:
        # your model uses `overview` (earlier) – if not, just title is fine
        try:
            c = Career(title=title, overview=overview)
        except TypeError:
            c = Career(title=title)
        db.session.add(c)
        db.session.flush()
    return c

def ensure_req(career, skill, importance=1.0, level=None, notes=None):
    exists = CareerSkillRequirement.query.filter_by(
        career_id=career.id, skill_id=skill.id
    ).first()
    if not exists:
        try:
            db.session.add(CareerSkillRequirement(
                career_id=career.id,
                skill_id=skill.id,
                importance=importance,
                level=level,
                notes=notes
            ))
        except TypeError:
            # if your CSR model only has (career_id, skill_id)
            db.session.add(CareerSkillRequirement(
                career_id=career.id, skill_id=skill.id
            ))

def add_resource_safe(title, url=None, rtype=None, provider=None, description=None):
    """Create Resource if model exists and supports these fields."""
    if not HAVE_RESOURCE:
        return None
    # find existing by title
    r = Resource.query.filter_by(title=title).first()
    if r:
        return r
    # be tolerant to model signature differences
    try:
        r = Resource(title=title, url=url, resource_type=rtype,
                     provider=provider, description=description)
    except TypeError:
        try:
            r = Resource(title=title, url=url)
        except TypeError:
            r = Resource(title=title)
    db.session.add(r)
    db.session.flush()
    return r

def link_resource_to_skill(resource, skill):
    if not (HAVE_RESOURCE and resource): return
    if hasattr(resource, "skills") and skill not in resource.skills:
        resource.skills.append(skill)

def link_resource_to_career(resource, career):
    if not (HAVE_RESOURCE and resource): return
    if hasattr(resource, "careers") and career not in resource.careers:
        resource.careers.append(career)

# ---------- data ----------
SKILLS = [
    'python','java','javascript','html','css','react','node','data-structures','algorithms','git','linux',
    'sql','statistics','data-analysis','machine-learning','deep-learning','pandas','numpy','powerbi','tableau',
    'aws','docker','kubernetes','bash',
    'networking','security-basics',
    'figma','design-principles','ux-research',
    'communication','problem-solving','spreadsheets'
]

CAREERS = {
    'Software Engineer': [
        ('python',1.0,'intermediate'),('java',0.7,'intermediate'),
        ('data-structures',1.0,'intermediate'),('algorithms',1.0,'intermediate'),
        ('git',0.8,'intermediate'),('linux',0.6,'beginner')
    ],
    'Front-end Developer': [
        ('html',1.0,'intermediate'),('css',1.0,'intermediate'),
        ('javascript',1.0,'intermediate'),('react',0.9,'beginner'),
        ('git',0.7,'beginner'),('design-principles',0.5,'beginner')
    ],
    'Back-end Developer': [
        ('python',1.0,'intermediate'),('node',0.8,'beginner'),
        ('sql',1.0,'intermediate'),('data-structures',0.9,'intermediate'),
        ('linux',0.8,'beginner'),('docker',0.6,'beginner')
    ],
    'Data Analyst': [
        ('sql',1.0,'intermediate'),('spreadsheets',1.0,'intermediate'),
        ('data-analysis',1.0,'intermediate'),('statistics',0.9,'beginner'),
        ('powerbi',0.7,'beginner'),('tableau',0.7,'beginner'),
        ('python',0.6,'beginner')
    ],
    'Data Scientist': [
        ('python',1.0,'intermediate'),('statistics',1.0,'intermediate'),
        ('machine-learning',1.0,'intermediate'),('pandas',0.9,'intermediate'),
        ('numpy',0.9,'intermediate'),('sql',0.8,'beginner'),
        ('deep-learning',0.7,'beginner')
    ],
    'ML Engineer': [
        ('python',1.0,'intermediate'),('machine-learning',1.0,'intermediate'),
        ('deep-learning',0.9,'beginner'),('docker',0.7,'beginner'),
        ('aws',0.7,'beginner'),('data-structures',0.8,'intermediate')
    ],
    'Cloud Engineer': [
        ('aws',1.0,'beginner'),('linux',0.9,'intermediate'),
        ('docker',0.8,'beginner'),('kubernetes',0.8,'beginner'),
        ('bash',0.7,'beginner'),('networking',0.7,'beginner')
    ],
    'Cybersecurity Analyst': [
        ('security-basics',1.0,'beginner'),('networking',1.0,'beginner'),
        ('linux',0.8,'beginner'),('bash',0.7,'beginner'),('python',0.6,'beginner')
    ],
    'Business Analyst': [
        ('spreadsheets',1.0,'intermediate'),('sql',0.9,'beginner'),
        ('communication',1.0,'intermediate'),('problem-solving',1.0,'intermediate'),
        ('powerbi',0.7,'beginner')
    ],
    'UI/UX Designer': [
        ('figma',1.0,'intermediate'),('design-principles',1.0,'intermediate'),
        ('ux-research',0.9,'beginner'),('communication',0.8,'intermediate'),
        ('html',0.4,'beginner')
    ],
}

RESOURCES = [
    # (title, url, type, provider, [skills], [careers])
    ('Automate the Boring Stuff with Python', 'https://automatetheboringstuff.com/', 'book', 'Al Sweigart',
     ['python'], ['Software Engineer','Data Analyst','Data Scientist']),
    ('CS50 Data Structures (Lecture)', 'https://cs50.harvard.edu/x/2024/notes/5/', 'article', 'Harvard',
     ['data-structures','algorithms'], ['Software Engineer','Back-end Developer']),
    ('SQLBolt', 'https://sqlbolt.com/', 'course', 'SQLBolt',
     ['sql'], ['Data Analyst','Back-end Developer']),
    ('Khan Academy — Statistics', 'https://www.khanacademy.org/math/statistics-probability', 'course', 'Khan Academy',
     ['statistics'], ['Data Scientist','Data Analyst']),
    ('React Docs — Learn', 'https://react.dev/learn', 'docs', 'Meta',
     ['react','javascript'], ['Front-end Developer']),
    ('Figma Learn', 'https://help.figma.com/hc/en-us/articles/360040514173-Get-started-with-Figma', 'guide', 'Figma',
     ['figma','design-principles'], ['UI/UX Designer']),
    ('Docker — Getting Started', 'https://docs.docker.com/get-started/', 'docs', 'Docker',
     ['docker'], ['Back-end Developer','ML Engineer','Cloud Engineer']),
    ('AWS Skill Builder (Free)', 'https://explore.skillbuilder.aws/', 'course', 'AWS',
     ['aws'], ['Cloud Engineer','ML Engineer']),
]

def main(reset=False):
    with app.app_context():
        if reset:
            db.drop_all()
            db.create_all()

        # skills
        for sk in SKILLS:
            get_or_create_skill(sk)
        db.session.commit()

        # careers + requirements
        for title, reqs in CAREERS.items():
            c = get_or_create_career(title)
            for (skill_name, importance, level) in reqs:
                s = get_or_create_skill(skill_name)
                ensure_req(c, s, importance=importance, level=level)
        db.session.commit()

        # resources (if your Resource model exists)
        if HAVE_RESOURCE:
            for title, url, rtype, provider, skill_names, career_titles in RESOURCES:
                r = add_resource_safe(title, url, rtype, provider)
                for sn in skill_names:
                    s = get_or_create_skill(sn)
                    link_resource_to_skill(r, s)
                for ct in career_titles:
                    c = get_or_create_career(ct)
                    link_resource_to_career(r, c)
            db.session.commit()

        # summary
        from sqlalchemy import func
        career_count = db.session.query(func.count(Career.id)).scalar()
        skill_count = db.session.query(func.count(Skill.id)).scalar()
        req_count = db.session.query(func.count(CareerSkillRequirement.id)).scalar()
        print(f"✅ Seed complete: {career_count} careers, {skill_count} skills, {req_count} requirements.")
        if HAVE_RESOURCE:
            print("   Resources also added.")
        print("   Try a profile like:")
        print("     Interests: programming, data")
        print("     Skills: python, sql")

if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    main(reset=reset_flag)
