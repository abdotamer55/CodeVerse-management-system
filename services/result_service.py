"""
Results & Analytics Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

_RESULTS_DB = [
    {
        "id": 1,
        "student_name": "زياد حسام الدين",
        "student_code": "#ST-2024-089",
        "assessment": "اختبار هياكل البيانات والخوارزميات",
        "score_percent": 96.0,
        "score_display": "96%",
        "date": "10 سبتمبر 2024",
        "status": "passed",
        "grade_badge": "badge-success",
        "grade_label": "ممتاز ومتميز",
    },
    {
        "id": 2,
        "student_name": "سارة طارق المنصور",
        "student_code": "#ST-2024-114",
        "assessment": "اختبار هياكل البيانات والخوارزميات",
        "score_percent": 91.0,
        "score_display": "91%",
        "date": "10 سبتمبر 2024",
        "status": "passed",
        "grade_badge": "badge-success",
        "grade_label": "جيد جداً مرتفع",
    },
    {
        "id": 3,
        "student_name": "عمر خالد الدوسري",
        "student_code": "#ST-2024-032",
        "assessment": "اختبار هياكل البيانات والخوارزميات",
        "score_percent": 58.0,
        "score_display": "58%",
        "date": "10 سبتمبر 2024",
        "status": "repeat",
        "grade_badge": "badge-danger",
        "grade_label": "فرصة إعادة",
    },
    {
        "id": 4,
        "student_name": "زياد حسام الدين",
        "student_code": "#ST-2024-089",
        "assessment": "مشروع REST API وتخزين Redis",
        "score_percent": 95.0,
        "score_display": "38 / 40",
        "date": "12 سبتمبر 2024",
        "status": "passed",
        "grade_badge": "badge-success",
        "grade_label": "ممتاز",
    },
]


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "results" in tables
    except Exception:
        return False


def get_results_summary():
    """Aggregated results metrics."""
    if is_db_active():
        try:
            sql = """
                SELECT 
                    ROUND(AVG(score_percent), 1) as avg_score,
                    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_cnt,
                    COUNT(CASE WHEN status = 'repeat' THEN 1 END) as repeat_cnt,
                    COUNT(*) as total_cnt
                FROM results;
            """
            rows = execute_query(sql, fetch=True)
            if rows:
                r = rows[0]
                total = r["total_cnt"] or 1
                pass_rate = round((r["passed_cnt"] / total) * 100, 1)
                return {
                    "cohort_average": f"{r['avg_score']}%",
                    "pass_rate": f"{pass_rate}%",
                    "needs_repeat": r["repeat_cnt"],
                    "graded_exams_count": r["total_cnt"],
                }
        except Exception as e:
            logger.warning(f"Error querying results summary: {e}")

    return {
        "cohort_average": "87.6%",
        "pass_rate": "91.2%",
        "needs_repeat": 14,
        "graded_exams_count": 32,
    }


def get_all_results():
    """Retrieve all grade records for admin view."""
    if is_db_active():
        try:
            sql = "SELECT * FROM results ORDER BY id DESC;"
            rows = execute_query(sql, fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying all results: {e}")

    return _RESULTS_DB


def get_student_results(student_code="#ST-2024-089"):
    """Retrieve grade records for specific student view by student_code."""
    if is_db_active():
        try:
            sql = "SELECT * FROM results WHERE student_code = %s ORDER BY id DESC;"
            rows = execute_query(sql, (student_code,), fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying student results: {e}")

    return [r for r in _RESULTS_DB if r["student_code"] == student_code]


def get_student_results_by_user_id(user_id):
    """Retrieve grade records for the authenticated student using their UUID."""
    if not user_id:
        return []
    if is_db_active():
        try:
            sql = "SELECT * FROM results WHERE CAST(student_id AS TEXT) = %s ORDER BY id DESC;"
            rows = execute_query(sql, (str(user_id),), fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying student results by user_id: {e}")

    # Fallback: return first student's results (dev mode only)
    return [r for r in _RESULTS_DB if r["student_code"] == "#ST-2024-089"]


def get_student_results_summary(results):
    """Derive a summary dict from a list of result records.
    Only returns metrics that are actually stored in the results table.
    Does NOT compute rank or certificates — those are unsupported by this backend.
    """
    if not results:
        return {
            "overall_average": None,
            "last_score": None,
            "total_graded": 0,
        }
    scores = [float(r["score_percent"]) for r in results if r.get("score_percent") is not None]
    overall_average = round(sum(scores) / len(scores), 1) if scores else None
    last_result = results[0]  # Already ordered by id DESC
    last_score = last_result.get("score_display") or (f"{last_result['score_percent']}%" if last_result.get("score_percent") is not None else None)
    return {
        "overall_average": f"{overall_average}%" if overall_average is not None else None,
        "last_score": last_score,
        "total_graded": len(results),
    }


def delete_result(result_id: int):
    """Delete an academic result record."""
    if not result_id:
        raise ValueError("معرّف النتيجة مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM results WHERE id = %s;", (int(result_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting result from DB: {e}")
            raise

    global _RESULTS_DB
    before = len(_RESULTS_DB)
    _RESULTS_DB = [r for r in _RESULTS_DB if r["id"] != int(result_id)]
    if len(_RESULTS_DB) < before:
        deleted = True
    return deleted


def get_pending_essay_attempts():
    """Retrieve all student exam attempts that require manual essay grading."""
    if is_db_active():
        try:
            sql = """
                SELECT a.id as attempt_id, a.assessment_id as exam_id, a.student_id, a.score as mcq_score,
                       a.total_score, a.status, 
                       TO_CHAR(a.submitted_at, 'YYYY-MM-DD HH24:MI') as submitted_at,
                       u.full_name as student_name, COALESCE(s.student_code, '#ST-DEMO') as student_code, 
                       e.title as exam_title,
                       sa.id as answer_id, sa.question_id, sa.essay_text, sa.marks_awarded,
                       q.prompt as question_prompt, q.points as question_points
                FROM assessment_attempts a
                JOIN users u ON CAST(a.student_id AS TEXT) = CAST(u.id AS TEXT)
                LEFT JOIN students s ON CAST(s.id AS TEXT) = CAST(u.id AS TEXT)
                JOIN exams e ON a.assessment_id = e.id
                JOIN student_answers sa ON sa.attempt_id = a.id AND sa.answer_type = 'essay'
                JOIN questions q ON sa.question_id = q.id
                WHERE a.status IN ('submitted', 'pending_essay_grading')
                ORDER BY a.submitted_at DESC;
            """
            rows = execute_query(sql, fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying pending essay attempts: {e}")
    return []


def grade_essay_attempt(attempt_id: int, answer_id: int, marks_awarded: float, feedback: str = None):
    """
    Award marks for an essay answer, update the overall attempt score,
    set attempt status to 'graded', and create a finalized record in the results table.
    """
    if is_db_active():
        try:
            # 1. Update student_answers with marks & feedback
            execute_query(
                "UPDATE student_answers SET marks_awarded = %s, feedback = %s WHERE id = %s;",
                (float(marks_awarded), feedback, int(answer_id)),
                fetch=False, commit=True
            )

            # 2. Recalculate total score for the attempt
            score_rows = execute_query(
                "SELECT COALESCE(SUM(marks_awarded), 0) as final_score FROM student_answers WHERE attempt_id = %s;",
                (int(attempt_id),),
                fetch=True
            )
            final_score = float(score_rows[0]["final_score"]) if score_rows else float(marks_awarded)

            # 3. Update attempt record
            att_rows = execute_query(
                """UPDATE assessment_attempts
                   SET score = %s,
                       percentage = ROUND((%s::numeric / NULLIF(total_score, 0)::numeric) * 100, 2),
                       status = 'graded'
                   WHERE id = %s
                   RETURNING assessment_id, student_id, score, total_score, percentage;""",
                (final_score, final_score, int(attempt_id)),
                fetch=True, commit=True
            )

            if att_rows:
                att = att_rows[0]
                total = att["total_score"] or 100
                percentage = float(att["percentage"] or round((final_score / total) * 100, 2))
                grade_label = "ممتاز" if percentage >= 90 else ("جيد جداً" if percentage >= 80 else ("جيد" if percentage >= 70 else "فرصة إعادة"))
                grade_badge = "badge-success" if percentage >= 70 else "badge-danger"

                # Get exam and student details
                exam_rows = execute_query("SELECT title FROM exams WHERE id = %s;", (att["assessment_id"],), fetch=True)
                exam_title = exam_rows[0]["title"] if exam_rows else "اختبار أكاديمي"

                user_rows = execute_query(
                    """SELECT u.id, u.full_name, COALESCE(s.student_code, '#ST-DEMO') as student_code 
                       FROM users u LEFT JOIN students s ON CAST(s.id AS TEXT) = CAST(u.id AS TEXT)
                       WHERE CAST(u.id AS TEXT) = %s;""",
                    (str(att["student_id"]),), fetch=True
                )
                if user_rows:
                    u = user_rows[0]
                    # Insert or update into results
                    res_sql = """
                        INSERT INTO results (student_id, student_name, student_code, exam_id, assessment, score_percent, score_display, date, status, grade_badge, grade_label)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE::text, 'passed', %s, %s);
                    """
                    execute_query(res_sql, (
                        u["id"], u["full_name"], u["student_code"],
                        att["assessment_id"], exam_title, percentage, f"{final_score:g} / {total:g}",
                        grade_badge, grade_label
                    ), fetch=False, commit=True)

                    # Send student notification
                    try:
                        from services import notification_service
                        notification_service.create_notification({
                            "user_id": u["id"],
                            "title": f"تم اعتماد نتيجتك في {exam_title}",
                            "content": f"اعتمد المعلم درجة الأسئلة المقالية. نتيجتك النهائية هي {final_score:g} من {total:g} بنسبة {percentage}%.",
                            "type": "exam",
                        })
                    except Exception as ne:
                        logger.warning(f"Could not send grade notification: {ne}")

            return True
        except Exception as e:
            logger.error(f"Error grading essay attempt: {e}")
            raise
    return False

