"""
Authentication Service for CodeVerse LMS
Supports PostgreSQL database authentication via DATABASE_URL with graceful dev fallback.
Uses Werkzeug password hashing (scrypt / pbkdf2:sha256).
"""
import re
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
    "student@codeverse.edu": "mariem@codeverse.dev",
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
                SELECT u.id, u.username, u.email, u.password_hash, u.role, u.full_name, u.title, u.initials,
                       s.track, s.level, s.student_code
                FROM users u
                LEFT JOIN students s ON u.id = s.id
                WHERE lower(u.email) = %s OR lower(u.username) = %s
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

            user_title = user_row.get("title")
            if user_row["role"] == "student":
                if user_row.get("track"):
                    user_title = f"طالب مسار {user_row['track']}"
                elif not user_title:
                    user_title = "طالب مسار الأكاديمية"
            elif user_row["role"] == "admin":
                user_title = user_title or "مشرف المنصة الأكاديمية"

            return {
                "id": str(user_row["id"]),
                "username": user_row["username"],
                "email": user_row["email"],
                "role": user_row["role"],
                "name": user_row["full_name"],
                "title": user_title,
                "track": user_row.get("track"),
                "level": user_row.get("level"),
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
                SELECT u.id, u.username, u.email, u.role, u.full_name, u.title, u.initials,
                       s.track, s.level, s.student_code
                FROM users u
                LEFT JOIN students s ON u.id = s.id
                WHERE CAST(u.id AS TEXT) = %s LIMIT 1;
            """
            rows = execute_query(sql, (str(user_id),), fetch=True)
            if rows:
                u = rows[0]
                user_title = u.get("title")
                if u["role"] == "student":
                    if u.get("track"):
                        user_title = f"طالب مسار {u['track']}"
                    elif not user_title:
                        user_title = "طالب مسار الأكاديمية"
                elif u["role"] == "admin":
                    user_title = user_title or "مشرف المنصة الأكاديمية"

                return {
                    "id": str(u["id"]),
                    "username": u["username"],
                    "email": u["email"],
                    "role": u["role"],
                    "name": u["full_name"],
                    "title": user_title,
                    "track": u.get("track"),
                    "level": u.get("level"),
                    "initials": u.get("initials") or u["full_name"][:2],
                }
        except Exception as e:
            logger.warning(f"Database query error in get_user_by_id: {e}")

    for user in _SAMPLE_USERS.values():
        if user["id"] == user_id:
            return user
    return None


def update_user_credentials(user_id: str, username: str = None, password: str = None, full_name: str = None):
    """
    Update administrator or user credentials including username, password, and display name.
    Supports live PostgreSQL database and fallback in-memory users.
    """
    if not user_id:
        raise ValueError("معرّف المستخدم غير متوفر.")

    clean_name = full_name.strip() if full_name is not None else None
    clean_username = username.strip() if username is not None else None
    clean_password = password.strip() if password is not None else None

    if clean_name is not None and len(clean_name) > 0:
        if len(clean_name) < 2:
            raise ValueError("الاسم الكامل يجب ألا يقل عن حرفين.")
        if len(clean_name) > 255:
            raise ValueError("الاسم الكامل طويل جداً.")
    elif clean_name == "":
        raise ValueError("الاسم الكامل لا يمكن أن يكون فارغاً.")

    if clean_username is not None and len(clean_username) > 0:
        if len(clean_username) < 3:
            raise ValueError("اسم المستخدم يجب ألا يقل عن 3 أحرف.")
        if len(clean_username) > 50:
            raise ValueError("اسم المستخدم يجب ألا يزيد عن 50 حرفاً.")
        if not re.match(r"^[a-zA-Z0-9_.@-]+$", clean_username):
            raise ValueError("اسم المستخدم يجب أن يحتوي على أحرف وأرقام ورموز مسموحة فقط (_ . - @).")
    elif clean_username == "":
        raise ValueError("اسم المستخدم لا يمكن أن يكون فارغاً.")

    if clean_password is not None and len(clean_password) > 0:
        if len(clean_password) < 6:
            raise ValueError("كلمة المرور يجب ألا تقل عن 6 أحرف أو أرقام.")
        new_hash = generate_password_hash(clean_password)
    else:
        new_hash = None

    if is_db_active():
        # Check username uniqueness against other users in database
        if clean_username:
            conflict = execute_query(
                "SELECT id FROM users WHERE lower(username) = lower(%s) AND CAST(id AS TEXT) != %s LIMIT 1;",
                (clean_username, str(user_id)),
                fetch=True,
            )
            if conflict:
                raise ValueError(f"اسم المستخدم '{clean_username}' مستخدم بالفعل لحساب آخر. يرجى اختيار اسم مستخدم مختلف.")

        updates = []
        params = []
        if clean_name:
            updates.append("full_name = %s")
            params.append(clean_name)
            updates.append("initials = %s")
            params.append(clean_name[:2])
        if clean_username:
            updates.append("username = %s")
            params.append(clean_username)
        if new_hash:
            updates.append("password_hash = %s")
            params.append(new_hash)

        if not updates:
            return {"id": str(user_id)}

        updates.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE users SET {', '.join(updates)} WHERE CAST(id AS TEXT) = %s RETURNING id, username, email, full_name, initials, role;"
        params.append(str(user_id))
        rows = execute_query(sql, tuple(params), fetch=True)
        if not rows:
            raise ValueError("تعذر العثور على حساب المستخدم في قاعدة البيانات.")

        updated_row = dict(rows[0])
        if clean_username:
            _USERNAME_TO_EMAIL[clean_username.lower()] = updated_row.get("email", "")

        return updated_row

    # Fallback in-memory
    for email, user in list(_SAMPLE_USERS.items()):
        if str(user["id"]) == str(user_id):
            if clean_username:
                for other_email, other_user in _SAMPLE_USERS.items():
                    if str(other_user["id"]) != str(user_id) and other_user.get("username", "").lower() == clean_username.lower():
                        raise ValueError(f"اسم المستخدم '{clean_username}' مستخدم بالفعل. يرجى اختيار اسم آخر.")
                old_username = user.get("username", "").lower()
                user["username"] = clean_username
                if old_username in _USERNAME_TO_EMAIL:
                    del _USERNAME_TO_EMAIL[old_username]
                _USERNAME_TO_EMAIL[clean_username.lower()] = email

            if clean_name:
                user["name"] = clean_name
                user["initials"] = clean_name[:2]
            if new_hash:
                user["password_hash"] = new_hash

            return {
                "id": str(user["id"]),
                "username": user.get("username", clean_username),
                "email": user["email"],
                "full_name": user.get("name", clean_name),
                "initials": user.get("initials", clean_name[:2] if clean_name else "م.م"),
                "role": user["role"]
            }

    raise ValueError("تعذر العثور على المستخدم.")


def update_user_name(user_id: str, full_name: str):
    """Update only the authenticated user's display name."""
    return update_user_credentials(user_id, full_name=full_name)

