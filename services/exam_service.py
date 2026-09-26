"""
Exam & Question Bank Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import json
import logging
from datetime import datetime, timezone
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

# Empty — all exams and questions come from the Supabase DB.
# Do NOT add mock exams here; if DB is offline the page will show an empty list.
_EXAMS_DB = []
_QUESTION_BANK = []


# Assessment attempts are deliberately kept separately from presentation state.
# In production the equivalent rows live in assessment_attempts (migration 003).
_ATTEMPTS_DB = {}


def _validate_questions(questions):
    """Validate the supported assessment question types used by the LMS."""
    if not questions:
        raise ValueError("أضف سؤالاً واحداً على الأقل قبل المراجعة أو النشر.")
    cleaned = []
    for order, raw in enumerate(questions, 1):
        kind = str(raw.get("type", raw.get("category", "mcq")).lower())
        prompt = (raw.get("prompt") or "").strip()
        points = int(raw.get("points") or 1)
        options = raw.get("options") or []
        if isinstance(options, str):
            options = [value.strip() for value in options.split("|") if value.strip()]
        if kind == "essay":
            if not prompt or points < 1:
                raise ValueError("السؤال المقالي يحتاج نصاً ودرجة موجبة.")
            cleaned.append({
                "id": raw.get("id") or order,
                "source_id": raw.get("id"),
                "type": "essay",
                "prompt": prompt,
                "options": [],
                "correct_index": None,
                "points": points,
                "order_index": order,
            })
            continue
        if kind == "boolean":
            options = ["صح", "خطأ"]
        if kind not in ("mcq", "boolean") or not prompt or len(options) != (4 if kind == "mcq" else 2):
            raise ValueError("كل سؤال اختيار متعدد يحتاج أربعة خيارات، وسؤال صح/خطأ يحتاج خيارين.")
        correct_index = int(raw.get("correct_index", 0))
        if correct_index not in range(len(options)) or points < 1:
            raise ValueError("اختر الإجابة الصحيحة وأدخل درجة موجبة لكل سؤال.")
        cleaned.append({"id": raw.get("id") or order, "source_id": raw.get("id"), "type": kind, "prompt": prompt,
                        "options": options, "correct_index": correct_index, "points": points,
                        "order_index": order})
    return cleaned


def save_exam_questions(exam_id: int, questions: list):
    """Replace an exam's ordered questions as one validated unit (allows admin editing anytime)."""
    questions = _validate_questions(questions)
    exam = get_exam_by_id(exam_id)
    if is_db_active():
        execute_query("DELETE FROM exam_questions WHERE exam_id = %s;", (exam_id,), fetch=False)
        for q in questions:
            question_id = _ensure_question_record(q)
            execute_query("""INSERT INTO exam_questions (exam_id, question_id, question_order, points)
                VALUES (%s, %s, %s, %s);""", (exam_id, question_id, q["order_index"], q["points"]), fetch=False)
        execute_query("UPDATE exams SET total_questions = %s, max_score = %s WHERE id = %s;",
                      (len(questions), sum(q["points"] for q in questions), exam_id), fetch=False)
    else:
        exam["questions"] = questions
        exam["total_questions"] = len(questions)
        exam["max_score"] = sum(q["points"] for q in questions)
    return exam


def _parse_iso_datetime(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    s = str(val).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def is_exam_available_now(exam: dict) -> tuple:
    """
    Check if an exam is currently open based on real schedule window (starts_at, ends_at) and status.
    Returns: (can_take: bool, state_code: str, message: str)
    state_code: 'open' | 'upcoming' | 'expired' | 'closed'
    """
    if not exam:
        return False, "closed", "الاختبار غير متوفر."

    status = (exam.get("status") or "").lower()
    if status in ("completed", "closed", "draft"):
        return False, "closed", "هذا الاختبار مغلق حالياً من قِبل الإدارة."

    now = datetime.now(timezone.utc)
    starts_at = _parse_iso_datetime(exam.get("starts_at"))
    ends_at = _parse_iso_datetime(exam.get("ends_at"))

    if starts_at and now < starts_at:
        local_time_str = starts_at.strftime("%Y-%m-%d %H:%M")
        return False, "upcoming", f"الاختبار مجدول وسيبدأ في: {local_time_str}"

    if ends_at and now > ends_at:
        local_time_str = ends_at.strftime("%Y-%m-%d %H:%M")
        return False, "expired", f"انتهت فترة الاختبار المحددة في: {local_time_str}"

    return True, "open", "الاختبار متاح الآن للبدء والتسليم."


def create_exam(data: dict):
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("عنوان الاختبار مطلوب.")

    duration_minutes = int(data.get("duration_minutes") or 60)
    total_questions = int(data.get("total_questions") or 0)
    scheduled_date = (data.get("scheduled_date") or "").strip()
    starts_at = _parse_iso_datetime(data.get("starts_at"))
    ends_at = _parse_iso_datetime(data.get("ends_at"))
    status = (data.get("status") or "scheduled").strip()
    status_map = {
        "active": "جارٍ الآن",
        "published": "منشور",
        "scheduled": "مجدول",
        "completed": "منتهي ومغلق",
        "draft": "مسودة",
    }
    status_label = status_map.get(status, "مجدول")

    if is_db_active():
        try:
            sql = """
                INSERT INTO exams (title, short_title, duration_minutes, duration_seconds, total_questions, scheduled_date, starts_at, ends_at, status, status_label, progress, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NOW(), NOW())
                RETURNING *;
            """
            rows = execute_query(sql, (
                title, title[:30], duration_minutes, duration_minutes * 60, total_questions,
                scheduled_date, starts_at, ends_at, status, status_label
            ), fetch=True, commit=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating exam in DB: {e}")
            raise

    exam = {
        "id": max([e["id"] for e in _EXAMS_DB], default=100) + 1,
        "title": title,
        "short_title": title[:30],
        "duration_minutes": duration_minutes,
        "duration_seconds": duration_minutes * 60,
        "total_questions": total_questions,
        "scheduled_date": scheduled_date,
        "starts_at": starts_at.isoformat() if starts_at else None,
        "ends_at": ends_at.isoformat() if ends_at else None,
        "status": status,
        "status_label": status_label,
        "progress": 0,
        "questions": [],
    }
    _EXAMS_DB.append(exam)
    return exam


def update_exam(exam_id: int, data: dict):
    if not exam_id:
        raise ValueError("معرّف الاختبار مطلوب.")

    title = (data.get("title") or "").strip() if "title" in data else None
    duration_minutes = int(data.get("duration_minutes") or 60) if data.get("duration_minutes") else None
    total_questions = int(data.get("total_questions")) if data.get("total_questions") is not None else None
    scheduled_date = (data.get("scheduled_date") or "").strip() if "scheduled_date" in data else None
    starts_at = _parse_iso_datetime(data.get("starts_at")) if "starts_at" in data else None
    ends_at = _parse_iso_datetime(data.get("ends_at")) if "ends_at" in data else None
    status = data.get("status")
    status_label = None
    if status:
        status_map = {
            "active": "جارٍ الآن",
            "published": "منشور",
            "scheduled": "مجدول",
            "completed": "منتهي ومغلق",
            "draft": "مسودة",
        }
        status_label = status_map.get(status, "مجدول")

    if is_db_active():
        try:
            sql = """
                UPDATE exams
                SET title = COALESCE(NULLIF(%s, ''), title),
                    short_title = COALESCE(NULLIF(%s, ''), short_title),
                    duration_minutes = COALESCE(%s, duration_minutes),
                    duration_seconds = COALESCE(%s * 60, duration_seconds),
                    total_questions = COALESCE(%s, total_questions),
                    scheduled_date = COALESCE(%s, scheduled_date),
                    starts_at = COALESCE(%s, starts_at),
                    ends_at = COALESCE(%s, ends_at),
                    status = COALESCE(%s, status),
                    status_label = COALESCE(%s, status_label),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *;
            """
            rows = execute_query(sql, (
                title, title[:30] if title else None, duration_minutes, duration_minutes,
                total_questions, scheduled_date, starts_at, ends_at,
                status, status_label, int(exam_id)
            ), fetch=True, commit=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error updating exam in DB: {e}")
            raise

    for e in _EXAMS_DB:
        if e["id"] == int(exam_id):
            if title: e["title"] = title; e["short_title"] = title[:30]
            if duration_minutes: e["duration_minutes"] = duration_minutes; e["duration_seconds"] = duration_minutes * 60
            if total_questions is not None: e["total_questions"] = total_questions
            if scheduled_date is not None: e["scheduled_date"] = scheduled_date
            if "starts_at" in data: e["starts_at"] = starts_at.isoformat() if starts_at else None
            if "ends_at" in data: e["ends_at"] = ends_at.isoformat() if ends_at else None
            if status: e["status"] = status; e["status_label"] = status_label
            return e
    return None


def republish_exam(exam_id: int):
    """Re-activate and republish an exam regardless of whether it ended or was completed."""
    if not exam_id:
        raise ValueError("معرّف الاختبار مطلوب.")

    if is_db_active():
        try:
            sql = """
                UPDATE exams
                SET status = 'active',
                    status_label = 'جارٍ الآن',
                    ends_at = CASE WHEN ends_at IS NOT NULL AND ends_at < NOW() THEN NULL ELSE ends_at END,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *;
            """
            rows = execute_query(sql, (int(exam_id),), fetch=True, commit=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error republishing exam in DB: {e}")
            raise

    for e in _EXAMS_DB:
        if e["id"] == int(exam_id):
            e["status"] = "active"
            e["status_label"] = "جارٍ الآن"
            return e
    return None


def delete_exam(exam_id: int):
    """Delete an exam and its associated questions relations."""
    if not exam_id:
        raise ValueError("معرّف الاختبار مطلوب.")

    if is_db_active():
        try:
            execute_query("DELETE FROM exam_questions WHERE exam_id = %s;", (int(exam_id),), fetch=False, commit=True)
            execute_query("DELETE FROM exams WHERE id = %s;", (int(exam_id),), fetch=False, commit=True)
            return True
        except Exception as e:
            logger.error(f"Error deleting exam in DB: {e}")
            raise

    global _EXAMS_DB
    before = len(_EXAMS_DB)
    _EXAMS_DB = [e for e in _EXAMS_DB if e["id"] != int(exam_id)]
    return len(_EXAMS_DB) < before


def get_student_exam_review(exam_id: int, student_id):
    """
    Retrieve full question-by-question review of a student's completed exam attempt,
    highlighting correct/incorrect answers, model answers, teacher feedback, and scores.
    """
    exam = get_exam_by_id(exam_id)
    if not exam:
        return None

    attempt = get_student_attempt(exam_id, student_id)
    if not attempt or attempt.get("status") not in ("submitted", "pending_essay_grading", "graded"):
        return None

    attempt_id = attempt.get("id")
    answers_map = {}
    if is_db_active() and attempt_id:
        try:
            ans_rows = execute_query(
                "SELECT * FROM student_answers WHERE attempt_id = %s;",
                (int(attempt_id),), fetch=True
            )
            for a in (ans_rows or []):
                answers_map[int(a["question_id"])] = dict(a)
        except Exception as e:
            logger.warning(f"Error loading student_answers for review: {e}")

    raw_answers = attempt.get("answers") or attempt.get("submitted_answers") or {}

    questions = exam.get("questions", [])
    questions_review = []
    correct_count = 0
    incorrect_count = 0

    for idx, q in enumerate(questions, 1):
        qid = int(q["id"])
        qtype = str(q.get("type", q.get("category", "mcq"))).lower()
        points = float(q.get("points") or 1)
        db_ans = answers_map.get(qid, {})

        student_selected_opt = db_ans.get("selected_option")
        student_essay_text = db_ans.get("essay_text") or db_ans.get("selected_text")
        if student_selected_opt is None and str(qid) in raw_answers:
            raw_val = str(raw_answers[str(qid)])
            if raw_val.isdigit():
                student_selected_opt = int(raw_val)
            else:
                student_essay_text = raw_val

        marks_awarded = float(db_ans.get("marks_awarded") or 0.0) if db_ans.get("marks_awarded") is not None else None
        feedback = db_ans.get("feedback")

        options = q.get("options") or []
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except Exception:
                options = [o.strip() for o in options.split("|") if o.strip()]

        correct_idx = q.get("correct_index")
        correct_ans = q.get("correct_answer") or (options[correct_idx] if (correct_idx is not None and 0 <= correct_idx < len(options)) else "")

        is_correct = False
        status_tag = "incorrect"

        if qtype in ("mcq", "boolean"):
            if student_selected_opt is not None and correct_idx is not None and student_selected_opt == correct_idx:
                is_correct = True
                status_tag = "correct"
                correct_count += 1
                if marks_awarded is None:
                    marks_awarded = points
            else:
                is_correct = False
                status_tag = "incorrect"
                incorrect_count += 1
                if marks_awarded is None:
                    marks_awarded = 0.0
        elif qtype == "essay":
            if attempt.get("status") == "pending_essay_grading" and marks_awarded is None:
                status_tag = "pending_grading"
            elif marks_awarded is not None and marks_awarded >= (points / 2.0):
                is_correct = True
                status_tag = "correct"
            else:
                status_tag = "partial" if (marks_awarded and marks_awarded > 0) else "incorrect"

        options_review = []
        for opt_idx, opt_text in enumerate(options):
            options_review.append({
                "index": opt_idx,
                "text": opt_text,
                "is_selected": (student_selected_opt == opt_idx),
                "is_correct": (correct_idx == opt_idx),
            })

        questions_review.append({
            "order": idx,
            "id": qid,
            "prompt": q.get("prompt"),
            "type": qtype,
            "points": points,
            "marks_awarded": marks_awarded if marks_awarded is not None else 0.0,
            "is_correct": is_correct,
            "status_tag": status_tag,
            "options": options_review,
            "correct_index": correct_idx,
            "correct_answer": correct_ans,
            "student_selected_index": student_selected_opt,
            "student_essay_text": student_essay_text,
            "explanation": q.get("explanation"),
            "feedback": feedback,
        })

    return {
        "exam": exam,
        "attempt": attempt,
        "questions": questions_review,
        "score": float(attempt.get("score") or 0.0),
        "total_score": float(attempt.get("total_score") or 0.0),
        "percentage": float(attempt.get("percentage") or round((float(attempt.get("score") or 0.0) / max(1.0, float(attempt.get("total_score") or 1.0))) * 100, 2)),
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "total_questions": len(questions_review),
    }


def publish_exam(exam_id: int):
    """Publish only a reviewed, complete exam; drafts are never student-visible."""
    exam = get_exam_by_id(exam_id)
    questions = _validate_questions(exam.get("questions", []))
    if is_db_active():
        execute_query("UPDATE exams SET status='active', status_label='منشور', total_questions=%s, max_score=%s WHERE id=%s;",
                      (len(questions), sum(q["points"] for q in questions), exam_id), fetch=False)
    else:
        exam.update(status="active", status_label="منشور", questions=questions,
                    total_questions=len(questions), max_score=sum(q["points"] for q in questions))
    return exam


def get_published_exams():
    return [exam for exam in get_all_exams() if exam.get("status") in ("active", "published")]


def _attempts_table_available():
    """Optional table used for tracked exam/homework attempts.
    Some environments have the main exam/question tables but not the attempts table yet.
    In that case we fall back to in-memory state without crashing the UI.
    """
    try:
        ok, _, tables, _ = check_connection()
        return ok and "assessment_attempts" in tables
    except Exception:
        return False


def get_student_attempt(exam_id: int, student_id):
    if is_db_active() and _attempts_table_available():
        try:
            rows = execute_query(
                "SELECT * FROM assessment_attempts WHERE assessment_type='exam' AND assessment_id=%s AND CAST(student_id AS TEXT)=%s LIMIT 1;",
                (int(exam_id), str(student_id)), fetch=True
            )
            return dict(rows[0]) if rows else None
        except Exception as e:
            logger.warning(f"Error in get_student_attempt: {e}")
    return _ATTEMPTS_DB.get(("exam", int(exam_id), str(student_id)))


def start_assessment_attempt(assessment_type: str, assessment_id: int, student_id, total_questions: int, duration_seconds: int = 0):
    """Create one in-progress attempt, or return/update its existing lifecycle row."""
    if assessment_type not in ("exam", "homework"):
        raise ValueError("نوع التقييم غير مدعوم.")
    key = (assessment_type, int(assessment_id), str(student_id))
    if is_db_active() and _attempts_table_available():
        rows = execute_query("""SELECT * FROM assessment_attempts
            WHERE assessment_type=%s AND assessment_id=%s AND student_id=%s LIMIT 1;""",
            (assessment_type, assessment_id, student_id), fetch=True)
        existing = dict(rows[0]) if rows else None
        if existing and existing.get("status") == "submitted":
            raise ValueError("تم تسليم هذا التقييم مسبقاً وهو مقفل.")
        if existing and existing.get("status") == "in_progress":
            return existing
        if existing and existing.get("status") == "expired":
            rows = execute_query("""UPDATE assessment_attempts
                SET status='in_progress', locked=FALSE, started_at=CURRENT_TIMESTAMP,
                    submit_time=NULL, expired_at=NULL, answers='{}'::jsonb,
                    submitted_answers='{}'::jsonb, score=0, total_score=0,
                    correct_count=0, total_questions=%s, duration_seconds=%s
                WHERE id=%s RETURNING *;""", (total_questions, duration_seconds, existing["id"]), fetch=True)
            return dict(rows[0])
        rows = execute_query("""INSERT INTO assessment_attempts
            (assessment_type, assessment_id, student_id, answers, score, total_score,
             correct_count, total_questions, locked, status, started_at, duration_seconds)
            VALUES (%s,%s,%s,'{}'::jsonb,0,0,0,%s,FALSE,'in_progress',CURRENT_TIMESTAMP,%s)
            RETURNING *;""", (assessment_type, assessment_id, student_id, total_questions, duration_seconds), fetch=True)
        return dict(rows[0])

    existing = _ATTEMPTS_DB.get(key)
    if existing and existing.get("status") == "submitted":
        raise ValueError("تم تسليم هذا التقييم مسبقاً وهو مقفل.")
    if existing and existing.get("status") == "in_progress":
        return existing
    attempt = {
        "assessment_type": assessment_type, "assessment_id": int(assessment_id),
        "student_id": str(student_id), "answers": {}, "score": 0,
        "total_score": 0, "correct_count": 0, "total_questions": total_questions,
        "locked": False, "status": "in_progress", "submitted_answers": {},
        "started_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration_seconds,
    }
    _ATTEMPTS_DB[key] = attempt
    return attempt


def start_exam_attempt(exam_id: int, student_id):
    exam = get_exam_by_id(exam_id)
    if exam.get("status") not in ("active", "published"):
        raise ValueError("هذا الاختبار غير منشور للطلاب.")
    return start_assessment_attempt("exam", exam_id, student_id, len(exam.get("questions", [])), exam.get("duration_seconds", 0))


def _ensure_question_record(question):
    """Reuse a question-bank row when selected; otherwise create one reusable row."""
    question_id = question.get("source_id")
    if question_id:
        rows = execute_query("SELECT id FROM questions WHERE id = %s LIMIT 1;", (int(question_id),), fetch=True)
        if rows:
            question["id"] = int(rows[0]["id"])
            return question["id"]

    rows = execute_query("""INSERT INTO questions
        (category, prompt, options, correct_index, points, order_index, essay_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;""", (
        question["type"], question["prompt"],
        json.dumps(question["options"], ensure_ascii=False),
        question["correct_index"], question["points"],
        question["order_index"], question.get("essay_text"),
    ), fetch=True)
    question["id"] = int(rows[0]["id"])
    return question["id"]


def _save_student_answers(attempt_id, questions, answers):
    """Persist normalized answers after a successful attempt insert."""
    try:
        execute_query("DELETE FROM student_answers WHERE attempt_id = %s;", (attempt_id,), fetch=False)
    except Exception as e:
        logger.warning(f"Could not clean old student answers: {e}")

    for question in questions:
        raw_answer = answers.get(str(question["id"]), "")
        answer_type = question["type"]
        selected_option = None
        selected_text = str(raw_answer) if raw_answer != "" else None
        essay_text = str(raw_answer) if answer_type == "essay" and raw_answer != "" else None
        if answer_type in ("mcq", "boolean") and str(raw_answer).lstrip("-").isdigit():
            selected_option = int(raw_answer)
        is_correct = answer_type != "essay" and str(raw_answer) == str(question["correct_index"])
        try:
            execute_query("""INSERT INTO student_answers
                (attempt_id, question_id, answer_type, selected_option, selected_text, essay_text, marks_awarded)
                VALUES (%s, %s, %s, %s, %s, %s, %s);""", (
                attempt_id, int(question["id"]), answer_type, selected_option,
                selected_text, essay_text, question["points"] if is_correct else 0,
            ), fetch=False)
        except Exception as e:
            logger.warning(f"Error inserting student_answer for q {question['id']}: {e}")


def submit_exam(exam_id: int, student_id, answers: dict):
    """Score and lock a single student attempt. The unique DB constraint is the race-safe lock."""
    existing_attempt = get_student_attempt(exam_id, student_id)
    if existing_attempt and existing_attempt.get("status") in ("submitted", "graded"):
        raise ValueError("تم تسليم هذا الاختبار مسبقاً وهو مقفل.")
    exam = get_exam_by_id(exam_id)
    if exam.get("status") not in ("active", "published"):
        raise ValueError("هذا الاختبار غير منشور للطلاب.")
    questions = _validate_questions(exam.get("questions", []))
    has_essay = any(q.get("type") == "essay" for q in questions)
    mcq_questions = [q for q in questions if q.get("type") != "essay"]

    correct = sum(1 for q in mcq_questions if str(answers.get(str(q["id"]), "")) == str(q.get("correct_index")))
    score = sum(q["points"] for q in mcq_questions if str(answers.get(str(q["id"]), "")) == str(q.get("correct_index")))
    mcq_total = sum(q["points"] for q in mcq_questions)
    total = sum(q["points"] for q in questions)
    attempt_status = "pending_essay_grading" if has_essay else "submitted"
    percentage = round(score * 100 / total, 2) if total > 0 else 0

    attempt = {
        "assessment_type": "exam", "assessment_id": int(exam_id), "student_id": str(student_id),
        "answers": answers, "score": score, "total_score": total, "correct_count": correct,
        "total_questions": len(questions), "percentage": percentage, "locked": True,
        "status": attempt_status, "has_essay": has_essay, "mcq_score": score, "mcq_total": mcq_total,
        "submitted_answers": answers, "submit_time": datetime.now(timezone.utc).isoformat()
    }
    if is_db_active() and _attempts_table_available():
        if existing_attempt and existing_attempt.get("status") in ("in_progress", "expired", "pending_essay_grading"):
            rows = execute_query("""UPDATE assessment_attempts
                SET answers=%s, submitted_answers=%s, score=%s, total_score=%s,
                    correct_count=%s, total_questions=%s, locked=TRUE,
                    status=%s, submit_time=CURRENT_TIMESTAMP,
                    submitted_at=CURRENT_TIMESTAMP
                WHERE id=%s RETURNING *;""", (
                json.dumps(answers), json.dumps(answers), score, total,
                correct, len(questions), attempt_status, existing_attempt["id"]
            ), fetch=True)
        else:
            rows = execute_query("""INSERT INTO assessment_attempts
                (assessment_type, assessment_id, student_id, answers, score, total_score,
                 correct_count, total_questions, locked, status, submit_time, submitted_answers)
                VALUES ('exam',%s,%s,%s,%s,%s,%s,%s,TRUE,%s,CURRENT_TIMESTAMP,%s)
                RETURNING *;""", (
                exam_id, student_id, json.dumps(answers), score, total, correct,
                len(questions), attempt_status, json.dumps(answers)
            ), fetch=True)
        saved_attempt = dict(rows[0])
        _save_student_answers(saved_attempt["id"], questions, answers)
        saved_attempt["has_essay"] = has_essay
        saved_attempt["mcq_score"] = score
        saved_attempt["mcq_total"] = mcq_total

        # Safely record or update in the results table so it shows in student results & teacher dashboard
        try:
            from services import student_service
            student = student_service.get_student_by_id(str(student_id))
            if student:
                if has_essay:
                    status_val = "pending_essay_grading"
                    grade_label = "بانتظار تصحيح المقالي"
                    grade_badge = "badge-warn"
                    score_disp = f"{score} / {total} (مبدئي)"
                else:
                    status_val = "passed" if percentage >= 50 else "repeat"
                    grade_label = "ممتاز" if percentage >= 90 else ("جيد جداً" if percentage >= 80 else ("جيد" if percentage >= 65 else ("مقبول" if percentage >= 50 else "فرصة إعادة")))
                    grade_badge = "badge-success" if percentage >= 50 else "badge-danger"
                    score_disp = f"{score} / {total}"

                existing_res = execute_query(
                    "SELECT id FROM results WHERE CAST(student_id AS TEXT) = %s AND exam_id = %s LIMIT 1;",
                    (str(student["id"]), int(exam["id"])), fetch=True
                )
                st_code = student.get("student_code") or student.get("code") or ""
                st_name = student.get("name") or student.get("username") or "طالب"
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
                        student["id"], st_name, st_code,
                        exam["id"], exam["title"], percentage, score_disp,
                        status_val, grade_badge, grade_label
                    ), fetch=False, commit=True)
        except Exception as re:
            logger.warning(f"Could not auto-insert/update result into results table: {re}")

        return saved_attempt

    _ATTEMPTS_DB[("exam", int(exam_id), str(student_id))] = attempt
    return attempt


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "exams" in tables and "questions" in tables
    except Exception:
        return False


def get_exams_summary():
    """Aggregated exam metrics dynamically linked to database and active exams."""
    from services import student_service
    students_count = student_service.get_students_summary().get("total_count", 8)

    if is_db_active():
        try:
            sql_all_exams = "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'active' THEN 1 END) as active FROM exams;"
            sql_q = "SELECT COUNT(*) as cnt FROM questions;"
            sql_pending = "SELECT COUNT(*) as cnt FROM assessment_attempts WHERE status = 'pending_essay_grading';"

            exam_res = execute_query(sql_all_exams, fetch=True)
            total_exams = exam_res[0]["total"] if exam_res else len(_EXAMS_DB)
            active_cnt = exam_res[0]["active"] if exam_res else sum(1 for e in _EXAMS_DB if e.get("status") == "active")

            q_res = execute_query(sql_q, fetch=True)
            q_cnt = q_res[0]["cnt"] if q_res else len(_QUESTION_BANK)

            pending_res = execute_query(sql_pending, fetch=True)
            pending_cnt = pending_res[0]["cnt"] if pending_res else 0

            return {
                "active_exams": total_exams or len(_EXAMS_DB),
                "today_active_halls": active_cnt,
                "total_participants": students_count,
                "awaiting_grading": pending_cnt,
                "question_bank_count": q_cnt or (len(_QUESTION_BANK) + sum(len(e.get("questions", [])) for e in _EXAMS_DB)),
            }
        except Exception as e:
            logger.warning(f"Error querying exam summary: {e}")

    total_exams = len(_EXAMS_DB)
    active_cnt = sum(1 for e in _EXAMS_DB if e.get("status") == "active")
    q_cnt = len(_QUESTION_BANK) + sum(len(e.get("questions", [])) for e in _EXAMS_DB)
    pending_cnt = sum(1 for a in _ATTEMPTS_DB.values() if isinstance(a, dict) and a.get("status") == "pending_essay_grading")

    return {
        "active_exams": total_exams,
        "today_active_halls": active_cnt,
        "total_participants": students_count,
        "awaiting_grading": pending_cnt,
        "question_bank_count": q_cnt,
    }


def get_all_exams():
    """Retrieve all exams."""
    if is_db_active():
        try:
            sql = "SELECT * FROM exams ORDER BY id ASC;"
            rows = execute_query(sql, fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying exams: {e}")

    return _EXAMS_DB


def get_exam_by_id(exam_id: int):
    """Retrieve single exam details with questions."""
    if is_db_active():
        try:
            sql_exam = "SELECT * FROM exams WHERE id = %s LIMIT 1;"
            e_rows = execute_query(sql_exam, (exam_id,), fetch=True)
            if e_rows:
                exam = dict(e_rows[0])
                sql_questions = """SELECT q.*, eq.question_order, eq.points AS assessment_points
                    FROM exam_questions eq
                    JOIN questions q ON q.id = eq.question_id
                    WHERE eq.exam_id = %s
                    ORDER BY eq.question_order, eq.id;"""
                q_rows = execute_query(sql_questions, (exam_id,), fetch=True)
                if not q_rows:
                    # Preserve visibility of pre-reconciliation rows until a later, approved backfill.
                    q_rows = execute_query(
                        "SELECT *, order_index, points AS assessment_points FROM questions WHERE exam_id = %s ORDER BY order_index, id;",
                        (exam_id,), fetch=True
                    )
                exam["questions"] = [dict(q) for q in q_rows]
                return exam
        except Exception as e:
            logger.warning(f"Error querying exam by ID: {e}")

    for e in _EXAMS_DB:
        if e["id"] == exam_id:
            return e
    return None


def get_question_units():
    """Retrieve organizing units for the question bank."""
    if is_db_active():
        try:
            sql = "SELECT * FROM question_units ORDER BY id ASC;"
            rows = execute_query(sql, fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying question units: {e}")
    return []


def create_question_unit(data: dict):
    """Create a question bank unit grouping related reusable questions."""
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("اسم الوحدة مطلوب.")
    description = (data.get("description") or "").strip()
    if is_db_active():
        try:
            sql = "INSERT INTO question_units (name, description) VALUES (%s, %s) RETURNING *;"
            rows = execute_query(sql, (name, description), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating question unit in DB: {e}")
            raise
    unit = {"id": len(get_question_units()) + 101, "name": name, "description": description}
    return unit


def update_question_unit(unit_id: int, data: dict):
    """Update a unit in the question bank."""
    if not unit_id:
        raise ValueError("معرّف الوحدة مطلوب.")
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if is_db_active():
        try:
            sql = "UPDATE question_units SET name = COALESCE(NULLIF(%s, ''), name), description = %s WHERE id = %s RETURNING *;"
            rows = execute_query(sql, (name, description, int(unit_id)), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error updating question unit in DB: {e}")
            raise
    return {"id": int(unit_id), "name": name or f"Unit {unit_id}", "description": description}


def delete_question_unit(unit_id: int):
    """Delete a unit. The questions remain as reusable bank content unless explicitly removed."""
    if not unit_id:
        raise ValueError("معرّف الوحدة مطلوب للحذف.")
    if is_db_active():
        try:
            execute_query("DELETE FROM question_units WHERE id = %s;", (int(unit_id),), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting question unit in DB: {e}")
            raise
    return True


def get_question_bank():
    """Retrieve questions bank repository."""
    if is_db_active():
        try:
            sql = "SELECT * FROM questions ORDER BY id ASC;"
            rows = execute_query(sql, fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying question bank: {e}")

    return _QUESTION_BANK


def get_question_by_id(question_id: int):
    """Retrieve single question by id."""
    if is_db_active():
        try:
            sql = "SELECT * FROM questions WHERE id = %s LIMIT 1;"
            rows = execute_query(sql, (int(question_id),), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.warning(f"Error querying question by ID: {e}")

    for q in _QUESTION_BANK:
        if q["id"] == int(question_id):
            return q
    return None


def create_question(data: dict):
    """Create a new question in the central question bank."""
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("نص السؤال مطلوب.")

    category = str(data.get("category", "mcq")).lower()
    if category not in ("mcq", "code", "boolean", "essay"):
        category = "mcq"

    difficulty = data.get("difficulty", "متوسط")
    badge_map = {"مبتدئ": "badge-info", "متوسط": "badge-info", "متقدم": "badge-warn", "تحدي برمجي": "badge-danger"}
    difficulty_badge = badge_map.get(difficulty, "badge-info")
    track = (data.get("track") or "الخوارزميات").strip()
    answer_preview = (data.get("answer_preview") or data.get("correct_answer") or "").strip()
    correct_answer = (data.get("correct_answer") or answer_preview).strip()

    options = data.get("options", [])
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            options = [opt.strip() for opt in options.split("\n") if opt.strip()]

    if category == "boolean":
        options = ["صح", "خطأ"]
    elif category in ("essay", "code"):
        options = []
    elif category == "mcq" and len(options) < 2:
        raise ValueError("أسئلة الاختيار من متعدد تحتاج خيارين على الأقل.")

    unit_id = data.get("unit_id")
    points = int(data.get("points") or 1)
    if points < 1:
        raise ValueError("درجة السؤال يجب أن تكون موجبة.")
    correct_index = None if category in ("essay", "code") else int(data.get("correct_index", 0))
    if correct_index is not None and (correct_index < 0 or correct_index >= len(options)):
        raise ValueError("الإجابة الصحيحة يجب أن تشير إلى أحد الخيارات.")

    if is_db_active():
        try:
            sql = """
                INSERT INTO questions (category, difficulty, difficulty_badge, track, prompt, options, correct_index, answer_preview, correct_answer, unit_id, points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
            """
            rows = execute_query(
                sql,
                (category, difficulty, difficulty_badge, track, prompt, json.dumps(options, ensure_ascii=False), correct_index, answer_preview, correct_answer, unit_id, points),
                fetch=True
            )
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating question in DB: {e}")
            raise

    new_q = {
        "id": max([q["id"] for q in _QUESTION_BANK], default=100) + 1,
        "category": category,
        "difficulty": difficulty,
        "difficulty_badge": difficulty_badge,
        "track": track,
        "prompt": prompt,
        "options": options,
        "correct_index": correct_index,
        "answer_preview": answer_preview,
        "correct_answer": correct_answer,
        "unit_id": unit_id,
        "points": points,
    }
    _QUESTION_BANK.append(new_q)
    return new_q


def update_question(question_id: int, data: dict):
    """Update question content, difficulty, category, and answers."""
    if not question_id:
        raise ValueError("معرّف السؤال مطلوب.")

    prompt = (data.get("prompt") or "").strip()
    category = data.get("category", "mcq")
    difficulty = data.get("difficulty", "متوسط")
    badge_map = {"مبتدئ": "badge-info", "متوسط": "badge-info", "متقدم": "badge-warn", "تحدي برمجي": "badge-danger"}
    difficulty_badge = badge_map.get(difficulty, "badge-info")
    track = (data.get("track") or "الخوارزميات").strip()
    answer_preview = (data.get("answer_preview") or data.get("correct_answer") or "").strip()
    correct_answer = (data.get("correct_answer") or answer_preview).strip()

    options = data.get("options")
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            options = [opt.strip() for opt in options.split("\n") if opt.strip()]

    if category == "boolean":
        options = ["صح", "خطأ"]
    elif category in ("essay", "code"):
        options = []

    points = int(data.get("points") or 1) if "points" in data and data.get("points") is not None else None
    if points is not None and points < 1:
        raise ValueError("درجة السؤال يجب أن تكون موجبة.")

    correct_index = None if category in ("essay", "code") else (int(data.get("correct_index", 0)) if "correct_index" in data and data.get("correct_index") is not None else None)

    if is_db_active():
        try:
            sql = """
                UPDATE questions
                SET prompt = %s,
                    category = %s,
                    difficulty = %s,
                    difficulty_badge = %s,
                    track = %s,
                    answer_preview = %s,
                    correct_answer = %s,
                    options = %s,
                    correct_index = %s,
                    points = COALESCE(%s, points)
                WHERE id = %s
                RETURNING *;
            """
            rows = execute_query(
                sql,
                (prompt, category, difficulty, difficulty_badge, track, answer_preview, correct_answer,
                 json.dumps(options, ensure_ascii=False) if options is not None else None,
                 correct_index, points, int(question_id)),
                fetch=True
            )
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error updating question in DB: {e}")
            raise

    for q in _QUESTION_BANK:
        if q["id"] == int(question_id):
            if prompt: q["prompt"] = prompt
            if category: q["category"] = category
            if difficulty:
                q["difficulty"] = difficulty
                q["difficulty_badge"] = difficulty_badge
            if track: q["track"] = track
            if answer_preview: q["answer_preview"] = answer_preview
            if correct_answer: q["correct_answer"] = correct_answer
            if options is not None: q["options"] = options
            if correct_index is not None: q["correct_index"] = correct_index
            if points is not None: q["points"] = points
            return q
    return None


def delete_question(question_id: int):
    """Delete a question from the question bank."""
    if not question_id:
        raise ValueError("معرّف السؤال مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM questions WHERE id = %s;", (int(question_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting question from DB: {e}")
            raise

    global _QUESTION_BANK
    before = len(_QUESTION_BANK)
    _QUESTION_BANK = [q for q in _QUESTION_BANK if q["id"] != int(question_id)]
    if len(_QUESTION_BANK) < before:
        deleted = True
    return deleted


def create_exam(data: dict):
    """Create a new exam."""
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("عنوان الاختبار مطلوب.")

    short_title = title[:50]
    duration_minutes = int(data.get("duration_minutes") or 90)
    duration_seconds = duration_minutes * 60
    total_questions = int(data.get("total_questions") or 10)
    scheduled_date = (data.get("scheduled_date") or "مجدول قريباً").strip()
    status = data.get("status", "scheduled")
    status_label = "جارٍ الآن" if status == "active" else "مجدول"

    if is_db_active():
        try:
            sql = """
                INSERT INTO exams (title, short_title, duration_minutes, duration_seconds, total_questions, scheduled_date, status, status_label, progress)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)
                RETURNING *;
            """
            rows = execute_query(
                sql,
                (title, short_title, duration_minutes, duration_seconds, total_questions, scheduled_date, status, status_label),
                fetch=True
            )
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating exam in DB: {e}")
            raise

    new_exam = {
        "id": max([e["id"] for e in _EXAMS_DB], default=10) + 1,
        "title": title,
        "short_title": short_title,
        "duration_minutes": duration_minutes,
        "duration_seconds": duration_seconds,
        "total_questions": total_questions,
        "scheduled_date": scheduled_date,
        "status": status,
        "status_label": status_label,
        "progress": 0,
        "questions": [],
    }
    _EXAMS_DB.append(new_exam)
    return new_exam


def update_exam(exam_id: int, data: dict):
    """Update exam details."""
    title = (data.get("title") or "").strip()
    duration_minutes = int(data.get("duration_minutes") or 90)
    total_questions = int(data.get("total_questions") or 10)
    scheduled_date = (data.get("scheduled_date") or "").strip()
    status = data.get("status", "scheduled")
    status_label = "جارٍ الآن" if status == "active" else "مجدول"

    if is_db_active():
        try:
            sql = """
                UPDATE exams
                SET title = COALESCE(NULLIF(%s, ''), title),
                    duration_minutes = %s,
                    duration_seconds = %s,
                    total_questions = %s,
                    scheduled_date = COALESCE(NULLIF(%s, ''), scheduled_date),
                    status = %s,
                    status_label = %s
                WHERE id = %s
                RETURNING *;
            """
            rows = execute_query(
                sql,
                (title, duration_minutes, duration_minutes * 60, total_questions, scheduled_date, status, status_label, int(exam_id)),
                fetch=True
            )
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error updating exam in DB: {e}")
            raise

    for e in _EXAMS_DB:
        if e["id"] == int(exam_id):
            if title: e["title"] = title
            e["duration_minutes"] = duration_minutes
            e["total_questions"] = total_questions
            if scheduled_date: e["scheduled_date"] = scheduled_date
            e["status"] = status
            e["status_label"] = status_label
            return e
    return None


def delete_exam(exam_id: int):
    """Delete an exam."""
    if not exam_id:
        raise ValueError("معرّف الاختبار مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM exams WHERE id = %s;", (int(exam_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting exam from DB: {e}")
            raise

    global _EXAMS_DB
    before = len(_EXAMS_DB)
    _EXAMS_DB = [e for e in _EXAMS_DB if e["id"] != int(exam_id)]
    if len(_EXAMS_DB) < before:
        deleted = True
    return deleted
