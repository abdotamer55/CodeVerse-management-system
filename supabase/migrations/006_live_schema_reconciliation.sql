-- CodeVerse LMS: Reconcile the live 10-table baseline with the assessment workflow.
-- Version: 006
--
-- This migration is intentionally deterministic. It is written for the verified
-- live baseline produced by migration 001, with no 003/004/005 objects applied.
-- It must be reviewed and applied once, after a live metadata backup/verification.
-- It does not seed, delete, update, or drop any business table or business row.

-- Fail closed if the verified baseline is not the database being reconciled.
DO $$
DECLARE
    required_table TEXT;
BEGIN
    FOREACH required_table IN ARRAY ARRAY[
        'users', 'students', 'lessons', 'homework', 'submissions',
        'exams', 'questions', 'results', 'files', 'notifications'
    ] LOOP
        IF to_regclass('public.' || required_table) IS NULL THEN
            RAISE EXCEPTION '006 requires baseline table public.%', required_table;
        END IF;
    END LOOP;

    IF to_regclass('public.assessment_attempts') IS NOT NULL
       OR to_regclass('public.question_units') IS NOT NULL
       OR to_regclass('public.lesson_files') IS NOT NULL
       OR to_regclass('public.homework_questions') IS NOT NULL
       OR to_regclass('public.exam_questions') IS NOT NULL
       OR to_regclass('public.student_answers') IS NOT NULL THEN
        RAISE EXCEPTION '006 expects reconciliation objects to be absent; inspect migration history before continuing';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND (
              (table_name = 'questions' AND column_name IN ('points', 'order_index', 'homework_id', 'unit_id', 'essay_text', 'explanation'))
              OR (table_name = 'exams' AND column_name = 'max_score')
              OR (table_name = 'lessons' AND column_name IN ('lesson_date', 'image_url', 'material_url', 'homework_id'))
          )
    ) THEN
        RAISE EXCEPTION '006 expects 003/004/005 columns to be absent; inspect partial migration state before continuing';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.questions'::regclass
          AND conname = 'questions_category_check'
    ) OR NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.homework'::regclass
          AND conname = 'homework_status_check'
    ) THEN
        RAISE EXCEPTION '006 requires the baseline category and homework status constraints';
    END IF;
END $$;

-- 003 assessment persistence. No existing rows are affected because this is a new table.
CREATE TABLE public.assessment_attempts (
    id SERIAL PRIMARY KEY,
    assessment_type VARCHAR(20) NOT NULL CHECK (assessment_type IN ('exam', 'homework')),
    assessment_id INT NOT NULL,
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    score NUMERIC(8,2) NOT NULL,
    total_score NUMERIC(8,2) NOT NULL,
    correct_count INT NOT NULL,
    total_questions INT NOT NULL,
    locked BOOLEAN NOT NULL DEFAULT TRUE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'submitted', 'expired')),
    started_at TIMESTAMPTZ,
    submit_time TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,
    duration_seconds INT NOT NULL DEFAULT 0,
    submitted_answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (assessment_type, assessment_id, student_id)
);

-- 003/004/005 columns. Defaults make the new required fields valid for all existing rows.
ALTER TABLE public.questions
    ADD COLUMN points INT NOT NULL DEFAULT 1,
    ADD COLUMN order_index INT NOT NULL DEFAULT 1,
    ADD COLUMN homework_id INT REFERENCES public.homework(id) ON DELETE CASCADE,
    ADD COLUMN unit_id INT,
    ADD COLUMN essay_text TEXT,
    ADD COLUMN explanation TEXT;

ALTER TABLE public.questions
    ADD CONSTRAINT questions_points_check CHECK (points > 0);

ALTER TABLE public.exams
    ADD COLUMN max_score INT NOT NULL DEFAULT 0;

ALTER TABLE public.lessons
    ADD COLUMN lesson_date DATE,
    ADD COLUMN image_url TEXT,
    ADD COLUMN material_url TEXT,
    ADD COLUMN homework_id INT REFERENCES public.homework(id) ON DELETE SET NULL;

-- Widen existing checks only after verifying current baseline values are compatible.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.questions
        WHERE category NOT IN ('mcq', 'code', 'boolean')
    ) THEN
        RAISE EXCEPTION 'Existing questions contain unsupported category values';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public.homework
        WHERE status NOT IN ('open', 'grading', 'completed')
    ) THEN
        RAISE EXCEPTION 'Existing homework contains unsupported status values';
    END IF;
END $$;

ALTER TABLE public.questions DROP CONSTRAINT questions_category_check;
ALTER TABLE public.questions ADD CONSTRAINT questions_category_check
    CHECK (category IN ('mcq', 'code', 'boolean', 'essay'));

ALTER TABLE public.homework DROP CONSTRAINT homework_status_check;
ALTER TABLE public.homework ADD CONSTRAINT homework_status_check
    CHECK (status IN ('open', 'grading', 'completed', 'published'));

-- 005 reusable question-bank units.
CREATE TABLE public.question_units (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE public.questions
    ADD CONSTRAINT questions_unit_id_fkey
    FOREIGN KEY (unit_id) REFERENCES public.question_units(id) ON DELETE SET NULL;

-- 005 lesson-to-file relationship.
CREATE TABLE public.lesson_files (
    id SERIAL PRIMARY KEY,
    lesson_id INT NOT NULL REFERENCES public.lessons(id) ON DELETE CASCADE,
    file_id INT NOT NULL REFERENCES public.files(id) ON DELETE CASCADE,
    display_name VARCHAR(255),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lesson_id, file_id)
);

-- 005 reusable homework question relationship.
CREATE TABLE public.homework_questions (
    id SERIAL PRIMARY KEY,
    homework_id INT NOT NULL REFERENCES public.homework(id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    question_order INT NOT NULL DEFAULT 1,
    points INT NOT NULL DEFAULT 1 CHECK (points > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (homework_id, question_id)
);

-- 005 reusable exam question relationship.
CREATE TABLE public.exam_questions (
    id SERIAL PRIMARY KEY,
    exam_id INT NOT NULL REFERENCES public.exams(id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    question_order INT NOT NULL DEFAULT 1,
    points INT NOT NULL DEFAULT 1 CHECK (points > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exam_id, question_id)
);

-- 005 per-question answers. The attempt FK is explicit because answers cannot exist
-- without the assessment attempt that owns them.
CREATE TABLE public.student_answers (
    id SERIAL PRIMARY KEY,
    attempt_id INT NOT NULL REFERENCES public.assessment_attempts(id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    answer_type VARCHAR(20) NOT NULL CHECK (answer_type IN ('mcq', 'boolean', 'essay')),
    selected_option INT,
    selected_text TEXT,
    essay_text TEXT,
    marks_awarded NUMERIC(8,2) NOT NULL DEFAULT 0,
    feedback TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (attempt_id, question_id)
);

-- Supporting indexes for the final relationship graph.
CREATE INDEX idx_attempts_student ON public.assessment_attempts(student_id, assessment_type);
CREATE INDEX idx_assessment_attempts_status ON public.assessment_attempts(status);
CREATE INDEX idx_assessment_attempts_student_assessment
    ON public.assessment_attempts(student_id, assessment_type, assessment_id);
CREATE INDEX idx_questions_homework_id ON public.questions(homework_id);
CREATE INDEX idx_questions_unit_id ON public.questions(unit_id);
CREATE INDEX idx_lesson_files_lesson_id ON public.lesson_files(lesson_id);
CREATE INDEX idx_lesson_files_file_id ON public.lesson_files(file_id);
CREATE INDEX idx_homework_questions_homework_id
    ON public.homework_questions(homework_id, question_order);
CREATE INDEX idx_homework_questions_question_id
    ON public.homework_questions(question_id);
CREATE INDEX idx_exam_questions_exam_id
    ON public.exam_questions(exam_id, question_order);
CREATE INDEX idx_exam_questions_question_id
    ON public.exam_questions(question_id);
CREATE INDEX idx_student_answers_attempt_id
    ON public.student_answers(attempt_id, question_id);
CREATE INDEX idx_student_answers_question_id
    ON public.student_answers(question_id);

-- Final invariant checks make a partial or incorrectly ordered application fail loudly.
DO $$
BEGIN
    IF to_regclass('public.assessment_attempts') IS NULL
       OR to_regclass('public.question_units') IS NULL
       OR to_regclass('public.lesson_files') IS NULL
       OR to_regclass('public.homework_questions') IS NULL
       OR to_regclass('public.exam_questions') IS NULL
       OR to_regclass('public.student_answers') IS NULL THEN
        RAISE EXCEPTION '006 reconciliation did not create all required tables';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'questions' AND column_name = 'unit_id'
    ) THEN
        RAISE EXCEPTION '006 reconciliation did not add questions.unit_id';
    END IF;
END $$;
