-- Minimal workflow extension for reusable question banks, lesson materials, and assessment linking.
-- This build reuses the existing core tables instead of creating duplicate lesson/exam concepts.

ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_category_check;
ALTER TABLE questions ADD CONSTRAINT questions_category_check CHECK (category IN ('mcq', 'code', 'boolean', 'essay'));

CREATE TABLE IF NOT EXISTS question_units (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS idx_question_units_name ON question_units(name);

ALTER TABLE questions ADD COLUMN IF NOT EXISTS unit_id INT REFERENCES question_units(id) ON DELETE SET NULL;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS essay_text TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS explanation TEXT;

CREATE INDEX IF NOT EXISTS idx_questions_unit_id ON questions(unit_id);

CREATE TABLE IF NOT EXISTS lesson_files (
    id SERIAL PRIMARY KEY,
    lesson_id INT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    file_id INT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    display_name VARCHAR(255),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lesson_id, file_id)
);

CREATE INDEX IF NOT EXISTS idx_lesson_files_lesson_id ON lesson_files(lesson_id);
CREATE INDEX IF NOT EXISTS idx_lesson_files_file_id ON lesson_files(file_id);

CREATE TABLE IF NOT EXISTS homework_questions (
    id SERIAL PRIMARY KEY,
    homework_id INT NOT NULL REFERENCES homework(id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    question_order INT NOT NULL DEFAULT 1,
    points INT NOT NULL DEFAULT 1 CHECK (points > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (homework_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_homework_questions_homework_id ON homework_questions(homework_id, question_order);
CREATE INDEX IF NOT EXISTS idx_homework_questions_question_id ON homework_questions(question_id);

CREATE TABLE IF NOT EXISTS exam_questions (
    id SERIAL PRIMARY KEY,
    exam_id INT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    question_order INT NOT NULL DEFAULT 1,
    points INT NOT NULL DEFAULT 1 CHECK (points > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exam_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_exam_questions_exam_id ON exam_questions(exam_id, question_order);
CREATE INDEX IF NOT EXISTS idx_exam_questions_question_id ON exam_questions(question_id);

CREATE TABLE IF NOT EXISTS student_answers (
    id SERIAL PRIMARY KEY,
    attempt_id INT NOT NULL,
    question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_type VARCHAR(20) NOT NULL CHECK (answer_type IN ('mcq', 'boolean', 'essay')),
    selected_option INT,
    selected_text TEXT,
    essay_text TEXT,
    marks_awarded NUMERIC(8,2) NOT NULL DEFAULT 0,
    feedback TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (attempt_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_student_answers_attempt_id ON student_answers(attempt_id, question_id);
CREATE INDEX IF NOT EXISTS idx_student_answers_question_id ON student_answers(question_id);

ALTER TABLE assessment_attempts
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'submitted', 'expired')),
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS submit_time TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS expired_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS duration_seconds INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS submitted_answers JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_assessment_attempts_status ON assessment_attempts(status);
CREATE INDEX IF NOT EXISTS idx_assessment_attempts_student_assessment ON assessment_attempts(student_id, assessment_type, assessment_id);

-- Keep the schema consistent with the app's existing permission model.
-- The server-side auth checks remain authoritative; this migration only adds the needed relational structure.
