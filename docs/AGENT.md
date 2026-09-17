# AGENT.md — Rules of Engagement & Memory for CodeVerse LMS

## Role and Philosophy
You are an expert AI software engineer working on the **CodeVerse LMS (منصة كودفيرس التعليمية)**.
The platform is an Arabic-first (RTL) Learning Management System specializing in computer science, system engineering, and programming education.

## Core Rules for All Agents
1. **Source of Truth**: The existing visual design, dark theme palette, typography (Cairo/Tajawal/Inter), RTL Arabic layout, and component aesthetics are frozen. NEVER redesign or downgrade the UI.
2. **Zero Duplication**:
   - Shared layout lives in `templates/base.html`.
   - Shared components live in `templates/components/` and are included via Jinja `{% include %}`.
   - Shared styles live in `static/css/`.
   - Shared client logic lives in `static/js/`.
   - Do NOT duplicate markup, CSS rules, or JS functions across pages.
3. **Thin Routes & Service Layer**:
   - Route handlers in `routes/` only parse requests, invoke services, and render templates.
   - Business logic, data retrieval, and validation live in `services/`.
4. **Supabase Readiness**:
   - Do not hardcode credentials.
   - Read configurations from `config.py` and environment variables.
   - Design service interfaces so that swapping static mock data for Supabase PostgreSQL client requires no route changes.
5. **Documentation Discipline**:
   - Before starting any task, read `docs/AGENT.md`, `docs/PROJECT_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, and `docs/CHANGELOG.md`.
   - Update documentation after every meaningful architectural change.
   - Categorize all tasks into CURRENT, IN PROGRESS, PLANNED, or BLOCKED. Do NOT mark planned tasks as done until verified.

## Technology Stack
- **Backend**: Python 3.11+, Flask 3.x
- **Template Engine**: Jinja2 with template inheritance and partials
- **Frontend Core**: Semantic HTML5, Vanilla CSS3 (CSS Variables, Grid, Flexbox), Vanilla Modern JavaScript (ES6+)
- **Typography & Icons**: Cairo, Tajawal, Inter, Google Material Symbols Outlined
- **Database (Target)**: Supabase PostgreSQL via `DATABASE_URL` / Supabase Client
