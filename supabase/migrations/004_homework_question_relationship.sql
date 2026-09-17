-- Extends the reusable question store for manually-authored homework assessments.
ALTER TABLE questions ADD COLUMN IF NOT EXISTS homework_id INT REFERENCES homework(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_questions_homework_id ON questions(homework_id);

-- Publishing is explicit for question-based assignments.
ALTER TABLE homework DROP CONSTRAINT IF EXISTS homework_status_check;
ALTER TABLE homework ADD CONSTRAINT homework_status_check CHECK (status IN ('open', 'grading', 'completed', 'published'));
