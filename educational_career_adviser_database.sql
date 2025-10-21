-- Educational & Career Path Adviser
-- Complete database schema (PostgreSQL dialect). Includes tables, constraints, indexes, and sample data.
-- File: Educational_Career_Adviser_Database.sql
-- Purpose: Use as the starting SQL DDL for the project. Adjust types for MySQL/SQLite as needed.

-- ==========================================================
-- SCHEMA: core
-- ==========================================================

-- Users: students, teachers, admins
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student','teacher','admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Profiles: extended user information
CREATE TABLE profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    gender VARCHAR(20),
    location VARCHAR(255),
    bio TEXT,
    phone VARCHAR(30),
    avatar_url TEXT
);

-- Interests: e.g., programming, biology, design
CREATE TABLE interests (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- User <-> Interest (many-to-many)
CREATE TABLE user_interests (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    interest_id BIGINT REFERENCES interests(id) ON DELETE CASCADE,
    confidence SMALLINT CHECK (confidence >= 0 AND confidence <= 100),
    PRIMARY KEY (user_id, interest_id)
);

-- Skills: atomic skills (python, lab-techniques, communication)
CREATE TABLE skills (
    id BIGSERIAL PRIMARY KEY,
    slug VARCHAR(150) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT
);

-- User skills (self-declared or assessed)
CREATE TABLE user_skills (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    skill_id BIGINT REFERENCES skills(id) ON DELETE CASCADE,
    level SMALLINT DEFAULT 0 CHECK (level >= 0 AND level <= 100), -- percent or score
    source VARCHAR(100), -- 'self','assessment','course'
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (user_id, skill_id)
);

-- Careers / Occupations
CREATE TABLE careers (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    overview TEXT,
    typical_education TEXT,
    median_salary BIGINT,
    growth_outlook VARCHAR(100)
);

-- Many-to-many: career required skills with weight/importance
CREATE TABLE career_skills (
    career_id BIGINT REFERENCES careers(id) ON DELETE CASCADE,
    skill_id BIGINT REFERENCES skills(id) ON DELETE CASCADE,
    importance SMALLINT DEFAULT 50 CHECK (importance >= 0 AND importance <= 100),
    PRIMARY KEY (career_id, skill_id)
);

-- Resources: courses, articles, certifications
CREATE TABLE resources (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('course','article','video','certificate','internship','book')),
    provider VARCHAR(255),
    url TEXT,
    duration_minutes INT,
    cost NUMERIC(10,2),
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Map resources to skills
CREATE TABLE resource_skills (
    resource_id BIGINT REFERENCES resources(id) ON DELETE CASCADE,
    skill_id BIGINT REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (resource_id, skill_id)
);

-- Map careers to recommended resources
CREATE TABLE career_resources (
    career_id BIGINT REFERENCES careers(id) ON DELETE CASCADE,
    resource_id BIGINT REFERENCES resources(id) ON DELETE CASCADE,
    priority SMALLINT DEFAULT 50,
    PRIMARY KEY (career_id, resource_id)
);

-- Assessments & quizzes (to capture results of personality/aptitude tests)
CREATE TABLE assessments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    assessment_type VARCHAR(100), -- e.g., 'aptitude-v1','mbti-lite'
    score JSONB,
    taken_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Recommendations: generated suggestions + rationale
CREATE TABLE recommendations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    career_id BIGINT REFERENCES careers(id),
    score NUMERIC(5,2), -- suitability score
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    source VARCHAR(50), -- 'rule-based','ml','expert'
    rationale TEXT
);

-- Roadmaps: personalized step-by-step plan (order matters)
CREATE TABLE roadmap_steps (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    step_order INT NOT NULL,
    due_date DATE,
    done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Institutions & Programs (colleges, degrees)
CREATE TABLE institutions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    website TEXT
);

CREATE TABLE programs (
    id BIGSERIAL PRIMARY KEY,
    institution_id BIGINT REFERENCES institutions(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    degree_type VARCHAR(100), -- e.g., 'B.Tech', 'BSc', 'MBA'
    duration_months INT,
    description TEXT
);

-- Map careers to typical programs
CREATE TABLE career_programs (
    career_id BIGINT REFERENCES careers(id) ON DELETE CASCADE,
    program_id BIGINT REFERENCES programs(id) ON DELETE CASCADE,
    PRIMARY KEY (career_id, program_id)
);

-- Chat/messages between users
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    sender_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    receiver_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    body TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    read_at TIMESTAMP WITH TIME ZONE
);

-- Notifications
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    body TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Files/uploads (notes, assignments, resumes)
CREATE TABLE uploads (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    file_name VARCHAR(255),
    file_type VARCHAR(100),
    url TEXT,
    size_bytes BIGINT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    context VARCHAR(100) -- e.g., 'resume','assignment','note'
);

-- Assignments (if the platform supports coursework)
CREATE TABLE assignments (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE assignment_submissions (
    id BIGSERIAL PRIMARY KEY,
    assignment_id BIGINT REFERENCES assignments(id) ON DELETE CASCADE,
    submitted_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    upload_id BIGINT REFERENCES uploads(id) ON DELETE SET NULL,
    marks NUMERIC(6,2),
    feedback TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Admin/audit logs
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    details JSONB
);

-- ==========================================================
-- INDEXES and helpful views
-- ==========================================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_profiles_name ON profiles(first_name, last_name);
CREATE INDEX idx_skills_slug ON skills(slug);
CREATE INDEX idx_careers_slug ON careers(slug);
CREATE INDEX idx_resources_tags ON resources USING gin (tags);

-- Example view: user's top recommended careers (latest recommendation per career)
CREATE VIEW user_career_recs AS
SELECT r.user_id, r.career_id, c.title, r.score, r.created_at
FROM recommendations r
JOIN careers c ON c.id = r.career_id
WHERE (r.user_id, r.career_id, r.created_at) IN (
    SELECT user_id, career_id, max(created_at) FROM recommendations GROUP BY user_id, career_id
);

-- ==========================================================
-- SAMPLE DATA (small set to bootstrap development/testing)
-- ==========================================================

-- users
INSERT INTO users (email, password_hash, role) VALUES
('alice@student.edu','hash_alice','student'),
('bob@teacher.edu','hash_bob','teacher'),
('claire@admin.edu','hash_claire','admin');

-- profiles
INSERT INTO profiles (user_id, first_name, last_name, dob, location, bio) VALUES
(1,'Alice','Kumar','2005-10-18','Pathanamthitta, Kerala','Interested in biology and data'),
(2,'Bob','Thomas','1985-06-05','Chennai','Faculty - Computer Science'),
(3,'Claire','Admin','1990-01-01','Bengaluru','Platform admin');

-- interests
INSERT INTO interests (name, description) VALUES
('programming','Software development and coding'),
('biology','Life sciences and research'),
('data','Data analysis & ML');

-- skills
INSERT INTO skills (slug,name,description) VALUES
('python','Python','General purpose programming language'),
('data-structures','Data Structures','Algorithms and structures'),
('molecular-bio','Molecular Biology','Lab techniques and theory');

-- careers
INSERT INTO careers (title,slug,overview,typical_education) VALUES
('Software Engineer','software-engineer','Build software products','B.Tech/BS in CS or related'),
('Biotech Researcher','biotech-researcher','Research in biological sciences','BSc/MSc/PhD in life sciences');

-- career_skills
INSERT INTO career_skills (career_id, skill_id, importance) VALUES
(1,1,90),(1,2,85),(2,3,95);

-- resources
INSERT INTO resources (title,type,provider,url,duration_minutes,cost,tags) VALUES
('Intro to Python','course','Coursera','https://example.com/python',600,0.00,array['python','programming']),
('Molecular Biology Basics','course','edX','https://example.com/mmbio',480,0.00,array['molecular-bio','biology']);

-- resource_skills
INSERT INTO resource_skills (resource_id,skill_id) VALUES
(1,1),(2,3);

-- career_resources
INSERT INTO career_resources (career_id, resource_id, priority) VALUES
(1,1,90),(2,2,90);

-- user_interests
INSERT INTO user_interests(user_id, interest_id, confidence) VALUES
(1,2,80),(1,3,60);

-- user_skills
INSERT INTO user_skills(user_id, skill_id, level, source) VALUES
(1,3,30,'self');

-- recommendations
INSERT INTO recommendations(user_id, career_id, score, source, rationale) VALUES
(1,1,42.50,'rule-based','Has interest in data, needs foundational skills in programming'),
(1,2,68.00,'rule-based','Strong interest in biology with some lab exposure');

-- roadmap_steps
INSERT INTO roadmap_steps(user_id,title,description,step_order,due_date) VALUES
(1,'Take Intro to Python','Complete the Intro to Python course on Coursera',1,'2025-12-31'),
(1,'Join lab volunteer','Find a lab internship at local college',2,'2026-06-30');

-- assessments
INSERT INTO assessments (user_id, assessment_type, score) VALUES
(1,'aptitude-v1','{"math":70,"verbal":60}');

-- uploads
INSERT INTO uploads (user_id,file_name,file_type,url,size_bytes,context) VALUES
(1,'alice_resume.pdf','application/pdf','https://storage.example.com/alice_resume.pdf',34567,'resume');

-- ==========================================================
-- NOTES & NEXT STEPS
-- - Adjust types if you prefer UUIDs (use uuid_generate_v4()).
-- - To port to MySQL: replace JSONB with JSON (or TEXT), remove 'WITH TIME ZONE' if needed, and replace arrays with a mapping table.
-- - Hook ML tables: you may add "models","model_runs" and store feature snapshots.
-- - Add FK ON UPDATE/DELETE policies according to app logic.
-- ==========================================================

-- End of Educational & Career Adviser database schema
