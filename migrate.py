"""
Migration Runner for CodeVerse LMS (PostgreSQL / Supabase)
Executes SQL migrations in dependency order and verifies schema creation.
Uses the identical configuration source (config.py / .env) as the Flask application.
"""
import sys
from pathlib import Path
from database import (
    get_connection,
    check_connection,
    format_safe_diagnostics,
    get_sanitized_db_host,
    get_database_url,
)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "supabase" / "migrations"


def run_migration(check_only: bool = False):
    print("=" * 60)
    print("CodeVerse LMS — Database Migration & Schema Runner")
    print("=" * 60)
    print(format_safe_diagnostics())
    print("=" * 60)

    db_url = get_database_url()
    if not db_url:
        print("\n[ERROR] Connection to database failed:")
        print("  Reason: DATABASE_URL is not configured")
        print("\nFix:")
        print("  Set a valid DATABASE_URL in your .env file.")
        print("  Example: DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/[DB]")
        return False

    success, host, tables, err = check_connection(force=True)
    if not success:
        print(f"\n[ERROR] Connection to database failed:")
        print(f"  Target: {host}")
        print(f"  Reason: {err}")
        print("\nLikely causes:")
        print("  1. DATABASE_URL in .env contains unreachable credentials or incorrect port.")
        print("  2. The Supabase project is paused or network access is blocked.")
        print("  3. Special characters in password require proper URL encoding.")
        print("\nMigration CANNOT proceed until a real database is available.")
        return False

    print(f"\n[OK] Connected successfully to {host}.")
    print(f"Existing public tables: {tables if tables else 'None'}\n")

    if check_only:
        print("Diagnostic check completed successfully (Check-only mode; no migrations applied).")
        return True

    # Read migration files
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print(f"[ERROR] No migration files found in {MIGRATIONS_DIR}")
        return False

    conn = None
    try:
        conn = get_connection()
        conn.autocommit = False
        with conn.cursor() as cur:
            for file_path in migration_files:
                print(f"Applying: {file_path.name} ...")
                sql = file_path.read_text(encoding="utf-8")
                cur.execute(sql)
                print(f"  -> Applied {file_path.name} successfully.")
        conn.commit()
        conn.close()
        conn = None
    except Exception as exc:
        print(f"\n[ERROR] Migration failed during execution: {exc}")
        if conn:
            conn.rollback()
            conn.close()
        return False

    # Post-migration verification
    success, _, new_tables, _ = check_connection(force=True)
    print("\n" + "=" * 60)
    print("Post-Migration Verification:")
    print("=" * 60)
    print(f"Total Tables Detected: {len(new_tables)}")
    for t in new_tables:
        print(f"  - {t}")

    return True


if __name__ == "__main__":
    check_only_flag = "--check" in sys.argv or "--check-only" in sys.argv
    ok = run_migration(check_only=check_only_flag)
    sys.exit(0 if ok else 1)
