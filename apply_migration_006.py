"""Standalone runner for the live schema reconciliation migration 006.

The runner is intentionally isolated from migrate.py and discovers no other
migration files. It performs only local validation by default; database writes
require the explicit --apply flag.
"""
import argparse
from pathlib import Path

from database import get_connection, get_connection_diagnostics

PROJECT_ROOT = Path(__file__).resolve().parent
MIGRATION_006 = PROJECT_ROOT / "supabase" / "migrations" / "006_live_schema_reconciliation.sql"


def read_migration_006() -> str:
    """Read the one permitted migration and reject path drift."""
    migration_path = MIGRATION_006.resolve()
    expected_path = (PROJECT_ROOT / "supabase" / "migrations" / "006_live_schema_reconciliation.sql").resolve()
    if migration_path != expected_path:
        raise RuntimeError("Migration path validation failed")
    if not migration_path.is_file():
        raise FileNotFoundError(f"Missing migration: {migration_path}")
    sql = migration_path.read_text(encoding="utf-8")
    if not sql.strip():
        raise RuntimeError("Migration 006 is empty")
    return sql


def validate_local() -> str:
    """Validate the fixed migration path without opening a database connection."""
    sql = read_migration_006()
    print(f"Validated migration: {MIGRATION_006}")
    print(f"SQL size: {len(sql.encode('utf-8'))} bytes")
    print("Migration discovery: disabled; only 006 is addressable")
    print("Database write: not requested")
    return sql


def apply_migration() -> None:
    """Apply only 006 in one transaction after explicit user intent."""
    sql = validate_local()
    diagnostics = get_connection_diagnostics()
    print(f"Target host: {diagnostics['host']}:{diagnostics['port']}")
    print(f"Target database: {diagnostics['database']}")
    print("Applying exactly: 006_live_schema_reconciliation.sql")

    connection = get_connection()
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            cursor.execute(sql)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print("Migration 006 applied successfully.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or apply migration 006 only.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply migration 006 to DATABASE_URL. Without this flag, no database connection is opened.",
    )
    args = parser.parse_args()

    if args.apply:
        apply_migration()
    else:
        validate_local()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
