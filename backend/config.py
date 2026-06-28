"""
DeadlineOS — Configuration Module
==================================
Centralizes all environment-driven configuration.
Supports three profiles: Development, Testing, Production.
"""

import os
from dotenv import load_dotenv

# Load .env from the backend directory (or project root)
load_dotenv()


class BaseConfig:
    """Shared settings across all environments."""

    # ── Application ──────────────────────────────────────────
    APP_NAME = "DeadlineOS"
    APP_VERSION = "1.0.0"
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB max upload size limit

    # ── Database ──────────────────────────────────────────────
    # SQLAlchemy connection string mapped to Neon PostgreSQL
    BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False  # Set True in Dev to log SQL queries
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 1800,  # recycle connections every 30 mins to avoid Neon drops
        "pool_pre_ping": True, # Test connections before handing out to prevent 'server closed the connection unexpectedly'
        "max_overflow": 20
    }

    # ── CORS ──────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Example: "http://localhost:5173,https://deadlineos.vercel.app"
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")

    # ── Google AI / Gemini ────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash")

    # ── Gemini Rate-limit / Retry ─────────────────────────────
    GEMINI_MAX_RETRIES: int = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    GEMINI_RETRY_DELAY: float = float(os.getenv("GEMINI_RETRY_DELAY", "1.5"))

    # ── Response Cache (in-memory TTL) ────────────────────────
    GEMINI_CACHE_TTL: int = int(os.getenv("GEMINI_CACHE_TTL", "300"))   # seconds
    GEMINI_CACHE_MAXSIZE: int = int(os.getenv("GEMINI_CACHE_MAXSIZE", "100"))

    # ── WebSocket ─────────────────────────────────────────────
    WS_ASYNC_MODE: str = os.getenv("WS_ASYNC_MODE", "eventlet")

    # ── Scheduler ─────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


class DevelopmentConfig(BaseConfig):
    """Local development — verbose output, debug mode on."""
    DEBUG = True
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = "DEBUG"


class TestingConfig(BaseConfig):
    """Isolated test runs — in-memory database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """Production — strict settings, no debug."""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = "WARNING"


# ── Config resolver ───────────────────────────────────────────────────────────
_config_map: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config() -> BaseConfig:
    """Return the config class matching the FLASK_ENV environment variable."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return _config_map.get(env, DevelopmentConfig)
