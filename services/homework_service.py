"""
Homework & Assignments Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
Provides complete workflow for homework management, student code submissions,
and administrative grading views.
"""
import logging
import json
from services import exam_service
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

# Sample/fallback datasets for offline development
_HOMEWORK_DB = [
    {
        "id": 1,
        "code": "HW-118",
        "title": "مشروع بناء REST API عالي الاعتمادية بنظام التخزين المؤقت Redis",
        "short_title": "مشروع REST API و Redis",
        "track": "هندسة النظم الخلفية (Backend)",
        "submissions_count": 312,
        "total_students": 348,
        "due_date": "18 سبتمبر 2024",
        "status": "grading",
        "status_label": "تصحيح جارٍ",
        "auto_tests_pass_rate": "89.4%",
        "sample_submission": {
            "student_name": "زياد حسام الدين",
            "student_code": "#ST-2024-089",
            "repo_url": "github.com/ziad-dev/fastapi-redis-cache",
            "grade": "38 / 40",
            "feedback": "تنفيذ ممتاز لمعمارية Repository Pattern والتعامل مع حالات Cache Invalidation.",
            "pipeline_passed": True,
            "tests_summary": "16/16 Unit Tests Passed · Code Coverage 94%",
        },
    },
    {
        "id": 2,
        "code": "HW-121",
        "title": "حل معضلات البرمجة الديناميكية: خوارزمية حقيبة الظهر (0/1 Knapsack)",
        "short_title": "خوارزميات البرمجة الديناميكية (DP)",
        "track": "خوارزميات وهياكل البيانات",
        "submissions_count": 280,
        "total_students": 348,
        "due_date": "21 سبتمبر 2024",
        "status": "open",
        "status_label": "مفتوح للتسليم",
        "auto_tests_pass_rate": "76.2%",
        "sample_submission": {
            "student_name": "سارة طارق المنصور",
            "student_code": "#ST-2024-114",
            "repo_url": "github.com/sara-m/knapsack-memoization",
            "grade": "قيد المراجعة",
            "feedback": "",
            "pipeline_passed": True,
            "tests_summary": "12/12 Tests Passed · Time Complexity O(nW)",
        },
    },
    {
        "id": 3,
        "code": "HW-109",
        "title": "تطبيق إدارة الحالة المتكامل باستخدام Zustand و React Query",
        "short_title": "إدارة الحالة بـ Zustand",
        "track": "تطوير واجهات React",
        "submissions_count": 340,
        "total_students": 348,
        "due_date": "10 سبتمبر 2024",
        "status": "completed",
        "status_label": "مكتمل ومرصود",
        "auto_tests_pass_rate": "95.1%",
        "sample_submission": {
            "student_name": "عمر خالد الدوسري",
            "student_code": "#ST-2024-032",
            "repo_url": "github.com/omar-d/react-state-lab",
            "grade": "28 / 40",
            "feedback": "تأخر في معالجة أخطاء الشبكة داخل Query Cache.",
            "pipeline_passed": False,
            "tests_summary": "10/14 Tests Passed",
        },
    },
]

# In-memory fallback submissions for offline mode
_SUBMISSIONS_DB = []


def is_db_active():
    """Verify live connection and required tables exist in database."""
    try:
        ok, _, tables, _ = check_connection()
        return ok and "homework" in tables and "submissions" in tables
    except Exception:
        return False


def get_homework_summary():
    """
    Returns aggregated homework metrics computed directly from the live database.
    Does not use invented or hardcoded numbers when database is active.
    """
    if is_db_active():
        try:
            sql_hw = """
                SELECT 
                    COUNT(*) as active_count,
                    COUNT(CASE WHEN status = 'grading' THEN 1 END) as pending_reviews
                FROM homework;
            """
            hw_rows = execute_query(sql_hw, fetch=True)
            hw_info = hw_rows[0] if hw_rows else {"active_count": 0, "pending_reviews": 0}

            sql_sub = """
                SELECT 
                    COUNT(*) as total_submissions,
                    COUNT(CASE WHEN pipeline_passed = true THEN 1 END) as auto_evaluated,
                    COUNT(CASE WHEN status = 'late' THEN 1 END) as overdue_count
                FROM submissions;
            """
            sub_rows = execute_query(sql_sub, fetch=True)
            sub_info = sub_rows[0] if sub_rows else {"total_submissions": 0, "auto_evaluated": 0, "overdue_count": 0}

            return {
                "active_count": hw_info.get("active_count") or 0,
                "pending_reviews": hw_info.get("pending_reviews") or 0,
                "auto_evaluated": sub_info.get("auto_evaluated") or 0,
                "overdue_count": sub_info.get("overdue_count") or 0,
            }
        except Exception as e:
            logger.error(f"Error calculating homework summary from DB: {e}")
            raise

    return {
        "active_count": 3,
        "pending_reviews": 1,
        "auto_evaluated": 0,
        "overdue_count": 0,
    }


def get_all_homework(student_id=None):
    """
    Retrieve all homework assignments from the database.
    If student_id is provided, attaches the student's personal submission if exists.
    """
    if is_db_active():
        try:
            sql = "SELECT * FROM homework ORDER BY id ASC;"
            rows = execute_query(sql, fetch=True)
            if rows:
                homework_list = [dict(r) for r in rows]

                # If student_id is given, resolve student UUID and attach personal submission
                if student_id:
                    for h in homework_list:
                        sub = get_student_submission(h["id"], student_id)
                        if sub:
                            h["my_submission"] = sub
                return homework_list
        except Exception as e:
            logger.error(f"Error querying homework from DB: {e}")
            raise

    # Fallback mode
    result = []
    for h in _HOMEWORK_DB:
        item = dict(h)
        if student_id:
            sub = next((s for s in _SUBMISSIONS_DB if s.get("homework_id") == h["id"] and str(s.get("student_id")) == str(student_id)), None)
            if sub:
                item["my_submission"] = sub
        result.append(item)
    return result


def get_homework_by_id(hw_id: int):
    """Retrieve single homework assignment details."""
    if not hw_id:
        return None

    if is_db_active():
        try:
            sql = "SELECT * FROM homework WHERE id = %s LIMIT 1;"
            rows = execute_query(sql, (int(hw_id),), fetch=True)
            if rows:
                homework = dict(rows[0])
                q_rows = execute_query("""SELECT q.id, q.category, q.prompt, q.options, q.correct_index,
                    q.points, hq.question_order AS order_index, hq.points AS assessment_points
                    FROM homework_questions hq
                    JOIN questions q ON q.id = hq.question_id
                    WHERE hq.homework_id=%s
                    ORDER BY hq.question_order, hq.id;""", (hw_id,), fetch=True) or []
                if not q_rows:
                    q_rows = execute_query(
                        "SELECT id, category, prompt, options, correct_index, points, order_index FROM questions WHERE homework_id=%s ORDER BY order_index, id;",
                        (hw_id,), fetch=True
                    ) or []
                homework["questions"] = [{**dict(q), "type": dict(q).get("category")} for q in q_rows]
                return homework
            return None
        except Exception as e:
            # A database awaiting migrations 003/004 must not break reads.
            logger.warning(f"Homework assessment columns unavailable; using development fallback: {e}")

    for h in _HOMEWORK_DB:
        if h["id"] == hw_id:
            return h
    return None


def get_student_submission(homework_id: int, student_id):
    """Retrieve the submission record for a specific homework and student."""
    if not homework_id or not student_id:
        return None

    if is_db_active():
        try:
            sql = """
                SELECT 
                    id, homework_id, student_id, student_name, student_code,
                    repo_url, code_snippet, grade, feedback, pipeline_passed,
                    tests_summary, status,
                    TO_CHAR(submitted_at, 'YYYY-MM-DD HH24:MI') as submitted_at,
                    graded_at
                FROM submissions
                WHERE homework_id = %s AND (CAST(student_id AS TEXT) = %s OR student_code = %s)
                ORDER BY submitted_at DESC
                LIMIT 1;
            """
            rows = execute_query(sql, (int(homework_id), str(student_id), str(student_id)), fetch=True)
            if rows:
                return dict(rows[0])
            return None
        except Exception as e:
            logger.error(f"Error querying student submission from DB: {e}")
            raise

    return next(
        (s for s in _SUBMISSIONS_DB if s.get("homework_id") == int(homework_id) and str(s.get("student_id")) == str(student_id)),
        None
    )


def submit_homework(homework_id: int, student_id, repo_url: str, code_snippet: str = None):
    """
    Submits student work for a homework assignment.
    Validates existence of homework and student records to prevent foreign key errors.
    Handles duplicate submissions by updating the existing record.
    Returns the created/updated submission dictionary.
    """
    # 1. Validation of required inputs
    if not homework_id:
        raise ValueError("معرّف التكليف البرمجي مطلوب.")
    if not student_id:
        raise ValueError("معرّف الطالب مطلوب.")
    if not repo_url or not str(repo_url).strip():
        raise ValueError("يرجى إدخال رابط مستودع الكود (GitHub).")

    cleaned_repo = str(repo_url).strip()[:500]
    cleaned_code = str(code_snippet).strip()[:5000] if code_snippet else None

    if is_db_active():
        try:
            # 2. Verify homework exists in DB
            hw_row = execute_query("SELECT id, title FROM homework WHERE id = %s LIMIT 1;", (int(homework_id),), fetch=True)
            if not hw_row:
                raise ValueError(f"التكليف البرمجي برقم {homework_id} غير مسجل في النظام.")

            # 3. Verify student exists in DB
            sql_student = """
                SELECT s.id, u.full_name, s.student_code
                FROM students s
                JOIN users u ON s.id = u.id
                WHERE CAST(s.id AS TEXT) = %s OR s.student_code = %s
                LIMIT 1;
            """
            st_rows = execute_query(sql_student, (str(student_id), str(student_id)), fetch=True)
            if not st_rows:
                raise ValueError(f"سجل الطالب غير مسجل في قاعدة البيانات.")

            real_student = st_rows[0]
            real_student_id = str(real_student["id"])
            student_name = real_student["full_name"]
            student_code = real_student["student_code"]

            # 4. Check for existing submission (duplicate handling)
            check_sql = "SELECT id FROM submissions WHERE homework_id = %s AND student_id = %s LIMIT 1;"
            existing = execute_query(check_sql, (int(homework_id), real_student_id), fetch=True)

            if existing:
                # Update existing submission
                update_sql = """
                    UPDATE submissions
                    SET repo_url = %s,
                        code_snippet = %s,
                        status = 'submitted',
                        pipeline_passed = false,
                        tests_summary = 'تم تحديث الكود · قيد الفحص الآلي بالـ CI/CD',
                        submitted_at = CURRENT_TIMESTAMP
                    WHERE homework_id = %s AND student_id = %s
                    RETURNING id, homework_id, student_id, student_name, student_code,
                              repo_url, code_snippet, grade, feedback, pipeline_passed,
                              tests_summary, status,
                              TO_CHAR(submitted_at, 'YYYY-MM-DD HH24:MI') as submitted_at;
                """
                sub_rows = execute_query(update_sql, (cleaned_repo, cleaned_code, int(homework_id), real_student_id), fetch=True)
            else:
                # Insert new submission
                insert_sql = """
                    INSERT INTO submissions (
                        homework_id, student_id, student_name, student_code,
                        repo_url, code_snippet, status, pipeline_passed, tests_summary
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, 'submitted', false, 'تم الاستلام · قيد الفحص الآلي بالـ CI/CD'
                    )
                    RETURNING id, homework_id, student_id, student_name, student_code,
                              repo_url, code_snippet, grade, feedback, pipeline_passed,
                              tests_summary, status,
                              TO_CHAR(submitted_at, 'YYYY-MM-DD HH24:MI') as submitted_at;
                """
                sub_rows = execute_query(
                    insert_sql,
                    (int(homework_id), real_student_id, student_name, student_code, cleaned_repo, cleaned_code),
                    fetch=True
                )

            # 5. Update submissions_count in homework table
            count_update_sql = """
                UPDATE homework
                SET submissions_count = (SELECT COUNT(*) FROM submissions WHERE homework_id = %s)
                WHERE id = %s;
            """
            execute_query(count_update_sql, (int(homework_id), int(homework_id)), fetch=False)

            if sub_rows:
                return dict(sub_rows[0])
            raise RuntimeError("فشل حفظ بيانات التسليم في قاعدة البيانات.")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Database error during submit_homework: {e}")
            raise

    # Offline / Fallback mode
    existing_idx = next((i for i, s in enumerate(_SUBMISSIONS_DB) if s["homework_id"] == int(homework_id) and str(s["student_id"]) == str(student_id)), None)
    record = {
        "id": existing_idx + 1 if existing_idx is not None else len(_SUBMISSIONS_DB) + 1,
        "homework_id": int(homework_id),
        "student_id": str(student_id),
        "student_name": "طالب تجريبي",
        "student_code": "#ST-DEMO",
        "repo_url": cleaned_repo,
        "code_snippet": cleaned_code,
        "status": "submitted",
        "pipeline_passed": False,
        "tests_summary": "تم الاستلام · قيد الفحص الآلي بالـ CI/CD",
        "submitted_at": "الآن",
    }
    if existing_idx is not None:
        _SUBMISSIONS_DB[existing_idx] = record
    else:
        _SUBMISSIONS_DB.append(record)
    return record


def get_homework_submissions(homework_id: int = None):
    """
    Retrieve real submission records from the submissions table.
    Joins with homework, students, and users to return full metadata.
    """
    if is_db_active():
        try:
            sql = """
                SELECT 
                    sub.id,
                    sub.homework_id,
                    h.code as homework_code,
                    h.title as homework_title,
                    sub.student_id,
                    COALESCE(sub.student_name, u.full_name) as student_name,
                    COALESCE(sub.student_code, s.student_code) as student_code,
                    COALESCE(u.initials, SUBSTRING(u.full_name, 1, 2)) as student_initials,
                    sub.repo_url,
                    sub.code_snippet,
                    sub.grade,
                    sub.feedback,
                    sub.pipeline_passed,
                    sub.tests_summary,
                    sub.status,
                    TO_CHAR(sub.submitted_at, 'YYYY-MM-DD HH24:MI') as submitted_at,
                    sub.graded_at
                FROM submissions sub
                JOIN homework h ON sub.homework_id = h.id
                JOIN students s ON sub.student_id = s.id
                JOIN users u ON s.id = u.id
                WHERE (%s IS NULL OR sub.homework_id = %s)
                ORDER BY sub.submitted_at DESC;
            """
            rows = execute_query(sql, (homework_id, homework_id), fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
            return []
        except Exception as e:
            logger.error(f"Error querying homework submissions from DB: {e}")
            raise

    # Fallback mode
    if homework_id:
        return [s for s in _SUBMISSIONS_DB if s.get("homework_id") == int(homework_id)]
    return list(_SUBMISSIONS_DB)


def grade_submission(submission_id: int, grade: str, feedback: str = None):
    """
    Update the grade and feedback for a submission (admin/teacher action).
    Returns the updated submission dict.
    """
    if not submission_id:
        raise ValueError("معرّف التسليم مطلوب.")
    if grade is None:
        raise ValueError("الدرجة مطلوبة.")

    cleaned_grade = str(grade).strip()[:50]
    cleaned_feedback = str(feedback).strip()[:2000] if feedback else None

    if is_db_active():
        try:
            sql = """
                UPDATE submissions
                SET grade = %s,
                    feedback = %s,
                    status = 'graded',
                    graded_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, homework_id, student_id, student_name, student_code,
                          repo_url, grade, feedback, pipeline_passed,
                          tests_summary, status,
                          TO_CHAR(submitted_at, 'YYYY-MM-DD HH24:MI') as submitted_at,
                          TO_CHAR(graded_at, 'YYYY-MM-DD HH24:MI') as graded_at;
            """
            rows = execute_query(sql, (cleaned_grade, cleaned_feedback, int(submission_id)), fetch=True)
            if rows:
                return dict(rows[0])
            raise ValueError(f"التسليم رقم {submission_id} غير موجود في قاعدة البيانات.")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Database error during grade_submission: {e}")
            raise

    # Fallback mode
    for s in _SUBMISSIONS_DB:
        if s.get("id") == int(submission_id):
            s["grade"] = cleaned_grade
            s["feedback"] = cleaned_feedback
            s["status"] = "graded"
            return s
    raise ValueError(f"التسليم رقم {submission_id} غير موجود.")


def create_homework(data: dict):
    """Create a new homework assignment."""
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("عنوان التكليف مطلوب.")

    code = (data.get("code") or "").strip()
    if not code:
        code = f"HW-{len(_HOMEWORK_DB) + 1:03d}"

    short_title = title[:50]
    track = (data.get("track") or "هندسة برمجيات الأنظمة").strip()
    due_date = (data.get("due_date") or "الأسبوع القادم").strip()
    instructions = (data.get("instructions") or "").strip()
    max_grade = int(data.get("max_grade") or 40)

    if is_db_active():
        try:
            sql = """
                INSERT INTO homework (code, title, short_title, track, due_date, instructions, status, status_label, submissions_count, total_students, max_grade)
                VALUES (%s, %s, %s, %s, %s, %s, 'open', 'مفتوح للتسليم', 0, 348, %s)
                RETURNING *;
            """
            rows = execute_query(sql, (code, title, short_title, track, due_date, instructions, max_grade), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating homework in DB: {e}")
            raise

    new_h = {
        "id": max([h["id"] for h in _HOMEWORK_DB], default=10) + 1,
        "code": code,
        "title": title,
        "short_title": short_title,
        "track": track,
        "due_date": due_date,
        "instructions": instructions,
        "status": "open",
        "status_label": "مفتوح للتسليم",
        "submissions_count": 0,
        "total_students": 348,
        "max_grade": max_grade,
    }
    _HOMEWORK_DB.append(new_h)
    return new_h


def update_homework(hw_id: int, data: dict):
    """Update an existing homework assignment."""
    title = (data.get("title") or "").strip()
    code = (data.get("code") or "").strip()
    track = (data.get("track") or "").strip()
    due_date = (data.get("due_date") or "").strip()
    instructions = (data.get("instructions") or "").strip()
    status = data.get("status", "open")
    status_label = "مغلق للتصحيح" if status == "grading" else ("مكتمل" if status == "completed" else "مفتوح للتسليم")

    if is_db_active():
        try:
            sql = """
                UPDATE homework
                SET title = COALESCE(NULLIF(%s, ''), title),
                    code = COALESCE(NULLIF(%s, ''), code),
                    track = COALESCE(NULLIF(%s, ''), track),
                    due_date = COALESCE(NULLIF(%s, ''), due_date),
                    instructions = COALESCE(NULLIF(%s, ''), instructions),
                    status = %s,
                    status_label = %s
                WHERE id = %s
                RETURNING *;
            """
            rows = execute_query(sql, (title, code, track, due_date, instructions, status, status_label, int(hw_id)), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error updating homework in DB: {e}")
            raise

    for h in _HOMEWORK_DB:
        if h["id"] == int(hw_id):
            if title: h["title"] = title
            if code: h["code"] = code
            if track: h["track"] = track
            if due_date: h["due_date"] = due_date
            if instructions: h["instructions"] = instructions
            h["status"] = status
            h["status_label"] = status_label
            return h
    return None


def delete_homework(hw_id: int):
    """Delete a homework assignment and cascade delete all submissions."""
    if not hw_id:
        raise ValueError("معرّف التكليف مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM homework WHERE id = %s;", (int(hw_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting homework from DB: {e}")
            raise

    global _HOMEWORK_DB
    before = len(_HOMEWORK_DB)
    _HOMEWORK_DB = [h for h in _HOMEWORK_DB if h["id"] != int(hw_id)]
    if len(_HOMEWORK_DB) < before:
        deleted = True
    return deleted


def delete_submission(submission_id: int):
    """Delete a student submission."""
    if not submission_id:
        raise ValueError("معرّف التسليم مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM submissions WHERE id = %s;", (int(submission_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting submission from DB: {e}")
            raise

    global _SUBMISSIONS_DB
    before = len(_SUBMISSIONS_DB)
    _SUBMISSIONS_DB = [s for s in _SUBMISSIONS_DB if s.get("id") != int(submission_id)]
    if len(_SUBMISSIONS_DB) < before:
        deleted = True
    return deleted


def save_homework_questions(homework_id: int, questions: list):
    """Reuse the assessment question validator for manual homework questions (allows admin editing anytime)."""
    questions = exam_service._validate_questions(questions)
    homework = get_homework_by_id(homework_id)
    homework["questions"] = questions
    homework["max_grade"] = sum(question["points"] for question in questions)
    if is_db_active():
        execute_query("DELETE FROM homework_questions WHERE homework_id = %s;", (homework_id,), fetch=False)
        for question in questions:
            question_id = exam_service._ensure_question_record(question)
            execute_query("""INSERT INTO homework_questions
                (homework_id, question_id, question_order, points)
                VALUES (%s, %s, %s, %s);""", (
                homework_id, question_id, question["order_index"], question["points"]
            ), fetch=False)
    return homework


def publish_homework(homework_id: int):
    homework = get_homework_by_id(homework_id)
    homework["questions"] = exam_service._validate_questions(homework.get("questions", []))
    homework["status"] = "published"
    homework["status_label"] = "منشور للطلاب"
    if is_db_active():
        execute_query("UPDATE homework SET status='published', status_label='منشور للطلاب' WHERE id=%s;", (homework_id,), fetch=False)
    return homework


def _attempts_table_available():
    """Some DBs provision exams/questions before assessment_attempts. Fall back to memory in that case."""
    try:
        ok, _, tables, _ = check_connection()
        return ok and "assessment_attempts" in tables
    except Exception:
        return False


def get_homework_attempt(homework_id: int, student_id):
    if is_db_active() and _attempts_table_available():
        rows = execute_query("SELECT * FROM assessment_attempts WHERE assessment_type='homework' AND assessment_id=%s AND student_id=%s LIMIT 1;", (homework_id, student_id), fetch=True)
        return dict(rows[0]) if rows else None
    return exam_service._ATTEMPTS_DB.get(("homework", int(homework_id), str(student_id)))


def start_homework_attempt(homework_id: int, student_id):
    """Create one in-progress homework attempt through the shared lifecycle."""
    homework = get_homework_by_id(homework_id)
    if homework.get("status") != "published":
        raise ValueError("هذا الواجب غير منشور للطلاب.")
    return exam_service.start_assessment_attempt(
        "homework", homework_id, student_id,
        len(homework.get("questions", [])), homework.get("duration_seconds", 0)
    )


def submit_homework_answers(homework_id: int, student_id, answers: dict):
    """One locked auto-graded assignment attempt, shared with exam attempt storage."""
    key = ("homework", int(homework_id), str(student_id))
    existing_attempt = get_homework_attempt(homework_id, student_id)
    if existing_attempt and existing_attempt.get("status") not in ("in_progress", "expired"):
        raise ValueError("تم تسليم هذا الواجب مسبقاً وهو مقفل.")
    homework = get_homework_by_id(homework_id)
    if homework.get("status") != "published":
        raise ValueError("هذا الواجب غير منشور للطلاب.")
    questions = exam_service._validate_questions(homework.get("questions", []))
    score = sum(question["points"] for question in questions if str(answers.get(str(question["id"]), "")) == str(question["correct_index"]))
    total = sum(question["points"] for question in questions)
    correct_count = sum(1 for question in questions if str(answers.get(str(question["id"]), "")) == str(question["correct_index"]))
    attempt = {"assessment_type":"homework", "assessment_id":int(homework_id), "student_id":str(student_id), "answers":answers, "score":score, "total_score":total, "correct_count":correct_count, "total_questions":len(questions), "percentage":round(score * 100 / total, 2), "locked":True, "status":"submitted", "submitted_answers":answers}
    if is_db_active() and _attempts_table_available():
        try:
            if existing_attempt and existing_attempt.get("status") in ("in_progress", "expired"):
                rows = execute_query("""UPDATE assessment_attempts
                    SET answers=%s, submitted_answers=%s, score=%s, total_score=%s,
                        correct_count=%s, total_questions=%s, locked=TRUE,
                        status='submitted', submit_time=CURRENT_TIMESTAMP,
                        submitted_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND status IN ('in_progress', 'expired') RETURNING *;""", (
                    json.dumps(answers), json.dumps(answers), score, total,
                    correct_count, len(questions), existing_attempt["id"]
                ), fetch=True)
            else:
                rows = execute_query("""INSERT INTO assessment_attempts
                    (assessment_type, assessment_id, student_id, answers, score, total_score,
                     correct_count, total_questions, locked, status, submit_time, submitted_answers)
                    VALUES ('homework',%s,%s,%s,%s,%s,%s,%s,TRUE,'submitted',CURRENT_TIMESTAMP,%s)
                    RETURNING *;""", (
                    homework_id, student_id, json.dumps(answers), score, total,
                    correct_count, len(questions), json.dumps(answers)
                ), fetch=True)
            saved_attempt = dict(rows[0])
            exam_service._save_student_answers(saved_attempt["id"], questions, answers)
            return saved_attempt
        except Exception as error:
            if "unique" in str(error).lower():
                raise ValueError("تم تسليم هذا الواجب مسبقاً وهو مقفل.") from error
            raise
    exam_service._ATTEMPTS_DB[key] = attempt
    return attempt
