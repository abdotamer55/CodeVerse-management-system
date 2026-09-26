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
        "code": "#ST-2024-001",
        "username": "mariem",
        "name": "مريم محمد",
        "initials": "م.م",
        "email": "mariem@codeverse.dev",
        "track": "أولى بكالوريا",
        "level": "أولى بكالوريا",
        "completed_lessons": 0,
        "total_lessons": 3,
        "completed_homework": 0,
        "total_homework": 3,
        "overall_grade": 0.0,
        "status": "active",
        "status_label": "نشط ومنتظم",
        "is_honor": False,
        "last_active": "الآن",
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
                    COALESCE(
                        ROUND(
                            (
                                (SELECT COUNT(DISTINCT student_id || '-' || lesson_id::text) FROM lesson_completions)::numeric 
                                / NULLIF(((SELECT COUNT(*) FROM students) * (SELECT GREATEST(COUNT(*), 1) FROM lessons)), 0)
                            ) * 100, 1
                        ),
                        0.0
                    ) as attendance_rate,
                    COALESCE(ROUND(AVG(overall_grade), 1), 0.0) as avg_grade
                FROM students;
            """
            rows = execute_query(sql, fetch=True)
            if rows:
                r = rows[0]
                att_val = float(r["attendance_rate"]) if r.get("attendance_rate") is not None else 0.0
                att_display = f"{int(att_val)}%" if att_val.is_integer() else f"{att_val}%"
                return {
                    "total_count": r["total_count"],
                    "active_today": r["active_today"],
                    "honor_count": r["honor_count"],
                    "at_risk_count": r["at_risk_count"],
                    "attendance_rate": att_display,
                    "seat_capacity": "87%",
                }
        except Exception as e:
            logger.warning(f"Error querying student summary from DB: {e}")

    from services import lesson_service
    all_l = lesson_service.get_all_lessons()
    tot_l_count = len(all_l)
    tot_students = len(_STUDENTS_DB)
    comp_sum = sum(s.get("completed_lessons", 0) for s in _STUDENTS_DB)
    calc_rate = round((comp_sum / max(1, tot_students * tot_l_count)) * 100, 1) if tot_students and tot_l_count else 0.0
    return {
        "total_count": tot_students,
        "active_today": sum(1 for s in _STUDENTS_DB if s["status"] == "online"),
        "honor_count": sum(1 for s in _STUDENTS_DB if s.get("is_honor")),
        "at_risk_count": sum(1 for s in _STUDENTS_DB if s["status"] == "risk"),
        "attendance_rate": f"{int(calc_rate) if calc_rate.is_integer() else calc_rate}%",
        "seat_capacity": "87%",
    }


def get_student_dashboard_stats(student_id):
    """Return real per-student stats: completed/total lessons, homework, overall_grade, next exam."""
    from services import lesson_service, homework_service
    all_lessons = lesson_service.get_all_lessons()
    actual_total_lessons = len(all_lessons)
    actual_completed_lessons = lesson_service.get_completed_lessons_count(student_id)
    all_homework = homework_service.get_all_homework()
    actual_total_hw = len(all_homework)

    if is_db_active():
        try:
            sql = """
                SELECT
                    s.completed_lessons,
                    s.total_lessons,
                    s.completed_homework,
                    s.total_homework,
                    s.overall_grade,
                    (SELECT COUNT(*) FROM lessons) AS real_total_lessons,
                    (SELECT COUNT(*) FROM exams WHERE status IN ('active','published')) AS active_exams,
                    (SELECT COUNT(*) FROM assessment_attempts
                        WHERE CAST(student_id AS TEXT) = CAST(s.id AS TEXT)
                        AND status IN ('submitted','graded','pending_essay_grading')) AS completed_hw_real,
                    (SELECT COUNT(*) FROM homework) AS real_total_hw,
                    (SELECT COUNT(*) FROM exams) AS total_exams
                FROM students s
                WHERE CAST(s.id AS TEXT) = %s
                LIMIT 1;
            """
            rows = execute_query(sql, (str(student_id),), fetch=True)
            if rows:
                r = rows[0]
                total_lessons = int(r["real_total_lessons"]) if (r.get("real_total_lessons") is not None) else actual_total_lessons
                completed_hw = int(r["completed_hw_real"] or r["completed_homework"] or 0)
                total_hw = int(r["real_total_hw"]) if (r.get("real_total_hw") is not None) else actual_total_hw
                return {
                    "completed_lessons": actual_completed_lessons,
                    "total_lessons": total_lessons,
                    "completed_homework": completed_hw,
                    "total_homework": total_hw,
                    "overall_grade": float(r["overall_grade"] or 0),
                    "active_exams": int(r["active_exams"] or 0),
                }
        except Exception as e:
            logger.warning(f"Error querying student dashboard stats: {e}")

    student = None
    for s in _STUDENTS_DB:
        if str(s.get("id")) == str(student_id) or str(s.get("code")) == str(student_id) or s.get("username") == str(student_id):
            student = s
            break

    return {
        "completed_lessons": actual_completed_lessons,
        "total_lessons": actual_total_lessons,
        "completed_homework": student.get("completed_homework", 0) if student else 0,
        "total_homework": actual_total_hw,
        "overall_grade": float(student.get("overall_grade", 0.0) if student else 0.0),
        "active_exams": 0,
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
                    u.username,
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
                        if q in s["name"].lower() or q in s["code"].lower() or q in s["email"].lower() or q in s.get("username", "").lower()
                    ]
                from services import lesson_service, homework_service
                act_total_l = len(lesson_service.get_all_lessons())
                act_total_hw = len(homework_service.get_all_homework())
                for s in results:
                    s["total_lessons"] = act_total_l
                    s["total_homework"] = act_total_hw
                    s["completed_lessons"] = lesson_service.get_completed_lessons_count(s.get("id") or s.get("code") or s.get("username"))
                return results
        except Exception as e:
            logger.warning(f"Error querying students list from DB: {e}")

    results = [dict(s) for s in _STUDENTS_DB]
    if status_filter and status_filter != "all":
        results = [s for s in results if s["status"] == status_filter]
    if query:
        q = query.strip().lower()
        results = [
            s for s in results
            if q in s["name"].lower() or q in s["code"].lower() or q in s["email"].lower() or q in s.get("username", "").lower()
        ]
    from services import lesson_service, homework_service
    act_total_l = len(lesson_service.get_all_lessons())
    act_total_hw = len(homework_service.get_all_homework())
    for s in results:
        s["total_lessons"] = act_total_l
        s["total_homework"] = act_total_hw
        s["completed_lessons"] = lesson_service.get_completed_lessons_count(s.get("id") or s.get("code") or s.get("username"))
    return results


def get_student_by_id(student_id):
    """Retrieve single student profile by id, student_code, or username."""
    if is_db_active():
        try:
            sql = """
                SELECT 
                    s.id,
                    s.student_code as code,
                    u.full_name as name,
                    u.username,
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
                WHERE s.student_code = %s
                   OR CAST(s.id AS TEXT) = %s
                   OR lower(u.username) = lower(%s)
                LIMIT 1;
            """
            sid_str = str(student_id)
            rows = execute_query(sql, (sid_str, sid_str, sid_str), fetch=True)
            if rows:
                target = dict(rows[0])
                from services import lesson_service, homework_service
                target["total_lessons"] = len(lesson_service.get_all_lessons())
                target["total_homework"] = len(homework_service.get_all_homework())
                target["completed_lessons"] = lesson_service.get_completed_lessons_count(target.get("id") or student_id)
                return target
        except Exception as e:
            logger.warning(f"Error querying student by ID from DB: {e}")

    # In-memory fallback: match by id, code, or username
    target = None
    sid_str = str(student_id).strip().lower()
    for s in _STUDENTS_DB:
        if (
            str(s["id"]) == sid_str
            or str(s.get("code", "")).lower() == sid_str
            or str(s.get("username", "")).lower() == sid_str
        ):
            target = dict(s)
            break
    if not target:
        # Last resort: return first student (only one exists in mock)
        target = dict(_STUDENTS_DB[0])

    from services import lesson_service, homework_service
    target["total_lessons"] = len(lesson_service.get_all_lessons())
    target["total_homework"] = len(homework_service.get_all_homework())
    comp = lesson_service.get_completed_lessons_count(student_id)
    target["completed_lessons"] = comp
    return target



def create_student(name: str, email: str, track: str, level: str, student_code: str = None, username: str = None, password: str = None):
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
    if username and username.strip():
        final_username = username.strip().lower()
    else:
        final_username = cleaned_email.split("@")[0] + "".join(random.choices(string.digits, k=3))

    final_password = password.strip() if (password and password.strip()) else "student123"

    if is_db_active():
        try:
            pw_hash = generate_password_hash(final_password)
            sql_user = """
                INSERT INTO users (username, email, password_hash, role, full_name, initials, title)
                VALUES (%s, %s, %s, 'student', %s, %s, %s)
                RETURNING id;
            """
            user_rows = execute_query(
                sql_user,
                (final_username, cleaned_email, pw_hash, cleaned_name, initials, f"طالب مسار {cleaned_track}"),
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
                    res = get_student_by_id(user_id)
                    res["username"] = final_username
                    res["plain_password"] = final_password
                    return res
        except Exception as e:
            logger.error(f"Error creating student in DB: {e}")
            raise

    # Fallback mode
    new_student = {
        "id": len(_STUDENTS_DB) + 1,
        "code": student_code,
        "username": final_username,
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

    # Also register in auth fallback so student can log in in tests
    try:
        from services import auth_service
        auth_service._SAMPLE_USERS[cleaned_email] = {
            "id": f"b0000000-0000-0000-0000-{len(_STUDENTS_DB):012d}",
            "username": final_username,
            "email": cleaned_email,
            "password_hash": generate_password_hash(final_password),
            "role": "student",
            "name": cleaned_name,
            "initials": initials,
            "student_code": student_code,
            "track": cleaned_track,
            "title": f"طالب مسار {cleaned_track}",
        }
        auth_service._USERNAME_TO_EMAIL[final_username] = cleaned_email
    except Exception:
        pass

    return new_student


def update_student(student_id, data: dict):
    """Update student academic profile and user info including username & password."""
    if not student_id:
        raise ValueError("معرّف الطالب مطلوب.")

    name = data.get("name")
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
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
                u_fields = []
                u_params = []
                s_fields = []
                s_params = []
                if name:
                    u_fields.append("full_name = %s")
                    u_params.append(name.strip())
                if email:
                    u_fields.append("email = %s")
                    u_params.append(email.strip().lower())
                if username and username.strip():
                    u_fields.append("username = %s")
                    u_params.append(username.strip().lower())
                if password and password.strip():
                    u_fields.append("password_hash = %s")
                    u_params.append(generate_password_hash(password.strip()))
                if track:
                    cleaned_t = track.strip()
                    s_fields.append("track = %s")
                    s_params.append(cleaned_t)
                    u_fields.append("title = %s")
                    u_params.append(f"طالب مسار {cleaned_t}")

                if u_fields:
                    u_params.append(u_id)
                    execute_query(f"UPDATE users SET {', '.join(u_fields)} WHERE id = %s;", tuple(u_params), fetch=False)

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
            if username and username.strip(): s["username"] = username.strip().lower()
            if track: s["track"] = track.strip()
            if level: s["level"] = level.strip()
            if status:
                s["status"] = status
                s["status_label"] = status_label
            if password and password.strip():
                try:
                    from services import auth_service
                    em = s.get("email")
                    if em in auth_service._SAMPLE_USERS:
                        auth_service._SAMPLE_USERS[em]["password_hash"] = generate_password_hash(password.strip())
                except Exception:
                    pass
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

