# CHANGELOG.md — Record of Changes

## [2026-09-17] - Assignment authoring and lesson metadata completion
### Added
- Reused assessment builder/review workflow for manually-authored homework, with explicit publishing and student scoring/locking routes.
- Dedicated teacher dashboard routing without elevating teacher users to admin permissions.
- Migration 004 to associate reusable questions with homework and permit explicit homework publishing.
### Changed
- Lesson administration now captures date, image, material URL, and related homework; student lesson/dashboard views use lesson metadata rather than video presentation or hard-coded lesson cards.

## [2026-09-17] - Assessment publishing and locked attempts
### Added
- Admin exam draft builder supporting ordered MCQ (four choices) and true/false questions, per-question points, review, and explicit publishing.
- Student exam scoring with a backend/database-ready single-attempt lock (`assessment_attempts` migration constraint).
- Migration 003 adds assessment attempt persistence, question point/order fields, and lesson material metadata.
### Changed
- Removed visible demo-login controls and credential disclosure; login now presents separate manual teacher and student credential sections.
- Student lesson view no longer presents a lesson video workflow; dashboard includes a materials collection backed by lesson metadata.

## [2026-09-17] - Phase 3: Database Layer & Schema Migration
### Added
- **Database Schema**: Authored `supabase/migrations/001_initial_schema.sql` implementing all 10 core entities (`users`, `students`, `lessons`, `homework`, `submissions`, `exams`, `questions`, `results`, `files`, `notifications`) with foreign keys, checks, indexes, and timestamps.
- **Seed Data**: Authored `supabase/migrations/002_seed_data.sql` with rich Arabic records and pre-hashed credentials matching Werkzeug security standards.
- **Connection Module**: Built `database.py` with `get_database_url()`, `get_sanitized_db_host()`, `check_connection(force, ttl)` with caching to prevent blocking timeouts, and `execute_query()`.
- **Migration Runner**: Created `migrate.py` with sequential script execution, error logging, and post-migration schema verification.
- **Notification Service**: Created `services/notification_service.py` to handle administrative broadcasts and student alerts.
- **Dual-Mode Services**: Updated all 8 service modules (`auth_service`, `student_service`, `lesson_service`, `homework_service`, `exam_service`, `result_service`, `file_service`, `notification_service`) to query PostgreSQL when active with graceful fallback to realistic data when offline.
- **Route Integration**: Connected `/admin/notifications` and `/student/notifications` to the notification service in `routes/admin.py` and `routes/student.py`.
- **Database Test Suite**: Created `tests/test_database.py` testing database sanitization, health checks, migration SQL definitions, and all service modules.
- **Expanded Test Coverage**: Test suite grew from 11 tests to 22 tests (100% pass rate).

## [2026-09-16] - Phase 2: Flask + Jinja Architecture Completed
### Added
- Created complete Flask application structure (`app.py`, `config.py`, `requirements.txt`, `.env`, `.env.example`, `.gitignore`).
- Migrated static assets to `static/` preserving exact visual identity, dark theme, and Arabic RTL layout.
- Implemented clean Jinja2 template inheritance (`base.html`, `components/`, `auth/`, `admin/`, `student/`, `errors/`).
- Created Route Blueprints in `routes/` (`auth_bp`, `admin_bp`, `student_bp`).
- Built automated test suite (`tests/test_app.py`) with 11 test cases (100% pass rate).

## [2026-09-16] - Phase 1: Frontend Foundation Completed
### Added
- Completed 24 responsive Arabic RTL screens for CodeVerse LMS based on Stitch source of truth.
- Implemented CSS design tokens and component system.
