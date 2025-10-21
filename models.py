# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ----------------
# Core tables
# ----------------
class User(db.Model):
    __tablename__ = 'users'
    # use Integer so SQLite auto-increments the primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # NEW fields
    name = db.Column(db.String(255), nullable=True)
    interests = db.Column(db.Text, nullable=True)
    skills_text = db.Column(db.Text, nullable=True)

    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    last_login = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, default=True)

    profile = db.relationship("Profile", back_populates="user", uselist=False)
    skills = db.relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    plans = db.relationship("Plan", back_populates="user", cascade="all, delete-orphan")

class Profile(db.Model):
    __tablename__ = 'profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    location = db.Column(db.String(255))
    bio = db.Column(db.Text)

    user = db.relationship("User", back_populates="profile")


class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)

    users = db.relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")
    career_links = db.relationship("CareerSkillRequirement", back_populates="skill", cascade="all, delete-orphan")


class UserSkill(db.Model):
    __tablename__ = 'user_skills'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=True)
    name = db.Column(db.String(255))  # textual fallback if skill_id is None
    proficiency_level = db.Column(db.String(50))
    years_experience = db.Column(db.Integer)

    user = db.relationship("User", back_populates="skills")
    skill = db.relationship("Skill", back_populates="users")


# ----------------
# Careers & Requirements
# ----------------
class Career(db.Model):
    __tablename__ = 'careers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    avg_salary = db.Column(db.Numeric)
    growth_rate = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    requirements = db.relationship("CareerSkillRequirement", back_populates="career", cascade="all, delete-orphan")
    resources = db.relationship("Resource", back_populates="career", cascade="all, delete-orphan")
    plans = db.relationship("Plan", back_populates="career", cascade="all, delete-orphan")


class CareerSkillRequirement(db.Model):
    __tablename__ = 'career_skills'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    career_id = db.Column(db.Integer, db.ForeignKey('careers.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    importance_level = db.Column(db.String(50))

    career = db.relationship("Career", back_populates="requirements")
    skill = db.relationship("Skill", back_populates="career_links")


# ----------------
# Plans & Steps
# ----------------
class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    career_id = db.Column(db.Integer, db.ForeignKey('careers.id'), nullable=True)
    title = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    user = db.relationship("User", back_populates="plans")
    career = db.relationship("Career", back_populates="plans")
    steps = db.relationship("PlanStep", back_populates="plan", cascade="all, delete-orphan", order_by="PlanStep.sort_order")


class PlanStep(db.Model):
    __tablename__ = 'plan_steps'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)

    plan = db.relationship("Plan", back_populates="steps")


# ----------------
# Resources
# ----------------
class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    career_id = db.Column(db.Integer, db.ForeignKey('careers.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(2000))
    type = db.Column(db.String(50))  # e.g., book, course, video

    # portable JSON column (works with SQLite and Postgres)
    metadata_json = db.Column(db.JSON, nullable=True)

    # tags can be stored as JSON list (portable across SQLite/Postgres)
    tags = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    career = db.relationship("Career", back_populates="resources")
