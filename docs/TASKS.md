# TASKS.md — Work Item Tracking

## CURRENT
- Assignment, lesson metadata, and teacher-routing changes are implemented in the application fallback mode; applying migrations 003 and 004 to the live database remains required before persistent use.
- Assessment publish/review workflow and locked exam attempts implemented and syntax-validated; live database application remains pending `DATABASE_URL`.
- Phase 3 schema migrations, seed data, connection module, and services completed with verified offline fallback.
- Automated tests passing 22/22 (both route tests and database/service tests).
- Ready for live Supabase credentials (`DATABASE_URL`) to execute real migrations.

## COMPLETED (Phase 3: Database & Services)
- [x] Researched entity relationships and created `supabase/migrations/001_initial_schema.sql` covering 10 tables.
- [x] Authored comprehensive realistic Arabic seed data in `supabase/migrations/002_seed_data.sql`.
- [x] Implemented database layer `database.py` with sanitized host diagnostics and TTL-cached connection checks.
- [x] Built migration runner `migrate.py` with multi-statement SQL execution, transaction safety, and schema verification.
- [x] Adapted all 8 services with live PostgreSQL queries and robust development fallback:
  - `auth_service.py`
  - `student_service.py`
  - `lesson_service.py`
  - `homework_service.py`
  - `exam_service.py`
  - `result_service.py`
  - `file_service.py`
  - `notification_service.py`
- [x] Integrated `services/__init__.py` to expose all services cleanly.
- [x] Connected routes in `routes/admin.py` and `routes/student.py` to `notification_service`.
- [x] Authored `tests/test_database.py` validating DB sanitization, connection checks, schema scripts, and all 8 services.
- [x] Validated full test suite (22/22 tests passing in `tests/test_app.py` and `tests/test_database.py`).

## COMPLETED (Phase 2: Flask + Jinja Migration)
- [x] Project permanent documentation creation (`docs/*`).
- [x] Flask structure setup (`app.py`, `config.py`, `requirements.txt`, `.env.example`, `.env`, `.gitignore`).
- [x] Static assets organized in `static/` (`css/`, `js/`, `icons/`) with `url_for` references.
- [x] Clean Jinja2 template architecture with zero duplication.
- [x] Blueprints setup (`auth_bp`, `admin_bp`, `student_bp`).
- [x] Session-based authentication with Werkzeug password hashing and role guards.

## IN PROGRESS
- Live Supabase connection verification (blocked on user-provided active Supabase project URL).

## BLOCKED
- `python migrate.py` execution against a live cloud database is blocked until a valid, active Supabase `DATABASE_URL` is set in `.env`.

## PLANNED
- Execute `python migrate.py` once live Supabase connection string is supplied.
- Verify real-time database queries and mutations in live Supabase table editor.
- Implement file upload handling with Supabase Storage buckets.
