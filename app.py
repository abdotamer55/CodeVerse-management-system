"""
CodeVerse Learning Management System (LMS)
Flask Application Factory & Core Server
"""
import os
import sys
import traceback
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from config import config_by_name

# Capture import errors for blueprints/services at module level
_import_error = None
try:
    from routes import auth_bp, admin_bp, student_bp
    from services import auth_service
except Exception as _e:
    _import_error = traceback.format_exc()


def create_app(config_name=None):
    """Application factory for CodeVerse Flask app."""
    if config_name is None:
        # Vercel sets FLASK_ENV=production; map it to our config keys safely
        env = os.environ.get("FLASK_ENV", "development")
        config_name = env if env in ("development", "testing", "production") else "development"

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure Uploads Directory Exists
    # NOTE: Vercel's filesystem is read-only, so we skip silently if creation fails
    upload_dir = app.config.get("UPLOAD_FOLDER")
    if upload_dir:
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except OSError:
            pass  # Read-only filesystem on Vercel — uploads go to cloud storage

    # ── Temporary Diagnostic Route (remove after debugging) ──────────────────
    @app.route("/debug-info")
    def debug_info():
        from database import get_database_url, check_connection
        db_url = get_database_url()
        db_ok, db_host, db_tables, db_err = False, "N/A", [], "not checked"
        try:
            db_ok, db_host, db_tables, db_err = check_connection(force=True)
        except Exception as e:
            db_err = str(e)

        return jsonify({
            "python_version": sys.version,
            "flask_env": os.environ.get("FLASK_ENV"),
            "database_url_set": bool(db_url),
            "database_url_prefix": (db_url[:40] + "...") if db_url else None,
            "db_connected": db_ok,
            "db_host": db_host,
            "db_tables": db_tables,
            "db_error": db_err,
            "import_error": _import_error,
            "secret_key_set": bool(os.environ.get("SECRET_KEY")),
            "supabase_url_set": bool(os.environ.get("SUPABASE_URL")),
        })
    # ─────────────────────────────────────────────────────────────────────────

    if _import_error:
        # If blueprints failed to import, return minimal app with error info
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def catch_all(path):
            return f"<pre>Import Error:\n{_import_error}</pre>", 500
        return app

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)

    # Root Gateway / Landing Page Route
    @app.route("/")
    def index():
        if "user_id" in session:
            if session.get("role") == "admin":
                return redirect(url_for("admin.dashboard"))
            if session.get("role") == "teacher":
                return redirect(url_for("auth.teacher_dashboard"))
            return redirect(url_for("student.dashboard"))
        return render_template("landing.html", user_role="student", page_id="landing")

    # Global Context Processors (Provides authenticated user data & role to all templates)
    @app.context_processor
    def inject_global_context():
        current_user = None
        user_id = session.get("user_id")
        if user_id:
            current_user = auth_service.get_user_by_id(user_id)

        user_role = session.get("role")
        return {
            "current_user": current_user,
            "user_role": user_role,
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html", page_id="404"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/404.html", page_id="403"), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html", page_id="500"), 500

    @app.errorhandler(413)
    def request_entity_too_large(e):
        flash("حجم الملف المرفوع يتجاوز الحد الأقصى المسموح به (100 ميجابايت).", "error")
        return redirect(request.referrer or url_for("admin.files"))

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
