"""
Admin & Teacher Portal Blueprint
All endpoints are strictly protected under role_required('admin').
Routes remain thin and delegate business logic to the service layer.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
import json
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

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
@admin_bp.route("/")
@role_required("admin")
def root():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    summary = student_service.get_students_summary()
    students = student_service.get_all_students()[:4]
    return render_template(
        "admin/dashboard.html",
        user_role="admin",
        page_id="dashboard",
        summary=summary,
        students=students,
    )


@admin_bp.route("/students")
@role_required("admin")
def students():
    q = request.args.get("q")
    status = request.args.get("status")
    summary = student_service.get_students_summary()
    students_list = student_service.get_all_students(query=q, status_filter=status)
    return render_template(
        "admin/students.html",
        user_role="admin",
        page_id="students",
        summary=summary,
        students=students_list,
    )


@admin_bp.route("/students/<student_id>")
@role_required("admin")
def student_detail(student_id):
    student = student_service.get_student_by_id(student_id)
    return render_template(
        "admin/student-profile.html",
        user_role="admin",
        page_id="students",
        student=student,
    )


@admin_bp.route("/lessons")
@role_required("admin")
def lessons():
    q = request.args.get("q")
    track = request.args.get("track")
    summary = lesson_service.get_lessons_summary()
    lessons_list = lesson_service.get_all_lessons(query=q, track=track)
    return render_template(
        "admin/lessons.html",
        user_role="admin",
        page_id="lessons",
        summary=summary,
        lessons=lessons_list,
        homework_options=homework_service.get_all_homework(),
    )


@admin_bp.route("/homework")
@role_required("admin")
def homework():
    summary = homework_service.get_homework_summary()
    homework_list = homework_service.get_all_homework()
    # Attach submissions to each homework for the review drawer
    hw_id_filter = request.args.get("hw_id")
    submissions = homework_service.get_homework_submissions(
        homework_id=int(hw_id_filter) if hw_id_filter else None
    )
    return render_template(
        "admin/homework.html",
        user_role="admin",
        page_id="homework",
        summary=summary,
        homework=homework_list,
        submissions=submissions,
        selected_hw_id=int(hw_id_filter) if hw_id_filter else None,
    )


@admin_bp.route("/homework/grade", methods=["POST"])
@role_required("admin")
def grade_submission():
    """Admin endpoint to grade a homework submission."""
    submission_id = request.form.get("submission_id")
    grade = request.form.get("grade")
    feedback = request.form.get("feedback")

    if not submission_id or grade is None:
        flash("يرجى إدخال رقم التسليم والدرجة.", "error")
        return redirect(url_for("admin.homework"))

    try:
        homework_service.grade_submission(
            submission_id=int(submission_id),
            grade=grade,
            feedback=feedback,
        )
        flash("تم رصد الدرجة بنجاح.", "success")
    except ValueError as ve:
        flash(str(ve), "error")
    except Exception as e:
        flash("حدث خطأ أثناء رصد الدرجة. يرجى المحاولة لاحقاً.", "error")

    return redirect(url_for("admin.homework"))


@admin_bp.route("/exams")
@role_required("admin")
def exams():
    summary = exam_service.get_exams_summary()
    exams_list = exam_service.get_all_exams()
    return render_template(
        "admin/exams.html",
        user_role="admin",
        page_id="exams",
        summary=summary,
        exams=exams_list,
    )


@admin_bp.route("/exams/<int:exam_id>/builder", methods=["GET", "POST"])
@role_required("admin")
def exam_builder(exam_id):
    """Single editor for mixed MCQ/true-false questions; only admins reach it."""
    if request.method == "POST":
        try:
            questions = json.loads(request.form.get("questions_json", "[]"))
            exam_service.save_exam_questions(exam_id, questions)
            exam_service.update_exam(exam_id, {
                "title": request.form.get("title"),
                "duration_minutes": request.form.get("duration_minutes"),
                "total_questions": len(questions),
                "scheduled_date": request.form.get("scheduled_date"),
                "status": request.form.get("status", "scheduled"),
            })
            flash("تم حفظ تفاصيل الاختبار وأسئلته كمسودة.", "success")
            return redirect(url_for("admin.exam_builder", exam_id=exam_id))
        except (ValueError, json.JSONDecodeError) as error:
            flash(str(error) or "تعذر حفظ الأسئلة.", "error")
    return render_template("admin/assessment-builder.html", user_role="admin", page_id="exams",
                           assessment=exam_service.get_exam_by_id(exam_id), assessment_type="exam", assessment_label="الاختبار",
                           review_url=url_for("admin.review_exam", exam_id=exam_id),
                           preview_url=url_for("admin.preview_exam", exam_id=exam_id),
                           question_bank=exam_service.get_question_bank())


@admin_bp.route("/exams/<int:exam_id>/review")
@role_required("admin")
def review_exam(exam_id):
    return render_template("admin/assessment-review.html", user_role="admin", page_id="exams", assessment_label="الاختبار",
                           assessment=exam_service.get_exam_by_id(exam_id), assessment_type="exam", builder_url=url_for("admin.exam_builder", exam_id=exam_id), preview_url=url_for("admin.preview_exam", exam_id=exam_id), publish_url=url_for("admin.publish_exam", exam_id=exam_id))


@admin_bp.route("/exams/<int:exam_id>/preview")
@role_required("admin")
def preview_exam(exam_id):
    """Show the exam exactly as a student sees it without creating an attempt."""
    exam = exam_service.get_exam_by_id(exam_id)
    return render_template(
        "admin/assessment-preview.html",
        user_role="admin",
        page_id="exams",
        assessment=exam,
        assessment_label="الاختبار",
        builder_url=url_for("admin.exam_builder", exam_id=exam_id),
    )


@admin_bp.route("/homework/<int:hw_id>/builder", methods=["GET", "POST"])
@role_required("admin")
def homework_builder(hw_id):
    if request.method == "POST":
        try:
            homework_service.save_homework_questions(hw_id, json.loads(request.form.get("questions_json", "[]")))
            flash("تم حفظ أسئلة الواجب كمسودة.", "success")
            return redirect(url_for("admin.homework_builder", hw_id=hw_id))
        except (ValueError, json.JSONDecodeError) as error:
            flash(str(error) or "تعذر حفظ الأسئلة.", "error")
    return render_template("admin/assessment-builder.html", user_role="admin", page_id="homework", assessment=homework_service.get_homework_by_id(hw_id), assessment_type="homework", assessment_label="الواجب", review_url=url_for("admin.review_homework", hw_id=hw_id), question_bank=exam_service.get_question_bank())


@admin_bp.route("/homework/<int:hw_id>/review")
@role_required("admin")
def review_homework(hw_id):
    return render_template("admin/assessment-review.html", user_role="admin", page_id="homework", assessment=homework_service.get_homework_by_id(hw_id), assessment_label="الواجب", builder_url=url_for("admin.homework_builder", hw_id=hw_id), publish_url=url_for("admin.publish_homework", hw_id=hw_id))


@admin_bp.route("/homework/<int:hw_id>/publish", methods=["POST"])
@role_required("admin")
def publish_homework(hw_id):
    try:
        homework_service.publish_homework(hw_id)
        flash("تم نشر الواجب للطلاب.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("admin.homework"))


@admin_bp.route("/exams/<int:exam_id>/publish", methods=["POST"])
@role_required("admin")
def publish_exam(exam_id):
    try:
        exam_service.publish_exam(exam_id)
        flash("تم نشر الاختبار، وأصبح متاحاً للطلاب.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("admin.exams"))


@admin_bp.route("/questions")
@role_required("admin")
def questions():
    questions_list = exam_service.get_question_bank()
    return render_template(
        "admin/questions.html",
        user_role="admin",
        page_id="questions",
        questions=questions_list,
    )


@admin_bp.route("/results")
@role_required("admin")
def results():
    summary = result_service.get_results_summary()
    results_list = result_service.get_all_results()
    return render_template(
        "admin/results.html",
        user_role="admin",
        page_id="results",
        summary=summary,
        results=results_list,
    )


@admin_bp.route("/files")
@role_required("admin")
def files():
    summary = file_service.get_files_summary()
    files_list = file_service.get_all_files()
    return render_template(
        "admin/files.html",
        user_role="admin",
        page_id="files",
        summary=summary,
        files=files_list,
    )


@admin_bp.route("/notifications")
@role_required("admin")
def notifications():
    notifications_list = notification_service.get_all_notifications()
    return render_template(
        "admin/notifications.html",
        user_role="admin",
        page_id="notifications",
        notifications=notifications_list,
    )


@admin_bp.route("/settings")
@role_required("admin")
def settings():
    return render_template(
        "admin/settings.html",
        user_role="admin",
        page_id="settings",
    )


# ------------------------------------------------------------------------------
# Students CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/students/create", methods=["POST"])
@role_required("admin")
def create_student():
    name = request.form.get("name")
    email = request.form.get("email")
    track = request.form.get("track")
    level = request.form.get("level")

    if not name or not email:
        flash("يرجى ملء الاسم والبريد الإلكتروني لطالب جديد.", "error")
        return redirect(url_for("admin.students"))

    try:
        student_service.create_student(name=name, email=email, track=track, level=level)
        flash("تمت إضافة الطالب بنجاح إلى النظام الأكاديمي.", "success")
    except Exception as e:
        flash(f"فشل إضافة الطالب: {e}", "error")

    return redirect(url_for("admin.students"))


@admin_bp.route("/students/<student_id>/edit", methods=["POST"])
@role_required("admin")
def edit_student(student_id):
    try:
        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "track": request.form.get("track"),
            "level": request.form.get("level"),
            "status": request.form.get("status"),
        }
        student_service.update_student(student_id, data)
        flash("تم تحديث بيانات الطالب بنجاح.", "success")
    except Exception as e:
        flash(f"فشل تحديث بيانات الطالب: {e}", "error")

    return redirect(request.referrer or url_for("admin.students"))


@admin_bp.route("/students/<student_id>/delete", methods=["POST"])
@role_required("admin")
def delete_student(student_id):
    try:
        student_service.delete_student(student_id)
        flash("تم حذف الطالب وسجلاته الأكاديمية بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف الطالب: {e}", "error")

    return redirect(url_for("admin.students"))


# ------------------------------------------------------------------------------
# Questions CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/questions/create", methods=["POST"])
@role_required("admin")
def create_question():
    prompt = request.form.get("prompt")
    if not prompt:
        flash("نص السؤال الأكاديمي مطلوب.", "error")
        return redirect(url_for("admin.questions"))

    try:
        data = {
            "prompt": prompt,
            "category": request.form.get("category", "mcq"),
            "difficulty": request.form.get("difficulty", "متوسط"),
            "track": request.form.get("track", "الخوارزميات"),
            "correct_answer": request.form.get("correct_answer", ""),
            "answer_preview": request.form.get("correct_answer", ""),
            "options": request.form.get("options", ""),
        }
        exam_service.create_question(data)
        flash("تمت إضافة السؤال لبنك الأسئلة المركزي بنجاح.", "success")
    except Exception as e:
        flash(f"فشل إضافة السؤال: {e}", "error")

    return redirect(url_for("admin.questions"))


@admin_bp.route("/questions/<int:question_id>/edit", methods=["POST"])
@role_required("admin")
def edit_question(question_id):
    try:
        data = {
            "prompt": request.form.get("prompt"),
            "category": request.form.get("category"),
            "difficulty": request.form.get("difficulty"),
            "track": request.form.get("track"),
            "correct_answer": request.form.get("correct_answer"),
            "answer_preview": request.form.get("correct_answer"),
        }
        exam_service.update_question(question_id, data)
        flash("تم تعديل السؤال بنجاح.", "success")
    except Exception as e:
        flash(f"فشل تعديل السؤال: {e}", "error")

    return redirect(url_for("admin.questions"))


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@role_required("admin")
def delete_question(question_id):
    try:
        exam_service.delete_question(question_id)
        flash("تم حذف السؤال من بنك الأسئلة بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف السؤال: {e}", "error")

    return redirect(url_for("admin.questions"))


# ------------------------------------------------------------------------------
# Lessons CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/lessons/create", methods=["POST"])
@role_required("admin")
def create_lesson():
    title = request.form.get("title")
    if not title:
        flash("عنوان الحصة مطلوب.", "error")
        return redirect(url_for("admin.lessons"))

    try:
        data = {
            "title": title,
            "code": request.form.get("code"),
            "track": request.form.get("track"),
            "duration_minutes": request.form.get("duration_minutes", 60),
            "lesson_date": request.form.get("lesson_date"), "image_url": request.form.get("image_url"),
            "material_url": request.form.get("material_url"), "homework_id": request.form.get("homework_id"),
        }
        lesson_service.create_lesson(data)
        flash("تم إنشاء الحصة وجدولتها بنجاح.", "success")
    except Exception as e:
        flash(f"فشل إنشاء الحصة: {e}", "error")

    return redirect(url_for("admin.lessons"))


@admin_bp.route("/lessons/<int:lesson_id>/edit", methods=["POST"])
@role_required("admin")
def edit_lesson(lesson_id):
    try:
        data = {
            "title": request.form.get("title"),
            "code": request.form.get("code"),
            "track": request.form.get("track"),
            "duration_minutes": request.form.get("duration_minutes"),
            "lesson_date": request.form.get("lesson_date"), "image_url": request.form.get("image_url"),
            "material_url": request.form.get("material_url"), "homework_id": request.form.get("homework_id"),
        }
        lesson_service.update_lesson(lesson_id, data)
        flash("تم تحديث بيانات الحصة بنجاح.", "success")
    except Exception as e:
        flash(f"فشل تحديث الحصة: {e}", "error")

    return redirect(url_for("admin.lessons"))


@admin_bp.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
@role_required("admin")
def delete_lesson(lesson_id):
    try:
        lesson_service.delete_lesson(lesson_id)
        flash("تم حذف الحصة بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف الحصة: {e}", "error")

    return redirect(url_for("admin.lessons"))


# ------------------------------------------------------------------------------
# Homework CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/homework/create", methods=["POST"])
@role_required("admin")
def create_homework():
    title = request.form.get("title")
    if not title:
        flash("عنوان التكليف مطلوب.", "error")
        return redirect(url_for("admin.homework"))

    try:
        data = {
            "title": title,
            "code": request.form.get("code"),
            "track": request.form.get("track"),
            "due_date": request.form.get("due_date"),
            "instructions": request.form.get("instructions"),
            "max_grade": request.form.get("max_grade", 40),
        }
        homework = homework_service.create_homework(data)
        flash("تم إنشاء مسودة الواجب. أضف الأسئلة ثم راجعه قبل النشر.", "success")
        return redirect(url_for("admin.homework_builder", hw_id=homework["id"]))
    except Exception as e:
        flash(f"فشل إنشاء التكليف: {e}", "error")

    return redirect(url_for("admin.homework"))


@admin_bp.route("/homework/<int:hw_id>/edit", methods=["POST"])
@role_required("admin")
def edit_homework(hw_id):
    try:
        data = {
            "title": request.form.get("title"),
            "code": request.form.get("code"),
            "track": request.form.get("track"),
            "due_date": request.form.get("due_date"),
            "instructions": request.form.get("instructions"),
            "status": request.form.get("status"),
        }
        homework_service.update_homework(hw_id, data)
        flash("تم تعديل التكليف بنجاح.", "success")
    except Exception as e:
        flash(f"فشل تعديل التكليف: {e}", "error")

    return redirect(url_for("admin.homework"))


@admin_bp.route("/homework/<int:hw_id>/delete", methods=["POST"])
@role_required("admin")
def delete_homework(hw_id):
    try:
        homework_service.delete_homework(hw_id)
        flash("تم حذف التكليف البرمجي وجميع تسليماته بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف التكليف: {e}", "error")

    return redirect(url_for("admin.homework"))


@admin_bp.route("/homework/submissions/<int:submission_id>/delete", methods=["POST"])
@role_required("admin")
def delete_submission(submission_id):
    try:
        homework_service.delete_submission(submission_id)
        flash("تم حذف تسليم الطالب بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف التسليم: {e}", "error")

    return redirect(url_for("admin.homework"))


# ------------------------------------------------------------------------------
# Exams CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/exams/create", methods=["POST"])
@role_required("admin")
def create_exam():
    title = request.form.get("title")
    if not title:
        flash("عنوان الاختبار مطلوب.", "error")
        return redirect(url_for("admin.exams"))

    try:
        data = {
            "title": title,
            "duration_minutes": request.form.get("duration_minutes", 90),
            "total_questions": request.form.get("total_questions", 10),
            "scheduled_date": request.form.get("scheduled_date"),
            "status": request.form.get("status", "scheduled"),
        }
        exam = exam_service.create_exam(data)
        flash("تم إنشاء مسودة الاختبار. أضف الأسئلة ثم راجعها قبل النشر.", "success")
        return redirect(url_for("admin.exam_builder", exam_id=exam["id"]))
    except Exception as e:
        flash(f"فشل إنشاء الاختبار: {e}", "error")

    return redirect(url_for("admin.exams"))


@admin_bp.route("/exams/<int:exam_id>/edit", methods=["POST"])
@role_required("admin")
def edit_exam(exam_id):
    try:
        data = {
            "title": request.form.get("title"),
            "duration_minutes": request.form.get("duration_minutes"),
            "total_questions": request.form.get("total_questions"),
            "scheduled_date": request.form.get("scheduled_date"),
            "status": request.form.get("status"),
        }
        exam_service.update_exam(exam_id, data)
        flash("تم تحديث بيانات الاختبار بنجاح.", "success")
    except Exception as e:
        flash(f"فشل تحديث الاختبار: {e}", "error")

    return redirect(url_for("admin.exams"))


@admin_bp.route("/exams/<int:exam_id>/delete", methods=["POST"])
@role_required("admin")
def delete_exam(exam_id):
    try:
        exam_service.delete_exam(exam_id)
        flash("تم حذف الاختبار بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف الاختبار: {e}", "error")

    return redirect(url_for("admin.exams"))


# ------------------------------------------------------------------------------
# Results CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/results/<int:result_id>/delete", methods=["POST"])
@role_required("admin")
def delete_result(result_id):
    try:
        result_service.delete_result(result_id)
        flash("تم حذف سجل النتيجة بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف النتيجة: {e}", "error")

    return redirect(url_for("admin.results"))


# ------------------------------------------------------------------------------
# Files CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/files/create", methods=["POST"])
@role_required("admin")
def create_file():
    name = request.form.get("name")
    if not name:
        flash("اسم الملف مطلوب.", "error")
        return redirect(url_for("admin.files"))

    try:
        data = {
            "name": name,
            "file_name": request.form.get("file_name", name),
            "category": request.form.get("category", "pdf"),
            "size_display": request.form.get("size_display", "2.4 MB"),
            "description": request.form.get("description", ""),
            "file_url": request.form.get("file_url", "#"),
        }
        file_service.create_file(data)
        flash("تم رفع الملف وإضافته للمستودع السحابي بنجاح.", "success")
    except Exception as e:
        flash(f"فشل إضافة الملف: {e}", "error")

    return redirect(url_for("admin.files"))


@admin_bp.route("/files/<int:file_id>/delete", methods=["POST"])
@role_required("admin")
def delete_file(file_id):
    try:
        file_service.delete_file(file_id)
        flash("تم حذف الملف من المستودع السحابي بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف الملف: {e}", "error")

    return redirect(url_for("admin.files"))


# ------------------------------------------------------------------------------
# Notifications CRUD Operations
# ------------------------------------------------------------------------------
@admin_bp.route("/notifications/create", methods=["POST"])
@role_required("admin")
def create_notification():
    title = request.form.get("title")
    content = request.form.get("content")

    if not title or not content:
        flash("عنوان ونص التعميم مطلوبان.", "error")
        return redirect(url_for("admin.notifications"))

    try:
        data = {
            "title": title,
            "content": content,
            "type": request.form.get("type", "announcement"),
        }
        notification_service.create_notification(data)
        flash("تم إرسال ونشر التعميم الأكاديمي بنجاح.", "success")
    except Exception as e:
        flash(f"فشل إرسال التعميم: {e}", "error")

    return redirect(url_for("admin.notifications"))


@admin_bp.route("/notifications/<int:notification_id>/delete", methods=["POST"])
@role_required("admin")
def delete_notification(notification_id):
    try:
        notification_service.delete_notification(notification_id)
        flash("تم حذف الإشعار بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف الإشعار: {e}", "error")

    return redirect(url_for("admin.notifications"))
