"""
CodeVerse Learning Management System (LMS)
Flask Application Factory & Core Server
"""
import os
from flask import Flask, render_template, redirect, url_for, session
from config import config_by_name
from routes import auth_bp, admin_bp, student_bp
from services import auth_service


def create_app(config_name=None):
    """Application factory for CodeVerse Flask app."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

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

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
