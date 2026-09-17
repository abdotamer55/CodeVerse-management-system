"""
Student Management Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import logging
import random
import string
from werkzeug.security import generate_password_hash
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

_STUDENTS_DB = [
    {
        "id": 1,
        "code": "#ST-2024-089",
        "name": "زياد حسام الدين",
        "initials": "ز.ح",
        "email": "ziad.h@codeverse.dev",
        "track": "هندسة برمجيات الأنظمة",
        "level": "المستوى المتقدم L3",
        "completed_lessons": 27,
        "total_lessons": 28,
        "completed_homework": 14,
        "total_homework": 14,
        "overall_grade": 98.4,
        "status": "online",
        "status_label": "متصل الآن",
        "is_honor": True,
        "last_active": "قبل دقيقتين",
    },
    {
        "id": 2,
        "code": "#ST-2024-114",
        "name": "سارة طارق المنصور",
        "initials": "س.م",
        "email": "sara.m@codeverse.edu",
        "track": "تطوير واجهات React",
        "level": "المستوى الثاني",
        "completed_lessons": 24,
        "total_lessons": 28,
        "completed_homework": 13,
        "total_homework": 14,
        "overall_grade": 93.0,
        "status": "active",
        "status_label": "نشط ومنتظم",
        "is_honor": False,
        "last_active": "اليوم 04:15 م",
    },
    {
        "id": 3,
        "code": "#ST-2024-032",
        "name": "عمر خالد الدوسري",
        "initials": "ع.د",
        "email": "omar.d@codeverse.edu",
        "track": "تطوير الخوادم Node.js",
        "level": "المستوى الأول",
        "completed_lessons": 14,
        "total_lessons": 28,
        "completed_homework": 6,
        "total_homework": 14,
        "overall_grade": 64.2,
        "status": "risk",
        "status_label": "متأخر دراسياً",
        "is_honor": False,
        "last_active": "قبل 3 أيام",
    },
    {
        "id": 4,
        "code": "CV-24901",
        "name": "عبدالله سامي القحطاني",
        "initials": "ع.س",
        "email": "abdullah.s@codeverse.edu",
        "track": "هندسة النظم الخلفية",
        "level": "المستوى المتقدم L3",
        "completed_lessons": 42,
        "total_lessons": 44,
        "completed_homework": 14,
        "total_homework": 14,
        "overall_grade": 98.8,
        "status": "online",
        "status_label": "متميز وأول الدفعة",
        "is_honor": True,
        "last_active": "الآن",
    },
    {
        "id": 5,
        "code": "CV-24918",
        "name": "فاطمة ناصر الزهراني",
        "initials": "ف.ن",
        "email": "fatima.n@codeverse.edu",
        "track": "تطبيقات الجوال Flutter",
        "level": "المستوى الثاني",
        "completed_lessons": 31,
        "total_lessons": 44,
        "completed_homework": 11,
        "total_homework": 14,
        "overall_grade": 88.5,
        "status": "active",
        "status_label": "نشط ومنتظم",
        "is_honor": False,
        "last_active": "أمس 09:30 م",
    },
]


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "students" in tables
    except Exception:
        return False


def get_students_summary():
    """Returns aggregated summary metrics for Admin Dashboard and Students list."""
    if is_db_active():
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 'online' THEN 1 END) as active_today,
                    COUNT(CASE WHEN is_honor = true THEN 1 END) as honor_count,
                    COUNT(CASE WHEN status = 'risk' THEN 1 END) as at_risk_count,
                    COALESCE(ROUND(AVG(overall_grade), 1), 0.0) as avg_grade
                FROM students;
            """
            rows = execute_query(sql, fetch=True)
            if rows:
                r = rows[0]
                return {
                    "total_count": r["total_count"],
                    "active_today": r["active_today"],
                    "honor_count": r["honor_count"],
                    "at_risk_count": r["at_risk_count"],
                    "attendance_rate": f"{r['avg_grade']}%",
                    "seat_capacity": "87%",
                }
        except Exception as e:
            logger.warning(f"Error querying student summary from DB: {e}")

    return {
        "total_count": 348,
        "active_today": 312,
        "honor_count": 14,
        "at_risk_count": 8,
        "attendance_rate": "91.4%",
        "seat_capacity": "87%",
    }


def get_all_students(query=None, status_filter=None):
    """Retrieve students with optional search and status filtering."""
    if is_db_active():
        try:
            sql = """
                SELECT 
                    s.id,
                    s.student_code as code,
                    u.full_name as name,
                    COALESCE(u.initials, SUBSTRING(u.full_name, 1, 2)) as initials,
                    u.email,
                    s.track,
                    s.level,
                    s.completed_lessons,
                    s.total_lessons,
                    s.completed_homework,
                    s.total_homework,
                    s.overall_grade,
                    s.status,
                    s.status_label,
                    s.is_honor,
                    s.last_active
                FROM students s
                JOIN users u ON s.id = u.id
                ORDER BY s.overall_grade DESC;
            """
            rows = execute_query(sql, fetch=True)
            if rows:
                results = [dict(r) for r in rows]
                if status_filter and status_filter != "all":
                    results = [s for s in results if s["status"] == status_filter]
                if query:
                    q = query.strip().lower()
                    results = [
                        s for s in results
                        if q in s["name"].lower() or q in s["code"].lower() or q in s["email"].lower()
                    ]
                return results
        except Exception as e:
            logger.warning(f"Error querying students list from DB: {e}")

    results = _STUDENTS_DB
    if status_filter and status_filter != "all":
        results = [s for s in results if s["status"] == status_filter]
    if query:
        q = query.strip().lower()
        results = [
            s for s in results
            if q in s["name"].lower() or q in s["code"].lower() or q in s["email"].lower()
        ]
    return results


def get_student_by_id(student_id):
    """Retrieve single student profile."""
    if is_db_active():
        try:
            sql = """
                SELECT 
                    s.id,
                    s.student_code as code,
                    u.full_name as name,
                    COALESCE(u.initials, SUBSTRING(u.full_name, 1, 2)) as initials,
                    u.email,
                    s.track,
                    s.level,
                    s.completed_lessons,
                    s.total_lessons,
                    s.completed_homework,
                    s.total_homework,
                    s.overall_grade,
                    s.status,
                    s.status_label,
                    s.is_honor,
                    s.last_active
                FROM students s
                JOIN users u ON s.id = u.id
                WHERE s.student_code = %s OR CAST(s.id AS TEXT) = %s
                LIMIT 1;
            """
            rows = execute_query(sql, (str(student_id), str(student_id)), fetch=True)
            if not rows and str(student_id).isdigit():
                offset = max(0, int(student_id) - 1)
                sql_idx = """
                    SELECT 
                        s.id,
                        s.student_code as code,
                        u.full_name as name,
                        COALESCE(u.initials, SUBSTRING(u.full_name, 1, 2)) as initials,
                        u.email,
                        s.track,
                        s.level,
                        s.completed_lessons,
                        s.total_lessons,
                        s.completed_homework,
                        s.total_homework,
                        s.overall_grade,
                        s.status,
                        s.status_label,
                        s.is_honor,
                        s.last_active
                    FROM students s
                    JOIN users u ON s.id = u.id
                    ORDER BY s.overall_grade DESC
                    LIMIT 1 OFFSET %s;
                """
                rows = execute_query(sql_idx, (offset,), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.warning(f"Error querying student by ID from DB: {e}")

    for s in _STUDENTS_DB:
        if str(s["id"]) == str(student_id) or s["code"] == str(student_id):
            return s
    return _STUDENTS_DB[0]


def create_student(name: str, email: str, track: str, level: str, student_code: str = None, password: str = "student123"):
    """Create a new student record and corresponding user account."""
    if not name or not email:
        raise ValueError("الاسم والبريد الإلكتروني مطلوبان.")

    cleaned_name = name.strip()
    cleaned_email = email.strip().lower()
    cleaned_track = (track or "هندسة برمجيات الأنظمة").strip()
    cleaned_level = (level or "المستوى الأول").strip()

    if not student_code:
        rand_suffix = "".join(random.choices(string.digits, k=4))
        student_code = f"CV-{rand_suffix}"

    initials = "".join([part[0] for part in cleaned_name.split()[:2]]) if cleaned_name else "ط.ج"
    username = cleaned_email.split("@")[0] + "".join(random.choices(string.digits, k=3))

    if is_db_active():
        try:
            pw_hash = generate_password_hash(password)
            sql_user = """
                INSERT INTO users (username, email, password_hash, role, full_name, initials, title)
                VALUES (%s, %s, %s, 'student', %s, %s, %s)
                RETURNING id;
            """
            user_rows = execute_query(
                sql_user,
                (username, cleaned_email, pw_hash, cleaned_name, initials, f"طالب مسار {cleaned_track}"),
                fetch=True
            )
            if user_rows:
                user_id = user_rows[0]["id"]
                sql_student = """
                    INSERT INTO students (id, student_code, track, level, overall_grade, status, status_label)
                    VALUES (%s, %s, %s, %s, 0.00, 'active', 'نشط ومنتظم')
                    RETURNING *;
                """
                std_rows = execute_query(sql_student, (user_id, student_code, cleaned_track, cleaned_level), fetch=True)
                if std_rows:
                    return get_student_by_id(user_id)
        except Exception as e:
            logger.error(f"Error creating student in DB: {e}")
            raise

    # Fallback mode
    new_student = {
        "id": len(_STUDENTS_DB) + 1,
        "code": student_code,
        "name": cleaned_name,
        "initials": initials,
        "email": cleaned_email,
        "track": cleaned_track,
        "level": cleaned_level,
        "completed_lessons": 0,
        "total_lessons": 28,
        "completed_homework": 0,
        "total_homework": 14,
        "overall_grade": 0.0,
        "status": "active",
        "status_label": "نشط ومنتظم",
        "is_honor": False,
        "last_active": "الآن",
    }
    _STUDENTS_DB.append(new_student)
    return new_student


def update_student(student_id, data: dict):
    """Update student academic profile and user info."""
    if not student_id:
        raise ValueError("معرّف الطالب مطلوب.")

    name = data.get("name")
    email = data.get("email")
    track = data.get("track")
    level = data.get("level")
    status = data.get("status", "active")
    status_label = "متصل الآن" if status == "online" else ("متأخر دراسياً" if status == "risk" else "نشط ومنتظم")

    if is_db_active():
        try:
            # Find the user id
            find_sql = "SELECT id FROM students WHERE student_code = %s OR CAST(id AS TEXT) = %s LIMIT 1;"
            rows = execute_query(find_sql, (str(student_id), str(student_id)), fetch=True)
            if rows:
                u_id = rows[0]["id"]
                if name or email:
                    u_fields = []
                    u_params = []
                    if name:
                        u_fields.append("full_name = %s")
                        u_params.append(name.strip())
                    if email:
                        u_fields.append("email = %s")
                        u_params.append(email.strip().lower())
                    u_params.append(u_id)
                    execute_query(f"UPDATE users SET {', '.join(u_fields)} WHERE id = %s;", tuple(u_params), fetch=False)

                s_fields = []
                s_params = []
                if track:
                    s_fields.append("track = %s")
                    s_params.append(track.strip())
                if level:
                    s_fields.append("level = %s")
                    s_params.append(level.strip())
                if status:
                    s_fields.append("status = %s")
                    s_params.append(status)
                    s_fields.append("status_label = %s")
                    s_params.append(status_label)

                if s_fields:
                    s_params.append(u_id)
                    execute_query(f"UPDATE students SET {', '.join(s_fields)} WHERE id = %s;", tuple(s_params), fetch=False)

                return get_student_by_id(u_id)
        except Exception as e:
            logger.error(f"Error updating student in DB: {e}")
            raise

    # Fallback mode
    for s in _STUDENTS_DB:
        if str(s["id"]) == str(student_id) or s["code"] == str(student_id):
            if name: s["name"] = name.strip()
            if email: s["email"] = email.strip().lower()
            if track: s["track"] = track.strip()
            if level: s["level"] = level.strip()
            if status:
                s["status"] = status
                s["status_label"] = status_label
            return s
    return None


def delete_student(student_id):
    """Delete student and cascade delete associated user account."""
    if not student_id:
        raise ValueError("معرّف الطالب مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            # Find user UUID
            find_sql = "SELECT id FROM students WHERE student_code = %s OR CAST(id AS TEXT) = %s LIMIT 1;"
            rows = execute_query(find_sql, (str(student_id), str(student_id)), fetch=True)
            if rows:
                u_id = rows[0]["id"]
                # Deleting from users cascades to students, submissions, results
                execute_query("DELETE FROM users WHERE id = %s;", (u_id,), fetch=False)
                deleted = True
        except Exception as e:
            logger.error(f"Error deleting student from DB: {e}")
            raise

    # Fallback mode
    global _STUDENTS_DB
    before_len = len(_STUDENTS_DB)
    _STUDENTS_DB = [s for s in _STUDENTS_DB if str(s["id"]) != str(student_id) and s["code"] != str(student_id)]
    if len(_STUDENTS_DB) < before_len:
        deleted = True

    return deleted

