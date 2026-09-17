-- ==============================================================================
-- CodeVerse LMS: PostgreSQL / Supabase Initial Schema Migration
-- Version: 001
-- Description: Core tables, constraints, foreign keys, and indexes
-- ==============================================================================

-- Enable UUID extension for cryptographic ID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. USERS TABLE
-- Authentication, identity, and role management (admin, teacher, student)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    full_name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    initials VARCHAR(10),
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ==============================================================================
-- 2. STUDENTS TABLE
-- Extended academic details for students (references users.id 1-to-1)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    student_code VARCHAR(50) UNIQUE NOT NULL,
    track VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    overall_grade NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('online', 'active', 'risk')),
    status_label VARCHAR(50) NOT NULL DEFAULT 'نشط ومنتظم',
    is_honor BOOLEAN NOT NULL DEFAULT FALSE,
    completed_lessons INT NOT NULL DEFAULT 0,
    total_lessons INT NOT NULL DEFAULT 28,
    completed_homework INT NOT NULL DEFAULT 0,
    total_homework INT NOT NULL DEFAULT 14,
    last_active VARCHAR(100) DEFAULT 'اليوم',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_students_code ON students(student_code);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
CREATE INDEX IF NOT EXISTS idx_students_track ON students(track);

-- ==============================================================================
-- 3. LESSONS TABLE
-- Academic courses, curriculum units, video player metadata, and topics
-- ==============================================================================
CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    short_title VARCHAR(255) NOT NULL,
    track VARCHAR(100) NOT NULL,
    track_slug VARCHAR(50) NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 60,
    duration_text VARCHAR(50) NOT NULL,
    attendees INT NOT NULL DEFAULT 0,
    progress INT NOT NULL DEFAULT 0,
    is_live BOOLEAN NOT NULL DEFAULT FALSE,
    live_time VARCHAR(100),
    instructor VARCHAR(255) NOT NULL DEFAULT 'د. طارق الحارثي',
    video_url TEXT,
    description TEXT,
    topics JSONB DEFAULT '[]'::jsonb,
    pdf_name VARCHAR(255),
    repo_name VARCHAR(255),
    order_num INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lessons_code ON lessons(code);
CREATE INDEX IF NOT EXISTS idx_lessons_track_slug ON lessons(track_slug);

-- ==============================================================================
-- 4. HOMEWORK TABLE
-- Practical assignments and programming exercises
-- ==============================================================================
CREATE TABLE IF NOT EXISTS homework (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    short_title VARCHAR(255) NOT NULL,
    track VARCHAR(100) NOT NULL,
    lesson_id INT REFERENCES lessons(id) ON DELETE SET NULL,
    instructions TEXT,
    due_date VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'grading', 'completed')),
    status_label VARCHAR(50) NOT NULL DEFAULT 'مفتوح للتسليم',
    submissions_count INT NOT NULL DEFAULT 0,
    total_students INT NOT NULL DEFAULT 348,
    auto_tests_pass_rate VARCHAR(20) DEFAULT '0%',
    max_grade INT NOT NULL DEFAULT 40,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_homework_code ON homework(code);
CREATE INDEX IF NOT EXISTS idx_homework_lesson ON homework(lesson_id);
CREATE INDEX IF NOT EXISTS idx_homework_status ON homework(status);

-- ==============================================================================
-- 5. SUBMISSIONS TABLE
-- Student submissions for homework, code review, and automated test results
-- ==============================================================================
CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    homework_id INT NOT NULL REFERENCES homework(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    student_name VARCHAR(255),
    student_code VARCHAR(50),
    repo_url TEXT,
    code_snippet TEXT,
    grade VARCHAR(50),
    feedback TEXT,
    pipeline_passed BOOLEAN NOT NULL DEFAULT FALSE,
    tests_summary VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'grading', 'graded', 'late')),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    graded_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_submissions_hw_student ON submissions(homework_id, student_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);

-- ==============================================================================
-- 6. EXAMS TABLE
-- Examination sessions, timed halls, and scheduling
-- ==============================================================================
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    short_title VARCHAR(255) NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 90,
    duration_seconds INT NOT NULL DEFAULT 5400,
    total_questions INT NOT NULL DEFAULT 0,
    scheduled_date VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'completed')),
    status_label VARCHAR(50) NOT NULL DEFAULT 'مجدول',
    progress INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exams_status ON exams(status);

-- ==============================================================================
-- 7. QUESTIONS TABLE
-- Centralized question bank repository (MCQ, code problems, and boolean)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    exam_id INT REFERENCES exams(id) ON DELETE SET NULL,
    category VARCHAR(20) NOT NULL DEFAULT 'mcq' CHECK (category IN ('mcq', 'code', 'boolean')),
    difficulty VARCHAR(50) NOT NULL DEFAULT 'متوسط',
    difficulty_badge VARCHAR(50) NOT NULL DEFAULT 'badge-info',
    track VARCHAR(100) NOT NULL DEFAULT 'الخوارزميات',
    prompt TEXT NOT NULL,
    options JSONB DEFAULT '[]'::jsonb,
    correct_index INT DEFAULT 0,
    correct_answer TEXT,
    answer_preview TEXT,
    code_snippet TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_exam_id ON questions(exam_id);
CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);

-- ==============================================================================
-- 8. RESULTS TABLE
-- Official academic exam scores, grading records, and performance ratings
-- ==============================================================================
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    student_name VARCHAR(255) NOT NULL,
    student_code VARCHAR(50) NOT NULL,
    exam_id INT REFERENCES exams(id) ON DELETE SET NULL,
    assessment VARCHAR(255) NOT NULL,
    score_percent NUMERIC(5, 2) NOT NULL,
    score_display VARCHAR(50) NOT NULL,
    date VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'passed' CHECK (status IN ('passed', 'repeat', 'failed')),
    grade_badge VARCHAR(50) NOT NULL DEFAULT 'badge-success',
    grade_label VARCHAR(50) NOT NULL DEFAULT 'ممتاز',
    feedback TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_results_student_id ON results(student_id);
CREATE INDEX IF NOT EXISTS idx_results_exam_id ON results(exam_id);

-- ==============================================================================
-- 9. FILES TABLE
-- Cloud repository for course handouts, PDFs, and code packages
-- ==============================================================================
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'pdf' CHECK (category IN ('pdf', 'zip', 'video', 'slides')),
    icon VARCHAR(50) NOT NULL DEFAULT 'picture_as_pdf',
    size_display VARCHAR(50) NOT NULL,
    downloads_count INT NOT NULL DEFAULT 0,
    updated_at VARCHAR(100) NOT NULL,
    description TEXT,
    file_url TEXT,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);

-- ==============================================================================
-- 10. NOTIFICATIONS TABLE
-- Broadcast announcements and personal academic alerts
-- ==============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL indicates global broadcast
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'announcement' CHECK (type IN ('exam', 'assignment', 'live', 'announcement')),
    icon VARCHAR(50) NOT NULL DEFAULT 'campaign',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
