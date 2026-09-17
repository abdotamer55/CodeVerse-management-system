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
    """Retrieve grade records for specific student view."""
    if is_db_active():
        try:
            sql = "SELECT * FROM results WHERE student_code = %s ORDER BY id DESC;"
            rows = execute_query(sql, (student_code,), fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying student results: {e}")

    return [r for r in _RESULTS_DB if r["student_code"] == student_code]


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

