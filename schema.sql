CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_type TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE Companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    industry TEXT
);

CREATE TABLE JobPostings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,          -- Added column for job description
    required_skills TEXT,
    experience TEXT,           -- Added column for experience requirements
    status TEXT CHECK (status IN ('Open', 'Closed', 'Draft')),
    FOREIGN KEY (company_id) REFERENCES Companies (id) ON DELETE CASCADE
);

CREATE TABLE Applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    resume_path TEXT,          -- Added column to store the path of the uploaded resume
    status TEXT CHECK (status IN ('Pending', 'Accepted', 'Rejected')),
    FOREIGN KEY (job_id) REFERENCES JobPostings (id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES Users (id) ON DELETE CASCADE
);

CREATE TABLE Interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    recruiter_id INTEGER NOT NULL,
    FOREIGN KEY (application_id) REFERENCES Applications (id) ON DELETE CASCADE,
    FOREIGN KEY (recruiter_id) REFERENCES Users (id) ON DELETE CASCADE
);

CREATE TABLE JobRoles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE Questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_role_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT CHECK (question_type IN ('MCQ', 'True/False', 'Descriptive')),
    difficulty TEXT CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    options JSON,
    correct_answer TEXT,
    FOREIGN KEY (job_role_id) REFERENCES JobRoles (id) ON DELETE CASCADE
);

CREATE TABLE AIAssessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    total_score REAL NOT NULL,
    FOREIGN KEY (application_id) REFERENCES Applications (id) ON DELETE CASCADE
);

CREATE TABLE AssessmentQuestions (
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    candidate_answer TEXT,
    score REAL NOT NULL,
    PRIMARY KEY (assessment_id, question_id),
    FOREIGN KEY (assessment_id) REFERENCES AIAssessments (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES Questions (id) ON DELETE CASCADE
);

CREATE TABLE Payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    recruiter_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (company_id) REFERENCES Companies (id) ON DELETE CASCADE,
    FOREIGN KEY (recruiter_id) REFERENCES Users (id) ON DELETE CASCADE
);
