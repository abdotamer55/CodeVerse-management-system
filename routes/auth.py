"""
Authentication Blueprint & RBAC Guards
Handles login, logout, session management, and role-based route protection.
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from services import auth_service

auth_bp = Blueprint("auth", __name__)


def login_required(view_func):
    """Decorator ensuring the request is made by an authenticated session."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("يرجى تسجيل الدخول للوصول إلى هذه الصفحة", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped_view


def role_required(role_name: str):
    """Decorator ensuring the authenticated user possesses the required role."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login", next=request.path))

            current_role = session.get("role")
            if current_role != role_name:
                # Disallow unauthorized cross-portal access
                if current_role == "student":
                    flash("ليس لديك صلاحيات الوصول إلى بوابة الإدارة", "error")
                    return redirect(url_for("student.dashboard"))
                elif current_role == "admin":
                    # Admins can be redirected to admin dashboard if accessing restricted student endpoints
                    flash("أنت مسجل كمسؤول، تم تحويلك إلى لوحة الإدارة", "info")
                    return redirect(url_for("admin.dashboard"))
                abort(403)

            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle login presentation and authentication processing."""
    # If already authenticated, redirect to respective dashboard
    if "user_id" in session:
        return _dashboard_for_role(session.get("role"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user, error = auth_service.authenticate(identifier, password)
        if error:
            flash(error, "error")
            return render_template("auth/login.html", identifier=identifier, user_role="student", page_id="login"), 401

        # Establish session
        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session.permanent = remember

        # Handle redirection
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)

        return _dashboard_for_role(user["role"])

    return render_template("auth/login.html", user_role="student", page_id="login")


def _dashboard_for_role(role):
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "teacher":
        return redirect(url_for("auth.teacher_dashboard"))
    return redirect(url_for("student.dashboard"))


@auth_bp.route("/teacher/dashboard")
@role_required("teacher")
def teacher_dashboard():
    """Dedicated teacher landing page; it grants no administrative permissions."""
    return render_template("teacher/dashboard.html", user_role="teacher", page_id="teacher-dashboard")


@auth_bp.route("/logout", methods=["GET"])
def logout():
    """Clear user session and redirect to login page."""
    session.clear()
    flash("تم تسجيل الخروج من المنصة بنجاح", "info")
    return redirect(url_for("auth.login"))
