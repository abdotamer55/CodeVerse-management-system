"""
Results & Analytics Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

# Empty — all results come from the live database.
_RESULTS_DB = []


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "results" in tables
    except Exception:
        return False


def _format_attempt_as_result(att, user_id=None, student_name=None, student_code=None):
    """Format an assessment_attempt row into a standardized result dictionary."""
    total = float(att.get("total_score") or 1)
    score = float(att.get("score") or 0)
    pct = round((score / total) * 100.0, 1) if total > 0 else 0.0

    is_pending_essay = (att.get("status") == "pending_essay_grading")
    if is_pending_essay:
        status_val = "pending_essay_grading"
        grade_badge = "badge-warn"
        grade_label = "بانتظار تصحيح المقالي"
        score_disp = f"{score:g} / {total:g} (مبدئي)"
    else:
        status_val = "passed" if pct >= 50.0 else "repeat"
        grade_badge = "badge-success" if pct >= 50.0 else "badge-danger"
        grade_label = (
            "ممتاز" if pct >= 90.0 else
            ("جيد جداً" if pct >= 80.0 else
            ("جيد" if pct >= 65.0 else
            ("مقبول" if pct >= 50.0 else "فرصة إعادة")))
        )
        score_disp = f"{score:g} / {total:g}"

    sub_time = att.get("submit_time") or att.get("submitted_at")
    date_str = str(sub_time)[:10] if sub_time else ""

    exam_id = att["assessment_id"] if att.get("assessment_type") == "exam" else None
    homework_id = att["assessment_id"] if att.get("assessment_type") == "homework" else None

    # Handle clean title
    title = att.get("assessment_title") or ""
    if not title or '\ufffd' in title or '?' in title:
        if homework_id:
            hw_code = att.get("homework_code") or f"HW-{homework_id}"
            title = f"تكليف واجب ({hw_code})"
        else:
            title = f"اختبار أكاديمي #{exam_id or ''}"

    return {
        "id": att.get("attempt_id") or att.get("id"),
        "student_id": str(user_id or att.get("student_id") or ""),
        "student_name": student_name or att.get("student_name") or "طالب",
        "student_code": student_code or att.get("student_code") or "",
        "assessment": title,
        "exam_id": exam_id,
        "homework_id": homework_id,
        "assessment_type": att.get("assessment_type"),
        "score_percent": pct,
        "score_display": score_disp,
        "date": date_str,
        "status": status_val,
        "grade_badge": grade_badge,
        "grade_label": grade_label,
        "feedback": att.get("feedback"),
    }


def get_results_summary():
    """Aggregated results metrics across all completed assessments (exams & homework)."""
    all_res = get_all_results()
    if not all_res:
        return {
            "cohort_average": "0.0%",
            "pass_rate": "0.0%",
            "needs_repeat": 0,
            "graded_exams_count": 0,
        }

    graded = [r for r in all_res if r.get("status") != "pending_essay_grading" and r.get("score_percent") is not None]
    if not graded:
        return {
            "cohort_average": "0.0%",
            "pass_rate": "0.0%",
            "needs_repeat": 0,
            "graded_exams_count": 0,
        }

    scores = [float(r["score_percent"]) for r in graded]
    avg_score = round(sum(scores) / len(scores), 1)
    passed_count = sum(1 for r in graded if r.get("status") == "passed" or float(r.get("score_percent", 0)) >= 50.0)
    repeat_count = sum(1 for r in graded if r.get("status") == "repeat" or float(r.get("score_percent", 0)) < 50.0)
    pass_rate = round((passed_count / len(graded)) * 100.0, 1)

    return {
        "cohort_average": f"{avg_score}%",
        "pass_rate": f"{pass_rate}%",
        "needs_repeat": repeat_count,
        "graded_exams_count": len(graded),
    }


def get_all_results():
    """Retrieve all grade records for admin view, combining finalized results and live assessment attempts."""
    if is_db_active():
        try:
            results_rows = execute_query("SELECT * FROM results ORDER BY id DESC;", fetch=True) or []
            results_list = [dict(r) for r in results_rows]
            recorded_pairs = {(str(r.get("student_id")), r.get("exam_id")) for r in results_list if r.get("exam_id")}

            sql_attempts = """
                SELECT 
                    aa.id as attempt_id,
                    aa.assessment_type,
                    aa.assessment_id,
                    aa.student_id,
                    aa.score,
                    aa.total_score,
                    aa.status,
                    COALESCE(aa.submit_time, aa.submitted_at) as submit_time,
                    u.full_name as student_name,
                    COALESCE(s.student_code, '#ST-DEMO') as student_code,
                    COALESCE(e.title, h.title, 'تقييم أكاديمي') as assessment_title,
                    h.code as homework_code
                FROM assessment_attempts aa
                JOIN users u ON CAST(aa.student_id AS TEXT) = CAST(u.id AS TEXT)
                LEFT JOIN students s ON CAST(aa.student_id AS TEXT) = CAST(s.id AS TEXT)
                LEFT JOIN exams e ON aa.assessment_type = 'exam' AND aa.assessment_id = e.id
                LEFT JOIN homework h ON aa.assessment_type = 'homework' AND aa.assessment_id = h.id
                WHERE aa.status IN ('submitted', 'graded', 'passed', 'repeat', 'pending_essay_grading')
                  AND aa.total_score > 0
                ORDER BY COALESCE(aa.submit_time, aa.submitted_at) DESC, aa.id DESC;
            """
            attempts_rows = execute_query(sql_attempts, fetch=True) or []

            for att in attempts_rows:
                pair = (str(att["student_id"]), att.get("assessment_id"))
                if att.get("assessment_type") == "exam" and pair in recorded_pairs:
                    continue
                results_list.append(_format_attempt_as_result(
                    att,
                    user_id=att.get("student_id"),
                    student_name=att.get("student_name"),
                    student_code=att.get("student_code")
                ))

            results_list.sort(key=lambda r: (str(r.get("date") or ""), int(r.get("id") or 0)), reverse=True)
            return results_list
        except Exception as e:
            logger.warning(f"Error querying all results: {e}")

    return _RESULTS_DB


def get_student_results(student_code="#ST-2024-089"):
    """Retrieve grade records for specific student view by student_code."""
    if not student_code:
        return []
    if is_db_active():
        try:
            st = execute_query(
                "SELECT id FROM students WHERE student_code = %s LIMIT 1;",
                (student_code,), fetch=True
            )
            if st:
                return get_student_results_by_user_id(str(st[0]["id"]))

            sql = "SELECT * FROM results WHERE student_code = %s ORDER BY id DESC;"
            rows = execute_query(sql, (student_code,), fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying student results: {e}")

    return [r for r in _RESULTS_DB if r["student_code"] == student_code]


def get_student_results_by_user_id(user_id):
    """Retrieve grade records for the authenticated student using their UUID,
    combining finalized records from results and submitted/graded assessment_attempts (exams & homework)."""
    if not user_id:
        return []
    if is_db_active():
        try:
            results_rows = execute_query(
                "SELECT * FROM results WHERE CAST(student_id AS TEXT) = %s ORDER BY id DESC;",
                (str(user_id),), fetch=True
            ) or []
            results_list = [dict(r) for r in results_rows]
            recorded_exam_ids = {r["exam_id"] for r in results_list if r.get("exam_id")}

            sql_attempts = """
                SELECT 
                    aa.id as attempt_id,
                    aa.assessment_type,
                    aa.assessment_id,
                    aa.student_id,
                    aa.score,
                    aa.total_score,
                    aa.status,
                    COALESCE(aa.submit_time, aa.submitted_at) as submit_time,
                    COALESCE(e.title, h.title, 'تقييم أكاديمي') as assessment_title,
                    h.code as homework_code
                FROM assessment_attempts aa
                LEFT JOIN exams e ON aa.assessment_type = 'exam' AND aa.assessment_id = e.id
                LEFT JOIN homework h ON aa.assessment_type = 'homework' AND aa.assessment_id = h.id
                WHERE CAST(aa.student_id AS TEXT) = %s
                  AND aa.status IN ('submitted', 'graded', 'passed', 'repeat', 'pending_essay_grading')
                  AND aa.total_score > 0
                ORDER BY COALESCE(aa.submit_time, aa.submitted_at) DESC, aa.id DESC;
            """
            attempts_rows = execute_query(sql_attempts, (str(user_id),), fetch=True) or []

            for att in attempts_rows:
                if att.get("assessment_type") == "exam" and att.get("assessment_id") in recorded_exam_ids:
                    continue
                results_list.append(_format_attempt_as_result(att, user_id=user_id))

            results_list.sort(key=lambda r: (str(r.get("date") or ""), int(r.get("id") or 0)), reverse=True)
            return results_list
        except Exception as e:
            logger.warning(f"Error querying student results by user_id: {e}")

    # Fallback: return first student's results (dev mode only)
    return [r for r in _RESULTS_DB if r["student_code"] == "#ST-2024-089"]


def get_student_results_summary(results):
    """Derive a summary dict from a list of result records."""
    if not results:
        return {
            "overall_average": None,
            "last_score": None,
            "total_graded": 0,
        }
    graded = [r for r in results if r.get("status") != "pending_essay_grading" and r.get("score_percent") is not None]
    if not graded:
        return {
            "overall_average": None,
            "last_score": results[0].get("score_display") if results else None,
            "total_graded": 0,
        }
    scores = [float(r["score_percent"]) for r in graded]
    overall_average = round(sum(scores) / len(scores), 1)
    last_result = graded[0]
    last_score = last_result.get("score_display") or (f"{last_result['score_percent']}%" if last_result.get("score_percent") is not None else None)
    return {
        "overall_average": f"{overall_average}%",
        "last_score": last_score,
        "total_graded": len(graded),
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


def get_pending_essays_by_exam():
    """
    Retrieve all pending essay submissions grouped by Exam, then by Student Attempt,
    so that teachers can review all essay questions organized directly under the Exam Name.
    """
    rows = get_pending_essay_attempts()
    if not rows:
        return []

    exams_map = {}
    for r in rows:
        eid = r["exam_id"]
        if eid not in exams_map:
            exams_map[eid] = {
                "exam_id": eid,
                "exam_title": r["exam_title"],
                "attempts_dict": {},
                "total_questions_count": 0,
            }

        att_id = r["attempt_id"]
        if att_id not in exams_map[eid]["attempts_dict"]:
            exams_map[eid]["attempts_dict"][att_id] = {
                "attempt_id": att_id,
                "exam_id": eid,
                "exam_title": r["exam_title"],
                "student_id": r["student_id"],
                "student_name": r["student_name"],
                "student_code": r["student_code"],
                "submitted_at": r["submitted_at"],
                "mcq_score": r["mcq_score"],
                "total_score": r["total_score"],
                "status": r["status"],
                "questions": [],
            }

        exams_map[eid]["attempts_dict"][att_id]["questions"].append({
            "answer_id": r["answer_id"],
            "question_id": r["question_id"],
            "prompt": r["question_prompt"],
            "essay_text": r["essay_text"],
            "points": r["question_points"],
            "marks_awarded": r["marks_awarded"],
        })
        exams_map[eid]["total_questions_count"] += 1

    result = []
    for eid, edata in exams_map.items():
        attempts_list = list(edata["attempts_dict"].values())
        result.append({
            "exam_id": eid,
            "exam_title": edata["exam_title"],
            "attempts_count": len(attempts_list),
            "total_questions_count": edata["total_questions_count"],
            "attempts": attempts_list,
        })

    return result


def grade_essay_attempt(attempt_id: int, answer_id: int, marks_awarded: float, feedback: str = None):
    """
    Award marks for a single essay answer, update the overall attempt score,
    set attempt status to 'graded', and create/update a finalized record in the results table.
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

            # 3. Update attempt record (percentage is computed in python, not in DB column)
            att_rows = execute_query(
                """UPDATE assessment_attempts
                   SET score = %s,
                       status = 'graded'
                   WHERE id = %s
                   RETURNING assessment_id, student_id, score, total_score;""",
                (final_score, int(attempt_id)),
                fetch=True, commit=True
            )

            if att_rows:
                att = att_rows[0]
                total = float(att["total_score"] or 100)
                percentage = round((final_score / total) * 100, 2) if total > 0 else 0.0
                status_val = "passed" if percentage >= 50 else "repeat"
                grade_label = "ممتاز" if percentage >= 90 else ("جيد جداً" if percentage >= 80 else ("جيد" if percentage >= 65 else ("مقبول" if percentage >= 50 else "فرصة إعادة")))
                grade_badge = "badge-success" if percentage >= 50 else "badge-danger"

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
                    st_id = str(u["id"])
                    st_name = u["full_name"] or "طالب"
                    st_code = u["student_code"] or ""
                    score_disp = f"{final_score:g} / {total:g}"

                    existing_res = execute_query(
                        "SELECT id FROM results WHERE CAST(student_id AS TEXT) = %s AND exam_id = %s LIMIT 1;",
                        (st_id, int(att["assessment_id"])), fetch=True
                    )
                    if existing_res:
                        execute_query("""
                            UPDATE results 
                            SET score_percent=%s, score_display=%s, date=CURRENT_DATE::text, status=%s, grade_badge=%s, grade_label=%s
                            WHERE id=%s;
                        """, (percentage, score_disp, status_val, grade_badge, grade_label, existing_res[0]["id"]), fetch=False, commit=True)
                    else:
                        execute_query("""
                            INSERT INTO results (student_id, student_name, student_code, exam_id, assessment, score_percent, score_display, date, status, grade_badge, grade_label)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE::text, %s, %s, %s);
                        """, (
                            st_id, st_name, st_code,
                            att["assessment_id"], exam_title, percentage, score_disp,
                            status_val, grade_badge, grade_label
                        ), fetch=False, commit=True)

                    # Recalculate student's cumulative GPA / overall_grade
                    try:
                        from services import student_service
                        student_service.recalculate_student_overall_grade(st_id)
                    except Exception as gpa_err:
                        logger.warning(f"Could not update overall grade: {gpa_err}")

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


def grade_attempt_all_essays(attempt_id: int, grades: list, overall_feedback: str = None):
    """
    Grade all essay questions of an attempt at once, compute final score,
    mark attempt as 'graded', and create/update the final record in the results table.
    grades format: [{'answer_id': 123, 'marks': 2.5, 'feedback': '...'}, ...]
    """
    if is_db_active():
        try:
            # 1. Update each essay answer
            for g in grades:
                ans_id = g.get("answer_id")
                marks = float(g.get("marks", 0))
                fb = g.get("feedback")
                execute_query(
                    "UPDATE student_answers SET marks_awarded = %s, feedback = %s WHERE id = %s;",
                    (marks, fb, int(ans_id)),
                    fetch=False, commit=True
                )

            # 2. Recalculate total attempt score (sum of all question marks awarded)
            score_rows = execute_query(
                "SELECT COALESCE(SUM(marks_awarded), 0) as final_score FROM student_answers WHERE attempt_id = %s;",
                (int(attempt_id),),
                fetch=True
            )
            final_score = float(score_rows[0]["final_score"]) if score_rows else 0.0

            # 3. Update assessment_attempts status to graded
            att_rows = execute_query(
                """UPDATE assessment_attempts
                   SET score = %s,
                       status = 'graded'
                   WHERE id = %s
                   RETURNING assessment_id, student_id, score, total_score;""",
                (final_score, int(attempt_id)),
                fetch=True, commit=True
            )

            if att_rows:
                att = att_rows[0]
                total = float(att["total_score"] or 100)
                percentage = round((final_score / total) * 100, 2) if total > 0 else 0.0
                status_val = "passed" if percentage >= 50 else "repeat"
                grade_label = "ممتاز" if percentage >= 90 else ("جيد جداً" if percentage >= 80 else ("جيد" if percentage >= 65 else ("مقبول" if percentage >= 50 else "فرصة إعادة")))
                grade_badge = "badge-success" if percentage >= 50 else "badge-danger"

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
                    st_id = str(u["id"])
                    st_name = u["full_name"] or "طالب"
                    st_code = u["student_code"] or ""
                    score_disp = f"{final_score:g} / {total:g}"

                    existing_res = execute_query(
                        "SELECT id FROM results WHERE CAST(student_id AS TEXT) = %s AND exam_id = %s LIMIT 1;",
                        (st_id, int(att["assessment_id"])), fetch=True
                    )
                    if existing_res:
                        execute_query("""
                            UPDATE results 
                            SET score_percent=%s, score_display=%s, date=CURRENT_DATE::text, status=%s, grade_badge=%s, grade_label=%s, feedback=%s
                            WHERE id=%s;
                        """, (percentage, score_disp, status_val, grade_badge, grade_label, overall_feedback, existing_res[0]["id"]), fetch=False, commit=True)
                    else:
                        execute_query("""
                            INSERT INTO results (student_id, student_name, student_code, exam_id, assessment, score_percent, score_display, date, status, grade_badge, grade_label, feedback)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE::text, %s, %s, %s, %s);
                        """, (
                            st_id, st_name, st_code,
                            att["assessment_id"], exam_title, percentage, score_disp,
                            status_val, grade_badge, grade_label, overall_feedback
                        ), fetch=False, commit=True)

                    # Send notification
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
            logger.error(f"Error in grade_attempt_all_essays: {e}")
            raise
    return False


