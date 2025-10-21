-- Create the database
CREATE DATABASE IF NOT EXISTS career_adviser_db;
USE career_adviser_db;

-- Table 1: Users (Students and Mentors)
-- Stores basic user info, authentication, and role.
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Store hashed passwords (e.g., using bcrypt)
    role ENUM('student', 'mentor', 'admin') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Table 2: StudentProfiles
-- Collects interests, strengths, personality traits, goals (from profile builder and quizzes like MBTI).
CREATE TABLE StudentProfiles (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    age INT,
    grade_level VARCHAR(50),  -- e.g., 'Class 10', 'College Freshman'
    preferred_subjects TEXT,  -- JSON or comma-separated: e.g., 'biology,math'
    interests TEXT,  -- e.g., 'problem-solving, healthcare'
    strengths TEXT,  -- e.g., 'analytical thinking, communication'
    personality_traits VARCHAR(100),  -- e.g., 'INTJ (MBTI), Extraverted'
    career_goals TEXT,  -- Free-text input for NLP analysis
    location VARCHAR(100),  -- For region-specific recommendations
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Table 3: Careers
-- Stores career paths (e.g., Software Engineer, Doctor) with details for recommendations.
CREATE TABLE Careers (
    career_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,  -- e.g., 'Software Engineer'
    description TEXT,
    industry VARCHAR(50),  -- e.g., 'IT', 'Healthcare'
    avg_salary DECIMAL(10,2),  -- Optional, from job market API
    job_demand_rating INT,  -- 1-10 scale, updated via API
    required_education_level VARCHAR(50),  -- e.g., 'Bachelor's', 'Diploma'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_industry (industry)
);

-- Table 4: Skills
-- Core skills (e.g., Python Programming) for gap analysis and recommendations.
CREATE TABLE Skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,  -- e.g., 'Python Programming'
    category VARCHAR(50),  -- e.g., 'Technical', 'Soft Skills'
    description TEXT,
    level_required ENUM('Beginner', 'Intermediate', 'Advanced') DEFAULT 'Beginner',
    suggested_resources TEXT,  -- e.g., 'Coursera: Python for Everybody'
    INDEX idx_name (name),
    INDEX idx_category (category)
);

-- Table 5: CareerSkills (Many-to-Many Junction Table)
-- Links careers to required skills for gap analysis.
CREATE TABLE CareerSkills (
    career_id INT NOT NULL,
    skill_id INT NOT NULL,
    priority INT DEFAULT 1,  -- 1=High priority
    PRIMARY KEY (career_id, skill_id),
    FOREIGN KEY (career_id) REFERENCES Careers(career_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE
);

-- Table 6: EducationStreams
-- Education options (e.g., Science Stream, IT Certifications) linked to careers.
CREATE TABLE EducationStreams (
    stream_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,  -- e.g., 'Science (PCB)', 'B.Tech in Computer Science'
    type ENUM('School Stream', 'College Major', 'Certification', 'Vocational') NOT NULL,
    description TEXT,
    duration VARCHAR(20),  -- e.g., '3 years'
    entrance_exams TEXT,  -- e.g., 'JEE, NEET'
    linked_careers TEXT,  -- Comma-separated career_ids or JSON for flexibility
    cost_estimate DECIMAL(8,2),
    INDEX idx_name (name),
    INDEX idx_type (type)
);

-- Table 7: Recommendations
-- Stores personalized suggestions (from rule-based/ML engine) for a student.
CREATE TABLE Recommendations (
    rec_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    career_id INT,  -- NULL if recommending a stream
    stream_id INT,  -- NULL if recommending a career
    confidence_score DECIMAL(3,2),  -- 0-1 from ML model (e.g., Scikit-learn)
    rationale TEXT,  -- Explanation: e.g., 'Matches your biology interest and math strength'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (career_id) REFERENCES Careers(career_id) ON DELETE SET NULL,
    FOREIGN KEY (stream_id) REFERENCES EducationStreams(stream_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_confidence (confidence_score)
);

-- Table 8: Roadmaps
-- Interactive timelines/steps for a career/stream (e.g., Class 11 → Internships).
CREATE TABLE Roadmaps (
    roadmap_id INT AUTO_INCREMENT PRIMARY KEY,
    career_id INT NOT NULL,  -- Or stream_id if needed
    step_number INT NOT NULL,  -- Order: 1,2,3...
    step_title VARCHAR(100),  -- e.g., 'Choose Class 11 Subjects'
    step_description TEXT,
    estimated_duration VARCHAR(20),  -- e.g., '6 months'
    prerequisites TEXT,  -- Skills or previous steps
    resources TEXT,  -- Links to courses/internships
    FOREIGN KEY (career_id) REFERENCES Careers(career_id) ON DELETE CASCADE,
    UNIQUE KEY unique_step (career_id, step_number)  -- One step per position per career
);

-- Table 9: StudentSkills (Many-to-Many Junction for Student Progress)
-- Tracks student's current skills for gap analysis and updates.
CREATE TABLE StudentSkills (
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency_level ENUM('Beginner', 'Intermediate', 'Advanced', 'Expert') DEFAULT 'Beginner',
    acquired_date DATE,
    evidence TEXT,  -- e.g., 'Completed Coursera course'
    PRIMARY KEY (user_id, skill_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Table 10: Achievements
-- Progress tracking: courses, certifications, projects, internships.
CREATE TABLE Achievements (
    achievement_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,  -- e.g., 'Completed Python Certification'
    type ENUM('Course', 'Certification', 'Project', 'Internship', 'Exam') NOT NULL,
    description TEXT,
    completion_date DATE,
    skills_gained TEXT,  -- Comma-separated skill_ids
    certificate_url VARCHAR(255),  -- Optional link
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_type (type)
);

-- Table 11: Mentors (Optional Feature)
-- Stores mentor profiles for connections.
CREATE TABLE Mentors (
    mentor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,  -- Links to Users table (role='mentor')
    expertise_areas TEXT,  -- e.g., 'IT, Software Engineering'
    bio TEXT,
    availability BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3,2) DEFAULT 0,  -- From student feedback
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Table 12: StudentMentorConnections (Many-to-Many for Mentor Matching)
CREATE TABLE StudentMentorConnections (
    connection_id INT AUTO_INCREMENT PRIMARY KEY,
    student_user_id INT NOT NULL,
    mentor_id INT NOT NULL,
    status ENUM('Pending', 'Accepted', 'Rejected', 'Completed') DEFAULT 'Pending',
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (mentor_id) REFERENCES Mentors(mentor_id) ON DELETE CASCADE,
    INDEX idx_student (student_user_id),
    INDEX idx_mentor (mentor_id)
);

-- Optional: Gamification Extension Table (for Badges)
CREATE TABLE Badges (
    badge_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,  -- e.g., 'Skill Master'
    description TEXT,
    icon_url VARCHAR(255)
);

CREATE TABLE StudentBadges (
    user_id INT NOT NULL,
    badge_id INT NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, badge_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES Badges(badge_id) ON DELETE CASCADE
);