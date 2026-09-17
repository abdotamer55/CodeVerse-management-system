import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env with override=True so project .env strictly overrides any shell environment variables
load_dotenv(BASE_DIR / ".env", override=True)


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "codeverse-dev-insecure-secret-key-replace-in-prod")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = False
    TESTING = False

    # Supabase PostgreSQL Configuration
    # Strictly loaded from environment. No localhost, 127.0.0.1, or MySQL fallback.
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

    # Security & Session Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Set to True in Production with HTTPS
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = "codeverse-testing-secret-key"


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = os.environ.get("SECRET_KEY")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
