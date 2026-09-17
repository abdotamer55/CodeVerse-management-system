-- Adds publish-gated, auto-graded assessments without replacing existing LMS tables.
ALTER TABLE questions ADD COLUMN IF NOT EXISTS points INT NOT NULL DEFAULT 1 CHECK (points > 0);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS order_index INT NOT NULL DEFAULT 1;
ALTER TABLE exams ADD COLUMN IF NOT EXISTS max_score INT NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS assessment_attempts (
    id SERIAL PRIMARY KEY,
    assessment_type VARCHAR(20) NOT NULL CHECK (assessment_type IN ('exam', 'homework')),
    assessment_id INT NOT NULL,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    score NUMERIC(8,2) NOT NULL,
    total_score NUMERIC(8,2) NOT NULL,
    correct_count INT NOT NULL,
    total_questions INT NOT NULL,
    locked BOOLEAN NOT NULL DEFAULT TRUE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (assessment_type, assessment_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_attempts_student ON assessment_attempts(student_id, assessment_type);

-- Lesson material is admin-controlled. Videos are intentionally not part of this workflow.
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS lesson_date DATE;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS image_url TEXT;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS material_url TEXT;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS homework_id INT REFERENCES homework(id) ON DELETE SET NULL;
