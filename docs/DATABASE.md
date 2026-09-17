# DATABASE.md — Database Schema & Supabase Architecture

## Overview
This document specifies the PostgreSQL relational schema, migration management, and database connectivity for CodeVerse LMS. The application connects to Supabase PostgreSQL via `DATABASE_URL` with a resilient service-layer fallback for offline development.

---

## 1. Status Overview

- **CURRENT**: Migration files `001_initial_schema.sql` and `002_seed_data.sql` created and verified. Connection layer `database.py` and migration runner `migrate.py` implemented. All 8 services adapted with dual live-query / fallback capability.
- **COMPLETED**:
  - Relational schema design for 10 entities in `supabase/migrations/001_initial_schema.sql`.
  - Realistic Arabic seed data with hashed credentials in `supabase/migrations/002_seed_data.sql`.
  - Database connection layer `database.py` with sanitized logging and TTL health-check caching.
  - Migration CLI tool `migrate.py`.
  - Automated test suite `tests/test_database.py` covering schema integrity and services.
- **IN PROGRESS**: Awaiting live Supabase project credentials.
- **BLOCKED**: Migration execution against live database is blocked until `DATABASE_URL` is configured with an active Supabase PostgreSQL instance.
- **PLANNED**: Run `python migrate.py` once live credentials are provided; verify live data reads and writes.

---

## 2. Supabase PostgreSQL Schema (10 Entities)

All tables use PostgreSQL syntax, proper foreign keys with referential actions (`ON DELETE CASCADE` / `ON DELETE SET NULL`), checks, sensible defaults, and indexing on frequent lookup columns.

### 1. `users`
Core identity and credentials.
- `id`: UUID (Primary Key, default `gen_random_uuid()`)
- `email`: VARCHAR(255) (UNIQUE, NOT NULL)
- `username`: VARCHAR(100) (UNIQUE, NOT NULL)
- `password_hash`: VARCHAR(255) (NOT NULL)
- `role`: VARCHAR(20) NOT NULL CHECK (`role IN ('admin', 'teacher', 'student')`)
- `full_name`: VARCHAR(255) (NOT NULL)
- `initials`: VARCHAR(10) (DEFAULT 'ك.ف')
- `title`: VARCHAR(255) (DEFAULT 'عضو أكاديمية كودفيرس')
- `avatar_url`: TEXT
- `is_active`: BOOLEAN (DEFAULT TRUE)
- `created_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)
- `updated_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 2. `students`
Academic profile extending `users` for student role.
- `id`: UUID (PRIMARY KEY, REFERENCES `users(id)` ON DELETE CASCADE)
- `student_code`: VARCHAR(50) (UNIQUE, NOT NULL)
- `track`: VARCHAR(100) (NOT NULL DEFAULT 'هندسة برمجيات الأنظمة')
- `level`: VARCHAR(50) (NOT NULL DEFAULT 'المستوى الأول')
- `overall_grade`: NUMERIC(5, 2) (DEFAULT 0.0)
- `completed_lessons`: INT (DEFAULT 0)
- `total_lessons`: INT (DEFAULT 28)
- `completed_homework`: INT (DEFAULT 0)
- `total_homework`: INT (DEFAULT 14)
- `status`: VARCHAR(20) NOT NULL CHECK (`status IN ('online', 'active', 'risk', 'inactive')`)
- `is_honor`: BOOLEAN (DEFAULT FALSE)
- `last_active`: VARCHAR(100) (DEFAULT 'الآن')
- `enrolled_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 3. `lessons`
Curriculum units and video lessons.
- `id`: SERIAL PRIMARY KEY
- `code`: VARCHAR(50) (UNIQUE, NOT NULL)
- `title`: VARCHAR(255) (NOT NULL)
- `track`: VARCHAR(100) (NOT NULL)
- `level`: VARCHAR(50) (DEFAULT 'متقدم')
- `duration_display`: VARCHAR(50) (NOT NULL)
- `duration_minutes`: INT (NOT NULL DEFAULT 45)
- `video_url`: TEXT
- `slides_url`: TEXT
- `order_index`: INT (NOT NULL DEFAULT 1)
- `is_live`: BOOLEAN (DEFAULT FALSE)
- `status`: VARCHAR(20) NOT NULL CHECK (`status IN ('published', 'draft', 'archived')`)
- `created_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 4. `homework`
Assignments and programming challenges.
- `id`: SERIAL PRIMARY KEY
- `code`: VARCHAR(50) (UNIQUE, NOT NULL)
- `title`: VARCHAR(255) (NOT NULL)
- `track`: VARCHAR(100) (NOT NULL)
- `lesson_id`: INT REFERENCES `lessons(id)` ON DELETE SET NULL
- `deadline_display`: VARCHAR(100) (NOT NULL)
- `deadline_at`: TIMESTAMPTZ
- `status`: VARCHAR(20) NOT NULL CHECK (`status IN ('active', 'review', 'closed')`)
- `submissions_count`: INT NOT NULL DEFAULT 0
- `total_students`: INT NOT NULL DEFAULT 348
- `instructions`: TEXT
- `starter_code`: TEXT
- `created_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 5. `submissions`
Student code submissions for homework assignments.
- `id`: SERIAL PRIMARY KEY
- `homework_id`: INT NOT NULL REFERENCES `homework(id)` ON DELETE CASCADE
- `student_id`: UUID NOT NULL REFERENCES `students(id)` ON DELETE CASCADE
- `repo_url`: TEXT
- `code_snippet`: TEXT
- `grade`: NUMERIC(5, 2)
- `status`: VARCHAR(20) NOT NULL CHECK (`status IN ('submitted', 'grading', 'graded', 'late')`)
- `ci_passed`: BOOLEAN DEFAULT FALSE
- `feedback`: TEXT
- `submitted_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 6. `exams`
Examination sessions and test halls.
- `id`: SERIAL PRIMARY KEY
- `title`: VARCHAR(255) (NOT NULL)
- `code`: VARCHAR(50) (UNIQUE, NOT NULL)
- `track`: VARCHAR(100) (NOT NULL)
- `duration_minutes`: INT NOT NULL DEFAULT 60
- `duration_display`: VARCHAR(50) NOT NULL DEFAULT '60 دقيقة'
- `total_questions`: INT NOT NULL DEFAULT 10
- `max_score`: INT NOT NULL DEFAULT 100
- `status`: VARCHAR(20) NOT NULL CHECK (`status IN ('active', 'upcoming', 'closed')`)
- `scheduled_date`: VARCHAR(100) NOT NULL
- `created_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 7. `questions`
Question bank repository for exams.
- `id`: SERIAL PRIMARY KEY
- `exam_id`: INT REFERENCES `exams(id)` ON DELETE SET NULL
- `category`: VARCHAR(50) NOT NULL CHECK (`category IN ('mcq', 'code', 'boolean', 'short_answer')`)
- `difficulty`: VARCHAR(50) NOT NULL DEFAULT 'متوسط'
- `track`: VARCHAR(100) NOT NULL DEFAULT 'الخوارزميات'
- `prompt`: TEXT NOT NULL
- `options`: JSONB DEFAULT '[]'::jsonb
- `correct_index`: INT DEFAULT 0
- `correct_answer`: TEXT
- `code_snippet`: TEXT
- `created_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 8. `results`
Academic grades, ratings, and examination outcomes.
- `id`: SERIAL PRIMARY KEY
- `student_id`: UUID NOT NULL REFERENCES `students(id)` ON DELETE CASCADE
- `student_name`: VARCHAR(255) NOT NULL
- `student_code`: VARCHAR(50) NOT NULL
- `exam_id`: INT REFERENCES `exams(id)` ON DELETE SET NULL
- `assessment`: VARCHAR(255) NOT NULL
- `score_percent`: NUMERIC(5, 2) NOT NULL
- `score_display`: VARCHAR(50) NOT NULL
- `date`: VARCHAR(100) NOT NULL
- `status`: VARCHAR(20) NOT NULL CHECK (`status IN ('passed', 'repeat', 'failed')`)
- `grade_badge`: VARCHAR(50) NOT NULL DEFAULT 'badge-success'
- `grade_label`: VARCHAR(50) NOT NULL DEFAULT 'ممتاز'
- `feedback`: TEXT
- `recorded_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 9. `files`
Cloud handouts, lecture slides, and starter code.
- `id`: SERIAL PRIMARY KEY
- `name`: VARCHAR(255) NOT NULL
- `file_name`: VARCHAR(255) NOT NULL
- `category`: VARCHAR(50) NOT NULL CHECK (`category IN ('pdf', 'zip', 'video', 'slides')`)
- `icon`: VARCHAR(50) NOT NULL DEFAULT 'picture_as_pdf'
- `size_display`: VARCHAR(50) NOT NULL
- `downloads_count`: INT NOT NULL DEFAULT 0
- `updated_at`: VARCHAR(100) NOT NULL
- `description`: TEXT
- `file_url`: TEXT
- `uploaded_by`: UUID REFERENCES `users(id)` ON DELETE SET NULL
- `created_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

### 10. `notifications`
Academic alerts and broadcast announcements.
- `id`: SERIAL PRIMARY KEY
- `user_id`: UUID REFERENCES `users(id)` ON DELETE CASCADE -- NULL indicates global broadcast
- `title`: VARCHAR(255) NOT NULL
- `content`: TEXT NOT NULL
- `type`: VARCHAR(50) NOT NULL CHECK (`type IN ('exam', 'assignment', 'live', 'announcement')`)
- `icon`: VARCHAR(50) NOT NULL DEFAULT 'campaign'
- `is_read`: BOOLEAN NOT NULL DEFAULT FALSE
- `created_at`: TIMESTAMPTZ (DEFAULT CURRENT_TIMESTAMP)

---

## 3. Migration Runner (`migrate.py`)
Run migrations sequentially via terminal:
```bash
python migrate.py
```
Options:
- Reads `DATABASE_URL` from `.env`.
- Verifies connection before attempting execution.
- Sanitizes logs to prevent leaking DB credentials.
- Checks and reports public tables created upon completion.
