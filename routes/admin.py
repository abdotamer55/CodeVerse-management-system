"""
Admin & Teacher Portal Blueprint
All endpoints are strictly protected under role_required('admin').
Routes remain thin and delegate business logic to the service layer.
"""
import os
import time
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
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


def _save_uploaded_file(file_storage, subfolder="uploads"):
    """Save a file uploaded via request.files and return (relative_url, size_display, filename, category)."""
    if not file_storage or not getattr(file_storage, "filename", None):
        return None, None, None, None
    orig_name = file_storage.filename.strip()
    if not orig_name:
        return None, None, None, None

    ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else ""
    # Validate extension — reject dangerous or unknown extensions
    allowed_exts = {"pdf", "zip", "rar", "7z", "tar", "gz", "ppt", "pptx",
                    "mp4", "mov", "avi", "webm", "mkv", "doc", "docx", "txt", "md",
                    "jpg", "jpeg", "jfif", "png", "gif", "webp", "svg"}
    if ext and ext not in allowed_exts:
        ext = "bin"

    timestamp = int(time.time())
    raw_stem = orig_name.rsplit(".", 1)[0] if "." in orig_name else orig_name
    safe_stem = "".join(c for c in raw_stem if c.isalnum() or c in ("-", "_")).strip() or "file"
    # Truncate to 60 chars max — prevents Windows MAX_PATH (260 chars) errors
    safe_stem = safe_stem[:60]
    safe_filename = f"{timestamp}_{safe_stem}.{ext}" if ext else f"{timestamp}_{safe_stem}"

    # Always build the full path from root_path + static + subfolder
    # (ignores UPLOAD_FOLDER which may point to base uploads only)
    upload_folder = os.path.join(current_app.root_path, "static", subfolder)
    os.makedirs(upload_folder, exist_ok=True)
    dest_path = os.path.join(upload_folder, safe_filename)
    file_storage.save(dest_path)

    file_size = os.path.getsize(dest_path)
    if file_size >= 1024 * 1024:
        size_display = f"{file_size / (1024 * 1024):.1f} MB"
    else:
        size_display = f"{max(1, round(file_size / 1024))} KB"

    rel_url = url_for("static", filename=f"{subfolder}/{safe_filename}")

    if ext in ("pdf",):
        category = "pdf"
    elif ext in ("zip", "rar", "7z", "tar", "gz"):
        category = "zip"
    elif ext in ("ppt", "pptx"):
        category = "slides"
    elif ext in ("mp4", "mov", "avi", "webm", "mkv"):
        category = "video"
    elif ext in ("doc", "docx", "txt", "md"):
        category = "doc"
    elif ext in ("jpg", "jpeg", "jfif", "png", "gif", "webp", "svg"):
        category = "image"
    else:
        category = "pdf"

    return rel_url, size_display, orig_name, category


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
    lesson_summary = lesson_service.get_lessons_summary()
    results_summary = result_service.get_results_summary()
    return render_template(
        "admin/dashboard.html",
        user_role="admin",
        page_id="dashboard",
        summary=summary,
        students=students,
        lesson_summary=lesson_summary,
        results_summary=results_summary,
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


@admin_bp.route("/lessons/<int:lesson_id>/preview")
@role_required("admin")
def preview_lesson(lesson_id):
    lesson = lesson_service.get_lesson_by_id(lesson_id)
    if not lesson:
        flash("الحصة غير موجودة.", "error")
        return redirect(url_for("admin.lessons"))
    return render_template(
        "student/lesson.html",
        user_role="admin",
        page_id="lessons",
        lesson=lesson,
        back_url=url_for("admin.lessons"),
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
        updated_sub = homework_service.grade_submission(
            submission_id=int(submission_id),
            grade=grade,
            feedback=feedback,
        )
        if updated_sub:
            try:
                # Record into results table
                clean_grade_str = str(grade).strip()
                pct = 95.0
                if "/" in clean_grade_str:
                    parts = clean_grade_str.split("/")
                    try:
                        pct = round((float(parts[0].strip()) / float(parts[1].strip())) * 100, 1)
                    except Exception:
                        pass
                elif "%" in clean_grade_str:
                    try:
                        pct = float(clean_grade_str.replace("%", "").strip())
                    except Exception:
                        pass
                grade_badge = "badge-success" if pct >= 70 else "badge-danger"
                grade_label = "ممتاز" if pct >= 90 else ("جيد جداً" if pct >= 80 else ("جيد" if pct >= 70 else "فرصة إعادة"))

                hw_title = "تكليف برمجي"
                hw_row = homework_service.get_homework_by_id(updated_sub["homework_id"])
                if hw_row:
                    hw_title = hw_row["title"]

                execute_query("""
                    INSERT INTO results (student_id, student_name, student_code, assessment, score_percent, score_display, date, status, grade_badge, grade_label)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE::text, 'passed', %s, %s);
                """, (
                    updated_sub["student_id"], updated_sub["student_name"], updated_sub["student_code"],
                    hw_title, pct, clean_grade_str, grade_badge, grade_label
                ), fetch=False, commit=True)

                notification_service.create_notification({
                    "user_id": updated_sub["student_id"],
                    "title": f"تم رصد نتيجة تكليفك البرمجي: {hw_title}",
                    "content": f"تم اعتماد درجتك: {clean_grade_str}. " + (f"ملاحظات: {feedback}" if feedback else ""),
                    "type": "assignment",
                })
            except Exception as ne:
                logger.warning(f"Could not record homework in results/notifications: {ne}")

        flash("تم رصد الدرجة بنجاح وتسجيلها في السجل الأكاديمي وإشعار الطالب.", "success")
    except ValueError as ve:
        flash(str(ve), "error")
    except Exception as e:
        flash(f"حدث خطأ أثناء رصد الدرجة: {e}", "error")

    return redirect(request.referrer or url_for("admin.homework"))


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
    if not exam:
        flash(f"الاختبار رقم {exam_id} غير متوفر للمعاينة.", "error")
        return redirect(url_for("admin.exams"))
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
    pending_essays = result_service.get_pending_essay_attempts()
    pending_homework = homework_service.get_homework_submissions()
    return render_template(
        "admin/results.html",
        user_role="admin",
        page_id="results",
        summary=summary,
        results=results_list,
        pending_essays=pending_essays,
        pending_homework=pending_homework,
    )


@admin_bp.route("/results/grade-essay", methods=["POST"])
@role_required("admin")
def grade_essay():
    attempt_id = request.form.get("attempt_id")
    answer_id = request.form.get("answer_id")
    marks = request.form.get("marks")
    feedback = request.form.get("feedback")

    if not attempt_id or not answer_id or marks is None:
        flash("يرجى إدخال بيانات التصحيح والدرجة بشكل صحيح.", "error")
        return redirect(url_for("admin.results"))

    try:
        result_service.grade_essay_attempt(
            attempt_id=int(attempt_id),
            answer_id=int(answer_id),
            marks_awarded=float(marks),
            feedback=feedback,
        )
        flash("تم رصد درجة السؤال المقالي واعتماد النتيجة الإجمالية وإشعار الطالب بنجاح.", "success")
    except Exception as e:
        flash(f"فشل رصد درجة السؤال المقالي: {e}", "error")

    return redirect(url_for("admin.results"))


@admin_bp.route("/files")
@role_required("admin")
def files():
    folder_id = request.args.get("folder_id", type=int)
    summary = file_service.get_files_summary()
    all_folders = file_service.get_all_folders()

    current_folder = None
    available_files = []
    if folder_id:
        current_folder = file_service.get_folder_by_id(folder_id)
        if not current_folder:
            flash("المجلد المطلوب غير موجود أو تم حذفه.", "error")
            return redirect(url_for("admin.files"))
        files_list = file_service.get_files_by_folder(folder_id)
        available_files = file_service.get_available_files_for_folder(folder_id)
    else:
        files_list = file_service.get_root_files()

    return render_template(
        "admin/files.html",
        user_role="admin",
        page_id="files",
        summary=summary,
        files=files_list,
        current_folder=current_folder,
        all_folders=all_folders,
        available_files=available_files,
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


@admin_bp.route("/settings", methods=["GET", "POST"])
@role_required("admin")
def settings():
    if request.method == "POST":
        try:
            from services import auth_service
            user_id = session.get("user_id")

            full_name = request.form.get("full_name")
            username = request.form.get("username")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if password:
                if confirm_password and password != confirm_password:
                    flash("كلمة المرور الجديدة وتأكيد كلمة المرور غير متطابقين.", "error")
                    return redirect(url_for("admin.settings"))
                elif not confirm_password:
                    flash("يرجى كتابة تأكيد كلمة المرور الجديدة للتأكد من صحتها.", "error")
                    return redirect(url_for("admin.settings"))

            updated = auth_service.update_user_credentials(
                user_id=user_id,
                username=username if username else None,
                password=password if password else None,
                full_name=full_name if full_name else None,
            )

            if updated.get("full_name"):
                session["user_name"] = updated["full_name"]
            if updated.get("username"):
                session["username"] = updated["username"]

            if password:
                flash("تم تحديث بيانات المسؤول، اسم المستخدم، وكلمة المرور الجديدة بنجاح.", "success")
            else:
                flash("تم تحديث اسم المستخدم وبيانات حساب المسؤول بنجاح.", "success")
        except ValueError as error:
            flash(str(error), "error")
        except Exception as error:
            flash(f"حدث خطأ أثناء حفظ التعديلات: {str(error)}", "error")
        return redirect(url_for("admin.settings"))
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
    username = request.form.get("username")
    password = request.form.get("password")
    track = request.form.get("track")
    level = request.form.get("level")

    if not name or not email:
        flash("يرجى ملء الاسم والبريد الإلكتروني لطالب جديد.", "error")
        return redirect(url_for("admin.students"))

    try:
        new_st = student_service.create_student(
            name=name,
            email=email,
            track=track,
            level=level,
            username=username,
            password=password,
        )
        st_user = (new_st.get("username") if isinstance(new_st, dict) else None) or username or email.split("@")[0]
        st_pass = (new_st.get("plain_password") if isinstance(new_st, dict) else None) or password or "student123"
        flash(
            f"تمت إضافة الطالب <strong>{name}</strong> بنجاح! "
            f"<span style='display:inline-block;background:rgba(255,255,255,0.15);padding:3px 8px;border-radius:4px;margin:0 4px;'>اسم المستخدم: <code class='ltr' style='font-weight:700'>{st_user}</code></span> "
            f"<span style='display:inline-block;background:rgba(255,255,255,0.15);padding:3px 8px;border-radius:4px;margin:0 4px;'>كلمة المرور: <code class='ltr' style='font-weight:700'>{st_pass}</code></span>",
            "success"
        )
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
            "username": request.form.get("username"),
            "password": request.form.get("password"),
            "track": request.form.get("track"),
            "level": request.form.get("level"),
            "status": request.form.get("status"),
        }
        student_service.update_student(student_id, data)
        flash("تم تحديث بيانات وحساب الطالب بنجاح.", "success")
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
def _extract_question_form_data(form):
    category = form.get("category", "mcq")
    prompt = (form.get("prompt") or "").strip()
    difficulty = form.get("difficulty", "متوسط")
    track = form.get("track", "الخوارزميات")
    points = int(form.get("points") or 1)

    if category == "mcq":
        raw_opts = [
            form.get("mcq_opt_0", "").strip(),
            form.get("mcq_opt_1", "").strip(),
            form.get("mcq_opt_2", "").strip(),
            form.get("mcq_opt_3", "").strip(),
        ]
        opts = [o for o in raw_opts if o]
        if not opts:
            opts = [o.strip() for o in (form.get("options") or "").splitlines() if o.strip()]
        try:
            correct_index = int(form.get("mcq_correct", form.get("correct_index", 0)))
        except Exception:
            correct_index = 0
        correct_answer = opts[correct_index] if 0 <= correct_index < len(opts) else ""
        answer_preview = correct_answer
    elif category == "boolean":
        opts = ["صح", "خطأ"]
        try:
            correct_index = int(form.get("bool_correct", form.get("correct_index", 0)))
        except Exception:
            correct_index = 0
        correct_answer = opts[correct_index] if 0 <= correct_index < len(opts) else "صح"
        answer_preview = correct_answer
    elif category == "essay":
        opts = []
        correct_index = None
        correct_answer = form.get("essay_model_answer") or form.get("correct_answer") or ""
        answer_preview = correct_answer or "إجابة مقالية (تصحيح يدوي)"
    elif category == "code":
        opts = []
        correct_index = None
        correct_answer = form.get("code_solution") or form.get("correct_answer") or ""
        answer_preview = correct_answer or "مسألة برمجية"
    else:
        opts = []
        correct_index = None
        correct_answer = form.get("correct_answer", "")
        answer_preview = correct_answer

    return {
        "prompt": prompt,
        "category": category,
        "difficulty": difficulty,
        "track": track,
        "options": opts,
        "correct_index": correct_index,
        "correct_answer": correct_answer,
        "answer_preview": answer_preview,
        "points": points,
    }


@admin_bp.route("/questions/create", methods=["POST"])
@role_required("admin")
def create_question():
    prompt = request.form.get("prompt")
    if not prompt:
        flash("نص السؤال الأكاديمي مطلوب.", "error")
        return redirect(url_for("admin.questions"))

    try:
        data = _extract_question_form_data(request.form)
        exam_service.create_question(data)
        flash("تمت إضافة السؤال لبنك الأسئلة المركزي بنجاح.", "success")
    except Exception as e:
        flash(f"فشل إضافة السؤال: {e}", "error")

    return redirect(url_for("admin.questions"))


@admin_bp.route("/questions/<int:question_id>/edit", methods=["POST"])
@role_required("admin")
def edit_question(question_id):
    try:
        data = _extract_question_form_data(request.form)
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
        material_url = request.form.get("material_url", "").strip()
        # Handle direct file upload from device
        uploaded_mat = request.files.get("material_file")
        if uploaded_mat and uploaded_mat.filename:
            f_url, f_size, f_orig, _ = _save_uploaded_file(uploaded_mat)
            if f_url:
                material_url = f_url
                try:
                    file_service.create_file({
                        "name": f"مذكرة: {title}",
                        "file_name": f_orig,
                        "category": "pdf",
                        "size_display": f_size,
                        "description": f"مذكرة وحقيبة الشرح المرفقة بحصة: {title}",
                        "file_url": f_url,
                    })
                except Exception:
                    pass

        # Handle image file upload from device
        image_url = request.form.get("image_url", "").strip()
        uploaded_img = request.files.get("image_file")
        if uploaded_img and uploaded_img.filename:
            img_url, _, _, _ = _save_uploaded_file(uploaded_img, subfolder="uploads/images")
            if img_url:
                image_url = img_url

        is_live = request.form.get("is_live") in ("true", "1", "on")
        video_url = request.form.get("video_url", "").strip()
        live_time = request.form.get("live_time", "").strip()
        live_url = request.form.get("live_url", "").strip()

        data = {
            "title": title,
            "code": request.form.get("code"),
            "track": request.form.get("track"),
            "duration_minutes": request.form.get("duration_minutes", 60),
            "lesson_date": request.form.get("lesson_date"),
            "image_url": image_url,
            "material_url": material_url,
            "homework_id": request.form.get("homework_id"),
            "is_live": is_live,
            "video_url": video_url,
            "live_time": live_time,
            "live_url": live_url,
            "instructor": request.form.get("instructor") or "المهندس عبدالرحمن تامر",
            "description": request.form.get("description", ""),
            "topics": request.form.get("topics", ""),
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
        material_url = request.form.get("material_url", "").strip()
        uploaded_mat = request.files.get("material_file")
        if uploaded_mat and uploaded_mat.filename:
            f_url, f_size, f_orig, _ = _save_uploaded_file(uploaded_mat)
            if f_url:
                material_url = f_url
                try:
                    file_service.create_file({
                        "name": f"مذكرة: {request.form.get('title', '')}",
                        "file_name": f_orig,
                        "category": "pdf",
                        "size_display": f_size,
                        "description": f"تحديث لمذكرة الشرح المرفقة بالحصة",
                        "file_url": f_url,
                    })
                except Exception:
                    pass

        # Handle image file upload from device
        image_url = request.form.get("image_url", "").strip()
        uploaded_img = request.files.get("image_file")
        if uploaded_img and uploaded_img.filename:
            img_url, _, _, _ = _save_uploaded_file(uploaded_img, subfolder="uploads/images")
            if img_url:
                image_url = img_url

        is_live = request.form.get("is_live") in ("true", "1", "on") if "is_live" in request.form else None
        video_url = request.form.get("video_url")
        live_time = request.form.get("live_time")
        live_url = request.form.get("live_url")

        data = {
            "title": request.form.get("title"),
            "code": request.form.get("code"),
            "track": request.form.get("track"),
            "duration_minutes": request.form.get("duration_minutes"),
            "lesson_date": request.form.get("lesson_date"),
            "image_url": image_url,
            "material_url": material_url,
            "homework_id": request.form.get("homework_id"),
            "is_live": is_live,
            "video_url": video_url,
            "live_time": live_time,
            "live_url": live_url,
            "instructor": request.form.get("instructor") or "المهندس عبدالرحمن تامر",
            "description": request.form.get("description", ""),
            "topics": request.form.get("topics", ""),
        }
        lesson_service.update_lesson(lesson_id, data)
        flash("تم تحديث بيانات الحصة بنجاح.", "success")
    except Exception as e:
        flash(f"فشل تحديث الحصة: {e}", "error")

    redirect_target = request.form.get("redirect_to") or url_for("admin.lessons")
    return redirect(redirect_target)


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
        if data.get("scheduled_date"):
            try:
                notification_service.create_notification({
                    "title": f"تنبيه أكاديمي: موعد اختبار {title}",
                    "content": f"تمت جدولة موعد الاختبار في {data['scheduled_date']}. يرجى من جميع الطلاب مراجعة بنك الأسئلة والاستعداد.",
                    "type": "exam",
                })
            except Exception as ne:
                logger.warning(f"Could not dispatch exam notification: {ne}")

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
        if data.get("scheduled_date"):
            try:
                notification_service.create_notification({
                    "title": f"تحديث موعد الاختبار: {data.get('title') or 'الاختبار'}",
                    "content": f"تم تحديث موعد الاختبار ليصبح: {data['scheduled_date']}.",
                    "type": "exam",
                })
            except Exception as ne:
                logger.warning(f"Could not dispatch exam notification: {ne}")

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
    uploaded_files = request.files.getlist("files")
    if not uploaded_files or not any(f.filename for f in uploaded_files):
        single = request.files.get("file")
        if single and single.filename:
            uploaded_files = [single]
        else:
            uploaded_files = []

    folder_id = request.form.get("folder_id")
    folder_id = int(folder_id) if folder_id and str(folder_id).isdigit() else None
    custom_name = (request.form.get("name") or "").strip()
    manual_url = (request.form.get("file_url") or "").strip()
    manual_cat = request.form.get("category")
    manual_size = (request.form.get("size_display") or "2.4 MB").strip()
    description = (request.form.get("description") or "").strip()

    # Case 1: Files uploaded directly via file input (supports multiple)
    if uploaded_files:
        success_count = 0
        last_name = ""
        for uf in uploaded_files:
            if not uf or not uf.filename:
                continue
            saved_url, auto_size, orig_fn, auto_cat = _save_uploaded_file(uf)
            if not saved_url:
                continue
            item_name = custom_name if (len(uploaded_files) == 1 and custom_name) else orig_fn.rsplit(".", 1)[0]
            item_cat = manual_cat if (manual_cat and len(uploaded_files) == 1) else auto_cat
            data = {
                "name": item_name,
                "file_name": orig_fn,
                "category": item_cat,
                "size_display": auto_size,
                "description": description,
                "file_url": saved_url,
                "folder_id": folder_id,
            }
            try:
                file_service.create_file(data)
                success_count += 1
                last_name = item_name
            except Exception as e:
                logger.error(f"Error saving uploaded file {orig_fn}: {e}")

        if success_count == 1:
            flash(f"تم رفع وتخزين الملف ({last_name}) بنجاح في المستودع السحابي.", "success")
        elif success_count > 1:
            flash(f"تم رفع وتخزين {success_count} ملفات بنجاح في المستودع السحابي.", "success")
        else:
            flash("تعذر حفظ الملفات المحددة، يرجى المحاولة مجدداً.", "error")

        if folder_id:
            return redirect(url_for("admin.files", folder_id=folder_id))
        return redirect(url_for("admin.files"))

    # Case 2: Manual URL or no files uploaded
    if not custom_name:
        flash("يرجى إدخال اسم الملف أو اختيار ملف واحد على الأقل لرفعه من الجهاز.", "error")
        if folder_id:
            return redirect(url_for("admin.files", folder_id=folder_id))
        return redirect(url_for("admin.files"))

    try:
        data = {
            "name": custom_name,
            "file_name": custom_name,
            "category": manual_cat or "pdf",
            "size_display": manual_size,
            "description": description,
            "file_url": manual_url or "#",
            "folder_id": folder_id,
        }
        file_service.create_file(data)
        flash(f"تمت إضافة الملف/الرابط ({custom_name}) بنجاح إلى المستودع السحابي.", "success")
    except Exception as e:
        flash(f"فشل إضافة الملف: {e}", "error")

    if folder_id:
        return redirect(url_for("admin.files", folder_id=folder_id))
    return redirect(url_for("admin.files"))


@admin_bp.route("/files/<int:file_id>/delete", methods=["POST"])
@role_required("admin")
def delete_file(file_id):
    folder_id = request.form.get("folder_id", type=int)
    try:
        file_service.delete_file(file_id)
        flash("تم حذف العنصر من المستودع السحابي بنجاح.", "success")
    except Exception as e:
        flash(f"فشل حذف العنصر: {e}", "error")

    if folder_id:
        return redirect(url_for("admin.files", folder_id=folder_id))
    return redirect(url_for("admin.files"))


@admin_bp.route("/files/folder/<int:folder_id>/attach", methods=["POST"])
@role_required("admin")
def attach_files_to_folder(folder_id):
    file_ids = request.form.getlist("file_ids")
    if not file_ids:
        flash("يرجى تحديد ملف واحد على الأقل لربطه بالمجلد.", "error")
        return redirect(url_for("admin.files", folder_id=folder_id))
    try:
        count = file_service.attach_files_to_folder(folder_id, file_ids)
        flash(f"تم ربط وإضافة {count} ملف إلى المجلد بنجاح.", "success")
    except Exception as e:
        flash(f"فشل ربط الملفات بالمجلد: {e}", "error")

    return redirect(url_for("admin.files", folder_id=folder_id))


@admin_bp.route("/files/<int:file_id>/detach", methods=["POST"])
@role_required("admin")
def detach_file_from_folder(file_id):
    folder_id = request.form.get("folder_id", type=int)
    try:
        file_service.detach_file_from_folder(file_id)
        flash("تم نقل الملف من المجلد إلى المستوى الرئيسي للمكتبة بنجاح.", "success")
    except Exception as e:
        flash(f"فشل إخراج الملف من المجلد: {e}", "error")

    if folder_id:
        return redirect(url_for("admin.files", folder_id=folder_id))
    return redirect(url_for("admin.files"))


@admin_bp.route("/files/create-folder", methods=["POST"])
@role_required("admin")
def create_folder():
    folder_name = (request.form.get("folder_name") or "").strip()
    if not folder_name:
        flash("اسم المجلد مطلوب.", "error")
        return redirect(url_for("admin.files"))

    track = (request.form.get("track") or "عام").strip()
    description = (request.form.get("description") or "مجلد أكاديمي منظم").strip()

    try:
        created = file_service.create_file({
            "name": folder_name,
            "file_name": "",
            "category": "folder",
            "icon": "folder",
            "size_display": "مجلد",
            "description": f"{description} · {track}",
            "file_url": "#",
        })
        flash(f"تم إنشاء المجلد ({folder_name}) بنجاح في المكتبة.", "success")
        if created and created.get("id"):
            return redirect(url_for("admin.files", folder_id=created["id"]))
    except Exception as e:
        flash(f"فشل إنشاء المجلد: {e}", "error")

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
