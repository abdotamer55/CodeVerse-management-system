"""
Database Module for CodeVerse LMS
Manages PostgreSQL connections via DATABASE_URL (Supabase compatible).
Provides safe connection verification, sanitized diagnostic reporting, and query execution.
"""
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

# Strictly load project .env with override=True to guarantee precedence
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

_cached_check = None
_cached_time = 0.0


def _normalize_db_url(url: str) -> str:
    """Clean URL, handling accidental surrounding whitespace or bracketed passwords."""
    if not url:
        return ""
    url = url.strip()
    # Handle Supabase bracketed password placeholder artifact: :[password]@ -> :password@
    m = re.search(r":\[(.*?)\]@", url)
    if m:
        url = url[:m.start()] + f":{m.group(1)}@" + url[m.end():]
    return url


def get_database_url():
    """
    Retrieve DATABASE_URL strictly from environment or Config.
    DATABASE_URL has absolute priority.
    Does NOT fall back to localhost, 127.0.0.1, port 5432, or MySQL environment variables.
    Returns None if unconfigured.
    """
    # 1. Primary source: DATABASE_URL in environment
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        # 2. Config object
        raw = getattr(Config, "DATABASE_URL", None)

    # 3. If missing, check if SUPABASE_URL was provided with a postgresql:// scheme
    if not raw:
        sup_url = os.environ.get("SUPABASE_URL", "")
        if sup_url and (sup_url.strip().startswith("postgresql://") or sup_url.strip().startswith("postgres://")):
            raw = sup_url

    if not raw:
        return None

    cleaned = _normalize_db_url(raw)
    return cleaned if cleaned else None


def get_connection_diagnostics() -> dict:
    """
    Extract safe diagnostic information without ever revealing passwords.
    """
    url = get_database_url()
    if not url:
        return {
            "driver": "PostgreSQL",
            "host": "None",
            "port": "None",
            "database": "None",
            "loaded": "NO",
        }

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        driver = "PostgreSQL" if ("postgres" in scheme) else scheme
        host = parsed.hostname or "None"
        port = str(parsed.port) if parsed.port else "None"
        db_name = parsed.path.lstrip("/") if parsed.path else "None"
        return {
            "driver": driver,
            "host": host,
            "port": port,
            "database": db_name,
            "loaded": "YES",
        }
    except Exception:
        return {
            "driver": "PostgreSQL",
            "host": "Unknown",
            "port": "Unknown",
            "database": "Unknown",
            "loaded": "YES",
        }


def format_safe_diagnostics() -> str:
    """
    Format the standardized safe diagnostic report.
    Guaranteed to never print database passwords.
    """
    diag = get_connection_diagnostics()
    return (
        f"Database driver: {diag['driver']}\n"
        f"Database host: {diag['host']}\n"
        f"Database port: {diag['port']}\n"
        f"Database name: {diag['database']}\n"
        f"DATABASE_URL loaded: {diag['loaded']}"
    )


def get_sanitized_db_host() -> str:
    """Return only host:port for display or 'Not Configured'."""
    diag = get_connection_diagnostics()
    if diag["loaded"] == "NO":
        return "Not Configured"
    return f"{diag['host']}:{diag['port']}"


def get_connection(timeout: int = 5):
    """
    Establish a connection to the PostgreSQL database.
    Raises ValueError if DATABASE_URL is not configured.
    Raises psycopg2.Error on connection failure.
    """
    db_url = get_database_url()
    if not db_url:
        raise ValueError("DATABASE_URL is not configured")
    return psycopg2.connect(db_url, connect_timeout=timeout)


def check_connection(force: bool = False, ttl: float = 5.0):
    """
    Perform a real live health check against the PostgreSQL database.
    Caches results for `ttl` seconds to avoid repeated connection latency during fallback mode.
    Returns:
        tuple: (success: bool, host: str, tables: list[str], error: str or None)
    """
    global _cached_check, _cached_time
    now = time.time()
    if not force and _cached_check is not None and (now - _cached_time) < ttl:
        return _cached_check

    db_url = get_database_url()
    if not db_url:
        _cached_check = (False, "Not Configured", [], "DATABASE_URL is not configured")
        _cached_time = now
        return _cached_check

    diag = get_connection_diagnostics()
    sanitized_host = f"{diag['host']}:{diag['port']}"

    try:
        conn = get_connection(timeout=3)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
        conn.close()
        _cached_check = (True, sanitized_host, tables, None)
        _cached_time = now
        return _cached_check
    except Exception as exc:
        err_type = type(exc).__name__
        err_msg = str(exc).strip().split("\n")[0]
        _cached_check = (False, sanitized_host, [], f"{err_type}: {err_msg}")
        _cached_time = now + 25.0  # Keep failure cached for 30s to prevent repeated delays
        return _cached_check


def execute_query(query: str, params: tuple = None, fetch: bool = True, commit: bool = False):
    """
    Execute a query safely against the database returning a list of dictionaries.
    Automatically commits if query modifies data or if commit=True is explicitly passed.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            results = cur.fetchall() if fetch else None
            stripped = query.strip().upper()
            is_write = any(stripped.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "CREATE", "SELECT SETVAL"))
            if commit or not fetch or is_write:
                conn.commit()
        return results
    finally:
        conn.close()
