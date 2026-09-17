# ARCHITECTURE.md — CodeVerse System Architecture

## Architecture Overview
The CodeVerse LMS follows a modular 3-tier architecture built on Python/Flask, Jinja2, and Supabase PostgreSQL:

```
[ Browser / Client (Arabic RTL) ]
          │  HTTPS / Cookie Session
          ▼
[ Flask Application Core (app.py) ]
    ├── Middleware & Context Processors (Session, User, RTL)
    ├── Error Handlers (404, 500)
    │
    ├── [ Route Blueprints (routes/) ]
    │     ├── auth.py     (/login, /logout)
    │     ├── admin.py    (/admin/*)
    │     └── student.py  (/student/*)
    │
    ├── [ Service Layer (services/) ]
    │     ├── auth_service.py
    │     ├── student_service.py
    │     ├── lesson_service.py
    │     ├── homework_service.py
    │     ├── exam_service.py
    │     ├── result_service.py
    │     ├── file_service.py
    │     └── notification_service.py
    │
    ├── [ Database Layer (database.py) ]
    │     ├── Connection pool / health check (psycopg2)
    │     ├── Resilient offline caching
    │     └── Safe query executor (execute_query)
    │
    ├── [ Migrations (supabase/migrations/) & Runner (migrate.py) ]
    │     ├── 001_initial_schema.sql (10 tables)
    │     └── 002_seed_data.sql (Arabic test dataset)
    │
    ├── [ Presentation Layer (templates/) ]
    │     ├── base.html (Universal App Shell)
    │     ├── components/ (sidebar, navbar, footer, modals)
    │     ├── auth/
    │     ├── admin/
    │     ├── student/
    │     └── errors/
    │
    └── [ Static Assets (static/) ]
          ├── css/ (variables, global, layout, components, pages, responsive)
          ├── js/ (main, components, navigation, ui, forms, exams)
          └── icons/ (logo.svg)
```

## Security & Session Architecture
1. **Password Hashing**: Werkzeug's `generate_password_hash` with `scrypt`/`pbkdf2:sha256` hashing.
2. **Session Security**:
   - `SESSION_COOKIE_HTTPONLY = True`
   - `SESSION_COOKIE_SAMESITE = 'Lax'`
   - Secret key pulled from environment variables (`SECRET_KEY`).
3. **Role-Based Access Control (RBAC)**:
   - `@login_required`: Redirects unauthenticated requests to `/login`.
   - `@role_required('admin')`: Restricts admin endpoints strictly to administrative staff.
   - `@role_required('student')`: Restricts student views to authenticated student accounts.

## Database & Fallback Strategy
- The application reads `DATABASE_URL` from the environment.
- When PostgreSQL is unreachable or unprovisioned, `database.py` caches the check result to prevent request latency.
- Services detect database presence and automatically toggle between live SQL queries and realistic local development datasets without breaking page renders or test executions.
