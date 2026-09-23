"""
Authentication Service for CodeVerse LMS
Supports PostgreSQL database authentication via DATABASE_URL with graceful dev fallback.
Uses Werkzeug password hashing (scrypt / pbkdf2:sha256).
"""
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

# Sample/fallback users for development prior to live Supabase connection
_SAMPLE_USERS = {
    "mariem@codeverse.dev": {
        "id": "mariem",
        "username": "mariem",
        "email": "mariem@codeverse.dev",
        "password_hash": generate_password_hash("student123"),
        "role": "student",
        "name": "مريم محمد",
        "initials": "م.م",
        "student_code": "#ST-2024-001",
        "track": "هندسة برمجيات الأنظمة",
        "title": "طالبة مسار هندسة البرمجيات",
    },
    "admin@codeverse.edu": {
        "id": "a0000000-0000-0000-0000-000000000001",
        "username": "admin",
        "email": "admin@codeverse.edu",
        "password_hash": generate_password_hash("admin123"),
        "role": "admin",
        "name": "أستاذ د. طارق الحارثي",
        "initials": "ط.ح",
        "student_code": "STAFF-001",
        "track": "إدارة الأكاديمية",
        "title": "مشرف المنصة الأكاديمية",
    },
}

_USERNAME_TO_EMAIL = {
    "mariem": "mariem@codeverse.dev",
    "student": "mariem@codeverse.dev",
    "admin": "admin@codeverse.edu",
    "tareq": "admin@codeverse.edu",
}


def is_db_active():
    """Check if the PostgreSQL database is live and has the users table."""
    try:
        ok, _, tables, _ = check_connection()
        return ok and "users" in tables
    except Exception:
        return False


def authenticate(identifier: str, password: str):
    """
    Authenticate a user by username or email and password.
    Queries PostgreSQL users table when available, with dev fallback.
    Returns:
        tuple (user_dict or None, error_message or None)
    """
    if not identifier or not password:
        return None, "يرجى إدخال اسم المستخدم وكلمة المرور"

    clean_id = identifier.strip().lower()

    if is_db_active():
        try:
            sql = """
                SELECT id, username, email, password_hash, role, full_name, title, initials
                FROM users
                WHERE lower(email) = %s OR lower(username) = %s
                LIMIT 1;
            """
            rows = execute_query(sql, (clean_id, clean_id), fetch=True)
            if not rows:
                # Check sample users fallback (e.g. ziad / student / tareq)
                email = _USERNAME_TO_EMAIL.get(clean_id, clean_id)
                user = _SAMPLE_USERS.get(email)
                if user and check_password_hash(user["password_hash"], password):
                    return user, None
                return None, "بيانات الاعتماد غير صحيحة. يرجى التحقق من اسم المستخدم أو البريد"

            user_row = rows[0]
            if not check_password_hash(user_row["password_hash"], password):
                return None, "كلمة المرور غير صحيحة"

            return {
                "id": str(user_row["id"]),
                "username": user_row["username"],
                "email": user_row["email"],
                "role": user_row["role"],
                "name": user_row["full_name"],
                "title": user_row.get("title") or ("مشرف المنصة" if user_row["role"] == "admin" else "طالب مسار برمجيات"),
                "initials": user_row.get("initials") or user_row["full_name"][:2],
            }, None
        except Exception as e:
            logger.warning(f"Database query failed, falling back to mock: {e}")

    # Fallback to in-memory dataset
    email = _USERNAME_TO_EMAIL.get(clean_id, clean_id)
    user = _SAMPLE_USERS.get(email)
    if not user:
        return None, "بيانات الاعتماد غير صحيحة. يرجى التحقق من اسم المستخدم أو البريد"

    if not check_password_hash(user["password_hash"], password):
        return None, "كلمة المرور غير صحيحة"

    return user, None


def get_user_by_id(user_id: str):
    """Retrieve user dictionary by ID."""
    if not user_id:
        return None

    if is_db_active():
        try:
            sql = """
                SELECT id, username, email, role, full_name, title, initials
                FROM users WHERE CAST(id AS TEXT) = %s LIMIT 1;
            """
            rows = execute_query(sql, (str(user_id),), fetch=True)
            if rows:
                u = rows[0]
                return {
                    "id": str(u["id"]),
                    "username": u["username"],
                    "email": u["email"],
                    "role": u["role"],
                    "name": u["full_name"],
                    "title": u.get("title") or ("مشرف المنصة" if u["role"] == "admin" else "طالب مسار برمجيات"),
                    "initials": u.get("initials") or u["full_name"][:2],
                }
        except Exception as e:
            logger.warning(f"Database query error in get_user_by_id: {e}")

    for user in _SAMPLE_USERS.values():
        if user["id"] == user_id:
            return user
    return None


def update_user_name(user_id: str, full_name: str):
    """Update only the authenticated user's display name."""
    name = (full_name or "").strip()
    if not user_id or not name:
        raise ValueError("الاسم الكامل مطلوب.")
    if len(name) > 255:
        raise ValueError("الاسم طويل جداً.")
    if is_db_active():
        rows = execute_query(
            "UPDATE users SET full_name = %s, initials = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, full_name, initials;",
            (name, name[:2], str(user_id)), fetch=True,
        )
        if not rows:
            raise ValueError("تعذر العثور على المستخدم.")
        return dict(rows[0])
    for user in _SAMPLE_USERS.values():
        if user["id"] == user_id:
            user["name"] = name
            user["initials"] = name[:2]
            return {"id": user_id, "full_name": name, "initials": name[:2]}
    raise ValueError("تعذر العثور على المستخدم.")
