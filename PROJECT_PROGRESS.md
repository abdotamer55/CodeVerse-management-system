# Project Progress

## Project State

CodeVerse LMS is a Flask + Jinja2 + Vanilla CSS/JS application backed by live Supabase PostgreSQL.

## Architecture / Source of Truth

- Runtime frontend uses `templates/` with shared `templates/base.html` and role-based Flask routes.
- Question assessment relationships use `exam_questions` and `homework_questions` for new writes.
- `questions.exam_id` and `questions.homework_id` remain legacy read fallbacks only.
- Assessment lifecycle is `in_progress -> submitted/locked`, with `expired` supported by services. No automatic backend expiration contract exists.
- Teacher role is strictly isolated to `/teacher/dashboard`. Teacher sessions cannot access `/admin/*` endpoints.

## Completed Work

### Phases 1 & 2 (Assessment Builder, Question Bank, Exam Lifecycle)
- Live schema reconciliation migration 006 applied and verified.
- Exam/Homework service lifecycle supports explicit start, submit, duplicate protection, Essay answers, and normalized `student_answers`.
- Student assessment UI supports Start, attempt states, Essay textareas, and double-submit prevention.
- Question Bank CRUD aligned with MCQ, Boolean, Essay, and Code categories, supporting `options`, `correct_index`, and `points`.
- Assessment Builder UI script verified to load through `base.html`'s `extra_scripts` block.
- Builder supports manual addition of MCQ, Boolean, and Essay questions, as well as importing from Question Bank.
- Points and question types are preserved when importing bank questions.
- Code questions are explicitly blocked from assessment builder since the backend assessment schema does not support them.
- Question reordering, deletion, and JSON serialization verified in builder.
- Live write-capable integration suites are intentionally deferred on the current
  production database; see the testing and production-safety notes below.

### Phase 3 (Student Results, Notifications, Profile UI Alignment)
**Phase Status: COMPLETE** — completed 2026-09-18

- **Results**: Route updated to call `result_service.get_student_results_by_user_id(user_id)` using session UUID. New service function `get_student_results_by_user_id` added to query `results` table by `student_id` UUID. Summary computed from live results via `get_student_results_summary`. Template summary cards use `summary.overall_average`, `summary.last_score`, `summary.total_graded`; rank/certificates shown as unsupported.
- **Notifications**: Route passes `user_id` to `notification_service.get_student_notifications(user_id=user_id)`. Template replaced hardcoded HTML with `{% for n in notifications %}` loop and `{% if not n.is_read %}unread{% endif %}` guard.
- **Profile**: `is_honor` badge conditional on `student.is_honor`. Academic stats cards (`overall_grade`, `completed_lessons`, `total_lessons`, `completed_homework`, `total_homework`, `status_label`) render from `student_service` data.

Files modified in Phase 3:
- `routes/student.py` — results, notifications, profile routes
- `services/result_service.py` — `get_student_results_by_user_id`, `get_student_results_summary`
- `templates/student/results.html`
- `templates/student/notifications.html`
- `templates/student/profile.html`

### Phase 4 (Teacher Dashboard, Admin Cleanup)
**Phase Status: COMPLETE** — completed 2026-09-18

- **Teacher dashboard**: Replaced 4-line stub with full dashboard. Route (`/teacher/dashboard`) now passes real data from four confirmed service calls: `student_service.get_students_summary()`, `lesson_service.get_lessons_summary()`, `homework_service.get_homework_summary()`, `exam_service.get_exams_summary()`. Template renders 4 summary cards + recent 5 lessons table (with empty-state guard). Teacher name from session. No `/admin/*` links. No invented metrics. Role guard unchanged.
- **Admin results empty-state**: Added `{% if results %}...{% else %}` guard to `templates/admin/results.html`. No behavior or query changes.

Files modified in Phase 4:
- `routes/auth.py` — teacher dashboard route, service imports
- `templates/teacher/dashboard.html` — full dashboard (was 4-line stub)
- `templates/admin/results.html` — empty-state guard added

## Current Phase

Phase 6: Focused Final Browser / UI QA.
**Phase Status: BLOCKED** — read-only browser, responsive, console, asset,
and protected-page GET verification completed. Staging E2E cannot proceed:
the project has only the configured Production `DATABASE_URL`/`SUPABASE_URL`
and no separate Staging credentials or configuration.

## Functional Polish (in progress)

- Admin settings now update only the authenticated admin's `users.full_name` and
  refresh session display data; no email or role fields are accepted.
- Student profile identity data is presentation-only. Name and email are no
  longer editable inputs and there is no student profile update route.
- Question Bank validates MCQ options server-side, fixes Boolean choices to
  True/False, and stores no options/correct index for Essay. The create/edit UI
  now switches fields by question type.
- Lesson file upload is BLOCKED: `lesson_files` and `files.file_url` exist, but
  no Supabase Storage bucket, storage policy, or server-side storage credential
  is configured. No storage upload or database record was attempted.
- No data was deleted. Existing fallback/demo arrays remain development-only
  fallbacks; the connected runtime uses database service queries when available.

## Exact Backend and Service Changes

### Phase 1 & 2
1. **`routes/admin.py`**:
   - `create_question`: Form handler parses `options` (multiline or JSON), `correct_index` (integer or null for essay), and positive `points`.
   - `edit_question`: Added extraction and forwarding of `options`, `correct_index`, and `points` to `exam_service.update_question`.
2. **`services/exam_service.py`**:
   - `update_question`: Extended to support updating `options`, `correct_index`, and `points` in the live Supabase `questions` table (using `COALESCE` updates) and in-memory `_QUESTION_BANK` fallback.
   - Preserved attempt lifecycle, `start_exam_attempt`, `submit_exam`, `student_answers`, modern relationship tables, and Essay support without breaking any interfaces.
3. **Legacy Relationships**:
   - Neither `routes/admin.py` nor `services/exam_service.py` introduce any new writes to legacy `questions.exam_id` or `questions.homework_id`. All assessment associations are persisted into `exam_questions` and `homework_questions`.

### Phase 3
4. **`services/result_service.py`**:
   - `get_student_results_by_user_id(user_id)`: New function. Queries `results WHERE CAST(student_id AS TEXT) = %s`. Falls back to first fallback student's results in offline mode.
   - `get_student_results_summary(results)`: New function. Derives `overall_average`, `last_score`, `total_graded` from a live results list. Does NOT compute rank or certificates.

### Phase 4
5. **`routes/auth.py`**:
   - Imports `student_service`, `lesson_service`, `homework_service`, `exam_service`.
   - `teacher_dashboard()`: Calls four summary functions and `get_all_lessons()[:5]`. Passes to template. Teacher `role_required("teacher")` unchanged.

### Phase 5 (Legacy Static Frontend Cleanup)
- **Discovery scope**: Inspected every HTML artifact under the root `admin/`,
  `student/`, and `pages/` directories, plus root `index.html`; inspected their
  shared root `assets/`, `css/`, `js/`, `components/`, and `_build_pages.py`
  dependencies.
- **Runtime source of truth**: Flask routes render only `templates/` files and
  `templates/base.html` loads only `static/` assets. No route, `render_template`,
  or active Jinja include resolves a root legacy HTML artifact.
- **Isolation**: Moved the complete mutually-referencing static bundle into
  `legacy/static-frontend/` without deleting any file:
  `admin/`, `student/`, `pages/`, `assets/`, `css/`, `js/`, `components/`,
  `index.html`, and `_build_pages.py`.
- **Safety rationale**: The moved files were generated/static historical pages
  with hard-coded demo content and root-relative CSS/JS/assets. Their only code
  references were inside that same static bundle or its generator; the Flask
  runtime continues to use `templates/` and `static/`.
- **Legacy reference note**: `static/js/components.js` still contains dormant
  static-shell path strings, but runtime Jinja pages do not provide its
  `sidebar-root`, `navbar-root`, or `footer-root` mount targets. No runtime route
  resolves a moved file; this was confirmed by admin, teacher, and student smoke
  requests.

## Tests

### Phase 1 & 2 (baseline)
- Historical safe-test results are retained as context only; tests must be rerun
  before being reported as current verification.
- `tests/test_assessment_lifecycle.py`: NOT RUN against production in the current
  phase because its cleanup is not interruption-safe.
- `tests/test_live_supabase.py`: NOT RUN against production in the current phase
  because it writes notifications and permanently mutates a real homework
  submission/grade without cleanup.

### Phase 3 (post-regression)
- `python -m pytest -q`: 24 passed (all Phase 3 route and template changes verified).

### Phase 4 (post-change)
- `python -m compileall -q routes services tests app.py database.py config.py`: PASS.
- `python -m pytest tests/test_app.py -q`: started safely, but the current
  execution session did not return a final pytest summary; it is not recorded as
  PASS.
- `python -m pytest tests/test_database.py -q`: started safely, but the current
  execution session did not return a final pytest summary; it is not recorded as
  PASS.
- `git diff --check`: PASS after removing the trailing blank line from
  `templates/admin/results.html`.
- Smoke test (Flask test client): teacher dashboard 200 OK, all 4 cards present, teacher name from session, no `/admin/` links. Admin results 200 OK.
- Live write integration suites are deferred pending a staging environment; they
  must not be labelled PASS for this phase.

### Phase 5 (post-change)
- `python -m compileall -q routes services tests app.py database.py config.py`: PASS.
- Runtime smoke (Flask test client): `/admin/dashboard`, `/teacher/dashboard`,
  and `/student/dashboard` each returned `200` after the isolation.
- `python -m pytest tests/test_app.py -q`: 14 passed in 130.26s. Pytest emitted
  one non-test `PytestCacheWarning` because `.pytest_cache` is not writable.
- `python -m pytest tests/test_database.py -q`: 12 passed in 37.89s. Pytest
  emitted the same non-test `.pytest_cache` warning.
- `git diff --check`: PASS.
- `tests/test_assessment_lifecycle.py` and `tests/test_live_supabase.py`: NOT RUN
  against production under the established live-test safety decision.

### Phase 6 (focused final Browser / UI QA)
- **Browser pages**: Opened the local Flask runtime landing page and login page.
  Unauthenticated `/admin/dashboard` and `/student/dashboard` correctly redirect
  to `/login?next=...`.
- **Protected-page GET smoke**: Using local Flask test-client sessions only (no
  browser login and no writes), `200 OK` was verified for Admin Dashboard,
  Question Bank, Results; Teacher Dashboard; Student Dashboard, Exams,
  Homework, Results, Notifications, and Profile. A published Exam detail also
  returned `200 OK`. There was no published Homework in the current production
  data, so its assessment-detail page was not available for read-only QA.
- **Teacher route correction**: The live route is `/teacher/dashboard`; previous
  handoff text that called it `/auth/teacher/dashboard` was documentation-only
  drift and has been corrected here. The rendered route returned `200 OK`.
- **Assessment and builder safety**: Start, Submit, Save, question create/edit,
  publish, and delete controls were deliberately not invoked. Those actions
  write production attempts or records. `tests/test_assessment_lifecycle.py`
  and `tests/test_live_supabase.py` were also NOT RUN.
- **Browser UI and responsive QA**: Landing/login had no horizontal overflow at
  1440px, 768px, or 390px. The mobile login form measured 294px within a 390px
  viewport. The login password visibility control changed its input from
  `password` to `text` as expected.
- **JavaScript and assets**: No console errors or warnings attributable to the
  application were observed on landing/login. Active runtime CSS, JavaScript,
  and logo assets resolve from `/static/`; no active reference to the relocated
  legacy bundle was observed.
- **Regression verification**: `python -m compileall -q routes services tests
  app.py database.py config.py`: PASS. `python -m pytest tests/test_app.py -q`:
  14 passed, 1 non-test `.pytest_cache` warning, in 115.95s. `python -m pytest
  tests/test_database.py -q`: 12 passed, 1 non-test `.pytest_cache` warning,
  in 57.74s. `git diff --check`: PASS.
- **Staging E2E verification**: BLOCKED. Read-only configuration inspection
  found only `DATABASE_URL` and `SUPABASE_URL`, both documented as Production;
  no `STAGING_*` database/Supabase variables, separate `.env` file, or Staging
  configuration exists. Exam and Homework Start → answer → Submit → locked
  tests were not run. No write test was attempted against Production.

## Production Safety

- Historical production schema change: migration 006 was previously applied and
  verified. This was not performed in the current Phase 4 work.
- Current Phase 4 production DB changes: NO.
- Current Phase 4 production schema changes: NO.
- Current Phase 4 migrations modified: NO (Migrations 001 through 006 preserved).
- Current Phase 4 production data changes: NO.
- `test_assessment_lifecycle.py`: NOT RUN against production due to
  cleanup/interruption risk.
- `test_live_supabase.py`: NOT RUN against production due to HIGH
  production-data risk.

### Phase 5

Historical production schema changes:
YES — migration 006 was previously applied and verified.

Current Phase 5 production DB changes:
NO.

Current Phase 5 production data changes:
NO.

Migrations executed during Phase 5:
NO.

### Phase 6

Current Phase 6 production DB changes:
NO.

Current Phase 6 production data changes:
NO.

Migrations executed during Phase 6:
NO.

## Files Modified (All Phases)

- `routes/admin.py`
- `routes/auth.py` ← Phase 4
- `routes/student.py`
- `services/exam_service.py`
- `services/result_service.py`
- `static/js/exams.js`
- `templates/admin/assessment-builder.html`
- `templates/admin/notifications.html`
- `templates/admin/questions.html`
- `templates/admin/results.html` ← Phase 4
- `templates/components/assessment-questions.html`
- `templates/student/assessment.html`
- `templates/student/exam.html`
- `templates/student/notifications.html`
- `templates/student/profile.html`
- `templates/student/results.html`
- `templates/teacher/dashboard.html` ← Phase 4
- `PROJECT_PROGRESS.md`
- `legacy/static-frontend/` ← Phase 5 isolation target (moved legacy files)

## Known Issues / Limitations

- Assessment timer is intentionally visual-only because no backend expiration endpoint exists.
- Static legacy HTML under `admin/`, `student/`, `pages/`, and `index.html` is separate from runtime Jinja templates and contains historical demo content.
- Teacher navigation/links outside the dashboard stub remain outside current scope.
- Teacher role has no dedicated CRUD routes. Teacher dashboard is read-only summary view.
- Phase 6 is BLOCKED until a separate Staging Supabase project and credentials
  are provided for Exam and Homework Start → answer → Submit → locked E2E
  verification. This was intentionally not run against Production because it
  creates or changes real attempt/submission data. No published Homework was
  available for even a read-only detail-page check during the prior QA pass.

## Remaining Phases

- Phase 6: BLOCKED — production-safe browser/UI QA is complete; live
  assessment write-flow verification requires a separate staging database.

## Next Agent Instructions

Do not modify Question Bank, Assessment Builder, Exam Lifecycle, or Phase 3
student routes unless regressions are detected. Preserve production schema,
migrations, and database cleanliness. Teacher role_required guards must not be
relaxed. Complete Phase 6 live assessment verification only against a dedicated
staging database after cleanup safety is improved.

## Handoff Status

BLOCKED (Phase 6 — separate staging credentials are not configured)

## Handoff Timestamp

2026-09-18T16:06:00+03:00
