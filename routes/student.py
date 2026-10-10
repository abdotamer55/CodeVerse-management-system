"""
Student Portal Blueprint
All endpoints are strictly protected under role_required('student').
Routes remain thin and delegate business logic to the service layer.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from routes.auth import role_required
from services import (
    student_service,
    lesson_service,
    homework_service,
    exam_service,
    result_service,
    file_service,
    notification_service,
)

student_bp = Blueprint("student", __name__, url_prefix="/student")


def _get_student_id():
    """Return the student identifier (canonical user_id UUID or username) from session."""
    return session.get("user_id") or session.get("username") or "mariem"


@student_bp.route("")
@student_bp.route("/")
@role_required("student")
def root():
    return redirect(url_for("student.dashboard"))


@student_bp.route("/dashboard")
@role_required("student")
def dashboard():
    student_id = _get_student_id()
    student = student_service.get_student_by_id(student_id)
    lesson_overview = lesson_service.get_student_lesson_overview()
    # Attempt to enrich student with real live stats from DB
    db_stats = student_service.get_student_dashboard_stats(student_id)
    if db_stats:
        student = dict(student) if student else {}
        student.update({
            "completed_lessons": db_stats["completed_lessons"],
            "total_lessons": db_stats["total_lessons"],
            "completed_homework": db_stats["completed_homework"],
            "total_homework": db_stats["total_homework"],
            "overall_grade": db_stats["overall_grade"],
            "active_exams": db_stats["active_exams"],
            "graded_exams_count": db_stats.get("graded_exams_count", 0),
            "highest_exam_score": db_stats.get("highest_exam_score", 0.0),
            "passed_exams_count": db_stats.get("passed_exams_count", 0),
        })
    return render_template(
        "student/dashboard.html",
        user_role="student",
        page_id="dashboard",
        student=student,
        lesson_overview=lesson_overview,
    )


@student_bp.route("/lessons")
@role_required("student")
def lessons():
    student_id = _get_student_id()
    lessons_list = lesson_service.get_all_lessons()
    completed_ids = lesson_service.get_completed_lesson_ids(student_id)
    completed_count = len(completed_ids)
    return render_template(
        "student/lessons.html",
        user_role="student",
        page_id="lessons",
        lessons=lessons_list,
        completed_lesson_ids=completed_ids,
        completed_lessons_count=completed_count,
    )


@student_bp.route("/lessons/<int:lesson_id>")
def lesson_detail(lesson_id):
    if session.get("role") == "admin":
        return redirect(url_for("admin.preview_lesson", lesson_id=lesson_id))
    if session.get("role") != "student":
        flash("يرجى تسجيل الدخول كطالب للوصول لهذه الصفحة.", "error")
        return redirect(url_for("auth.login"))

    student_id = _get_student_id()
    lesson = lesson_service.get_lesson_by_id(lesson_id)
    if not lesson:
        flash("الحصة غير موجودة.", "error")
        return redirect(url_for("student.lessons"))
    is_completed = lesson_service.is_lesson_completed(lesson_id, student_id)
    return render_template(
        "student/lesson.html",
        user_role="student",
        page_id="lessons",
        lesson=lesson,
        is_completed=is_completed,
    )


@student_bp.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
@role_required("student")
def complete_lesson(lesson_id):
    student_id = _get_student_id()
    is_completed = lesson_service.toggle_lesson_completion(lesson_id, student_id)
    if is_completed:
        flash("تم تسجيل إكمال مشاهدة الحصة بنجاح! تم تحديث رصيدك الأكاديمي.", "success")
    else:
        flash("تم إلغاء تحديد إكمال الحصة.", "info")
    return redirect(request.referrer or url_for("student.lesson_detail", lesson_id=lesson_id))


@student_bp.route("/homework")
@role_required("student")
def homework():
    student_id = session.get("user_id")
    homework_list = [item for item in homework_service.get_all_homework(student_id=student_id) if item.get("status") != "draft"]
    # Attach assessment_attempt data as my_submission for quiz-based homework
    for h in homework_list:
        attempt = homework_service.get_homework_attempt(h["id"], student_id)
        if attempt:
            h["my_submission"] = attempt
    return render_template(
        "student/homework.html",
        user_role="student",
        page_id="homework",
        homework=homework_list,
    )


@student_bp.route("/homework/<int:hw_id>")
@role_required("student")
def homework_detail(hw_id):
    homework = homework_service.get_homework_by_id(hw_id)
    if not homework or homework.get("status") == "draft":
        flash("هذا الواجب غير متاح حالياً.", "error")
        return redirect(url_for("student.homework"))
    attempt = homework_service.get_homework_attempt(hw_id, session.get("user_id"))
    return render_template("student/assessment.html", user_role="student", page_id="homework", assessment=homework, assessment_label="الواجب", attempt=attempt, submit_url=url_for("student.submit_homework_answers", hw_id=hw_id))


@student_bp.route("/homework/<int:hw_id>/start", methods=["POST"])
@role_required("student")
def start_homework_attempt(hw_id):
    try:
        homework_service.start_homework_attempt(hw_id, session.get("user_id"))
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("student.homework_detail", hw_id=hw_id))


@student_bp.route("/homework/<int:hw_id>/submit", methods=["POST"])
@role_required("student")
def submit_homework_answers(hw_id):
    try:
        attempt = homework_service.get_homework_attempt(hw_id, session.get("user_id"))
        if not attempt or attempt.get("status") != "in_progress":
            raise ValueError("ابدأ المحاولة قبل إرسال الإجابات.")
        attempt = homework_service.submit_homework_answers(hw_id, session.get("user_id"), request.form.to_dict())
        return render_template("student/assessment-result.html", user_role="student", page_id="homework", assessment=homework_service.get_homework_by_id(hw_id), attempt=attempt)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("student.homework_detail", hw_id=hw_id))


@student_bp.route("/homework/submit", methods=["POST"])
@role_required("student")
def submit_homework_route():
    student_id = session.get("user_id")
    if not student_id:
        flash("يرجى تسجيل الدخول أولاً لتسليم الواجب.", "error")
        return redirect(url_for("auth.login"))

    homework_id = request.form.get("homework_id")
    repo_url = request.form.get("repo_url")
    code_snippet = request.form.get("code_snippet") or request.form.get("notes")

    if not homework_id or not repo_url:
        flash("يرجى اختيار التكليف وإدخال رابط المستودع بشكل صحيح.", "error")
        return redirect(url_for("student.homework"))

    try:
        homework_service.submit_homework(
            homework_id=int(homework_id),
            student_id=student_id,
            repo_url=repo_url,
            code_snippet=code_snippet,
        )
        flash("تم تسجيل تسليم التكليف البرمجي بنجاح وجارٍ فحصه بالـ CI/CD Pipeline.", "success")
    except ValueError as ve:
        flash(str(ve), "error")
    except Exception as e:
        flash("حدث خطأ أثناء حفظ التسليم. يرجى المحاولة لاحقاً.", "error")

    return redirect(url_for("student.homework"))


@student_bp.route("/exams")
@role_required("student")
def exams():
    user_id = session.get("user_id")
    exams_list = exam_service.get_published_exams(student_id=user_id)
    for e in exams_list:
        can_take, state_code, msg = exam_service.is_exam_available_now(e)
        e["is_available"] = can_take
        e["state_code"] = state_code
        e["availability_message"] = msg
        e["my_attempt"] = exam_service.get_student_attempt(e["id"], user_id)
    return render_template(
        "student/exams.html",
        user_role="student",
        page_id="exams",
        exams=exams_list,
    )


@student_bp.route("/exams/<int:exam_id>")
@role_required("student")
def exam_detail(exam_id):
    exam = exam_service.get_exam_by_id(exam_id)
    if not exam or exam.get("status") not in ("active", "published", "scheduled"):
        flash("هذا الاختبار غير منشور أو مغلق.", "error")
        return redirect(url_for("student.exams"))
    user_id = session.get("user_id")
    if not exam_service.is_student_eligible_for_exam(exam, user_id):
        flash("هذا الاختبار مخصص لطلاب محددين فقط وغير متاح لحسابك الأكاديمي.", "error")
        return redirect(url_for("student.exams"))

    attempt = exam_service.get_student_attempt(exam_id, user_id)
    remaining_seconds = exam_service.calculate_attempt_remaining_seconds(attempt, exam)

    can_take, state_code, state_msg = exam_service.is_exam_available_now(exam)
    availability = {
        "can_take": can_take,
        "state_code": state_code,
        "message": state_msg,
    }
    return render_template(
        "student/exam.html",
        user_role="student",
        page_id="exams",
        exam=exam,
        attempt=attempt,
        remaining_seconds=remaining_seconds,
        availability=availability,
    )


@student_bp.route("/exams/<int:exam_id>/start", methods=["POST"])
@role_required("student")
def start_exam_attempt(exam_id):
    exam = exam_service.get_exam_by_id(exam_id)
    if not exam:
        flash("الاختبار غير موجود.", "error")
        return redirect(url_for("student.exams"))

    user_id = session.get("user_id")
    if not exam_service.is_student_eligible_for_exam(exam, user_id):
        flash("هذا الاختبار مخصص لطلاب محددين فقط وغير متاح لحسابك.", "error")
        return redirect(url_for("student.exams"))

    can_take, state_code, state_msg = exam_service.is_exam_available_now(exam)
    if not can_take:
        flash(state_msg, "error")
        return redirect(url_for("student.exam_detail", exam_id=exam_id))

    try:
        exam_service.start_exam_attempt(exam_id, user_id)
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("student.exam_detail", exam_id=exam_id))


@student_bp.route("/exams/<int:exam_id>/submit", methods=["POST"])
@role_required("student")
def submit_exam(exam_id):
    try:
        user_id = session.get("user_id")
        exam = exam_service.get_exam_by_id(exam_id)
        if not exam:
            flash("الاختبار غير موجود.", "error")
            return redirect(url_for("student.exams"))

        if not exam_service.is_student_eligible_for_exam(exam, user_id):
            flash("هذا الاختبار غير مخصص لك.", "error")
            return redirect(url_for("student.exams"))

        attempt = exam_service.get_student_attempt(exam_id, user_id)
        if not attempt:
            # If attempt not explicitly started yet, start it automatically so answers are preserved
            attempt = exam_service.start_exam_attempt(exam_id, user_id)
        elif attempt.get("status") in ("submitted", "graded", "pending_essay_grading"):
            flash("تم تسليم هذا الاختبار مسبقاً وهو مقفل ولا يُسمح سوى بمحاولة واحدة فقط.", "info")
            return redirect(url_for("student.review_exam_attempt", exam_id=exam_id))
        elif attempt.get("status") == "expired":
            flash("انتهى وقت الاختبار المحدد مسبقاً ولا يمكن تسليم إجابات جديدة.", "error")
            return redirect(url_for("student.exam_detail", exam_id=exam_id))

        attempt = exam_service.submit_exam(exam_id, user_id, request.form.to_dict())
        flash("تم إرسال وحفظ إجابات الاختبار بنجاح!", "success")
        return render_template(
            "student/assessment-result.html",
            user_role="student",
            page_id="exams",
            assessment=exam_service.get_exam_by_id(exam_id),
            attempt=attempt,
        )
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("student.exam_detail", exam_id=exam_id))
    except Exception as error:
        flash(f"حدث خطأ أثناء حفظ إجابات الاختبار: {str(error)}", "error")
        return redirect(url_for("student.exam_detail", exam_id=exam_id))


@student_bp.route("/exams/<int:exam_id>/review")
@role_required("student")
def review_exam_attempt(exam_id):
    user_id = session.get("user_id")
    review_data = exam_service.get_student_exam_review(exam_id, user_id)
    if not review_data:
        flash("لا توجد محاولة مكتملة لهذا الاختبار لمراجعتها حتى الآن.", "info")
        return redirect(url_for("student.exam_detail", exam_id=exam_id))

    return render_template(
        "student/exam-review.html",
        user_role="student",
        page_id="exams",
        review=review_data,
        exam=review_data["exam"],
        attempt=review_data["attempt"],
    )



@student_bp.route("/results")
@role_required("student")
def results():
    user_id = session.get("user_id")
    results_list = result_service.get_student_results_by_user_id(user_id)
    summary = result_service.get_student_results_summary(results_list)
    return render_template(
        "student/results.html",
        user_role="student",
        page_id="results",
        results=results_list,
        summary=summary,
    )



@student_bp.route("/files")
@role_required("student")
def files():
    folder_id = request.args.get("folder_id", type=int)
    current_folder = None
    if folder_id:
        current_folder = file_service.get_folder_by_id(folder_id)
        if not current_folder:
            flash("المجلد المطلوب غير موجود.", "error")
            return redirect(url_for("student.files"))
        files_list = file_service.get_files_by_folder(folder_id)
    else:
        files_list = file_service.get_root_files()

    return render_template(
        "student/files.html",
        user_role="student",
        page_id="files",
        files=files_list,
        current_folder=current_folder,
    )


@student_bp.route("/notifications")
@role_required("student")
def notifications():
    user_id = session.get("user_id") or _get_student_id()
    notifications_list = notification_service.get_student_notifications(user_id=user_id)
    return render_template(
        "student/notifications.html",
        user_role="student",
        page_id="notifications",
        notifications=notifications_list,
    )


@student_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@role_required("student")
def mark_notification_read(notif_id):
    user_id = session.get("user_id") or _get_student_id()
    notification_service.mark_notification_read(notif_id, user_id)
    return redirect(request.referrer or url_for("student.notifications"))


@student_bp.route("/notifications/read-all", methods=["POST"])
@role_required("student")
def mark_all_notifications_read():
    user_id = session.get("user_id") or _get_student_id()
    notification_service.mark_all_read(user_id)
    return redirect(request.referrer or url_for("student.notifications"))





@student_bp.route("/profile")
@role_required("student")
def profile():
    student_id = _get_student_id()
    student = student_service.get_student_by_id(student_id)
    # Enrich with real live stats from DB
    db_stats = student_service.get_student_dashboard_stats(student_id)
    if db_stats:
        student = dict(student) if student else {}
        student.update({
            "completed_lessons": db_stats["completed_lessons"],
            "total_lessons": db_stats["total_lessons"],
            "completed_homework": db_stats["completed_homework"],
            "total_homework": db_stats["total_homework"],
            "overall_grade": db_stats["overall_grade"],
            "graded_exams_count": db_stats.get("graded_exams_count", 0),
            "highest_exam_score": db_stats.get("highest_exam_score", 0.0),
            "passed_exams_count": db_stats.get("passed_exams_count", 0),
        })
    return render_template(
        "student/profile.html",
        user_role="student",
        page_id="profile",
        student=student,
    )
