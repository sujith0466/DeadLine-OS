"""
DeadlineOS — Flask Application Factory
=========================================
Entry point for the DeadlineOS backend.

Uses the Application Factory Pattern so multiple instances can be created
with different configurations (e.g., for testing, development, production).

Usage
-----
    # Development server
    python app.py

    # Production (Gunicorn + eventlet for SocketIO)
    gunicorn --worker-class eventlet -w 1 app:create_app()

    # With Flask CLI
    FLASK_APP=app.py flask run
"""

import logging
import logging.config
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Local imports ──────────────────────────────────────────────────────────────
from config import get_config
from database.db import db
from services.gemini_service import GeminiService


# ── Logging setup (called before create_app so logs are captured from start) ──
def _configure_logging(cfg) -> None:
    """
    Configure application-wide logging.

    Forces stdout to UTF-8 on Windows so emoji / Unicode in log messages
    don't raise UnicodeEncodeError on CP1252 terminals.
    Outputs structured log lines to stdout captured by Render / Heroku log drains.
    """
    # Re-open stdout in UTF-8 mode (no-op on Linux/macOS where UTF-8 is default)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=getattr(logging, cfg.LOG_LEVEL, logging.INFO),
        format=cfg.LOG_FORMAT,
        datefmt=cfg.LOG_DATE_FORMAT,
        stream=sys.stdout,
    )
    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)


# ── Application Factory ────────────────────────────────────────────────────────
def create_app(config_override=None) -> Flask:
    """
    Create and configure a Flask application instance.

    Parameters
    ----------
    config_override : Optional config class to override the environment-based one.
                      Useful for testing: create_app(TestingConfig)

    Returns
    -------
    Flask : Fully configured Flask application.
    """
    app = Flask(__name__)

    # ── 1. Load configuration ──────────────────────────────────────────────────
    cfg = config_override or get_config()
    app.config.from_object(cfg)

    # ── 2. Configure logging & Env Validation ──────────────────────────────────
    _configure_logging(cfg)
    logger = logging.getLogger(__name__)
    logger.info("[START] DeadlineOS starting | env=%s", os.getenv("FLASK_ENV", "development"))

    missing_envs = []
    if not os.getenv("GEMINI_API_KEY"): missing_envs.append("GEMINI_API_KEY")
    if not os.getenv("DATABASE_URL") and not app.config.get("TESTING"):
        logger.error("[ENV] DATABASE_URL is missing. DeadlineOS requires a valid PostgreSQL database (Neon) to start.")
        sys.exit(1)
    if not os.getenv("FLASK_SECRET_KEY"):
        logger.warning("[ENV] FLASK_SECRET_KEY missing. Using insecure dev key.")

    if missing_envs:
        logger.error(f"[ENV] MISSING CRITICAL VARIABLES: {missing_envs}")
        logger.warning("Application will start, but features relying on these variables will fail gracefully.")

    # ── 3. Initialise SQLAlchemy ───────────────────────────────────────────────
    db.init_app(app)
    logger.info("[DB] Database: %s", app.config["SQLALCHEMY_DATABASE_URI"])

    # ── 4. Create database tables (idempotent) ─────────────────────────────────
    with app.app_context():
        # Import all models so their metadata is registered before create_all()
        import models  # noqa: F401
        db.create_all()
        logger.info("[DB] Database tables ensured.")

    # ── 5. Configure CORS ─────────────────────────────────────────────────────
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
    logger.info("[CORS] Enabled for origins: %s", app.config["CORS_ORIGINS"])

    # ── 6. Initialise Gemini Service ───────────────────────────────────────────
    if app.config.get("GEMINI_API_KEY"):
        gemini = GeminiService(
            api_key=app.config["GEMINI_API_KEY"],
            model=app.config["GEMINI_MODEL"],
            vision_model=app.config["GEMINI_VISION_MODEL"],
            max_retries=app.config["GEMINI_MAX_RETRIES"],
            retry_delay=app.config["GEMINI_RETRY_DELAY"],
            cache_ttl=app.config["GEMINI_CACHE_TTL"],
            cache_maxsize=app.config["GEMINI_CACHE_MAXSIZE"],
        )
        # Store on app.extensions so blueprints can access via current_app.extensions
        app.extensions["gemini_service"] = gemini
        logger.info("[GEMINI] GeminiService initialised | model=%s", app.config["GEMINI_MODEL"])
    else:
        logger.warning(
            "[GEMINI] GEMINI_API_KEY not set. GeminiService disabled. "
            "Add it to your .env file."
        )

    # ── 7. Register Blueprints ─────────────────────────────────────────────────
    _register_blueprints(app)

    # ── 8. Register Error Handlers ─────────────────────────────────────────────
    _register_error_handlers(app)

    # ── 9. Register Request Hooks ──────────────────────────────────────────────
    _register_request_hooks(app)

    # ── 10. Root Endpoint ──────────────────────────────────────────────────────
    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "name": "DeadlineOS API",
            "status": "healthy",
            "version": "1.0.0"
        })

    logger.info("[OK] DeadlineOS backend ready.")
    return app


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints under the /api prefix."""
    from api.health import health_bp
    from api.tasks import tasks_bp
    from api.agents import agents_bp
    from api.orchestration import orchestration_bp
    from api.analytics import analytics_bp
    from api.calendar import calendar_bp
    from api.interventions import interventions_bp
    from api.goals import goals_bp
    from api.documents import documents_bp
    from api.voice import voice_bp
    from api.notifications import notifications_bp
    from api.reports import reports_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(tasks_bp, url_prefix="/api")
    app.register_blueprint(agents_bp, url_prefix="/api")
    app.register_blueprint(orchestration_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(calendar_bp, url_prefix="/api")
    app.register_blueprint(interventions_bp, url_prefix="/api")
    app.register_blueprint(goals_bp, url_prefix="/api")
    app.register_blueprint(documents_bp, url_prefix="/api")
    app.register_blueprint(voice_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")
    app.register_blueprint(reports_bp, url_prefix="/api")

    logging.getLogger(__name__).info(
        "[ROUTES] Blueprints registered: health, tasks, agents, orchestration, analytics, calendar, interventions, goals, documents, voice, notifications, reports"
    )


def _register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers that return consistent JSON error responses.

    All errors follow the shape:
        { "error": "<message>", "status": <http_code> }
    """
    logger = logging.getLogger(__name__)

    @app.errorhandler(400)
    def bad_request(exc):
        logger.warning("400 Bad Request: %s | path=%s", exc.description, request.path)
        return jsonify({"error": str(exc.description), "status": 400}), 400

    @app.errorhandler(404)
    def not_found(exc):
        logger.info("404 Not Found: %s", request.path)
        return jsonify(
            {
                "error": str(exc.description) if exc.description else "Resource not found.",
                "status": 404,
            }
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify(
            {"error": f"Method '{request.method}' not allowed on this endpoint.", "status": 405}
        ), 405

    @app.errorhandler(422)
    def unprocessable(exc):
        return jsonify({"error": str(exc.description), "status": 422}), 422

    @app.errorhandler(500)
    def internal_error(exc):
        logger.exception("500 Internal Server Error: %s", exc)
        return jsonify(
            {
                "error": "An unexpected server error occurred. Please try again.",
                "status": 500,
            }
        ), 500

    @app.errorhandler(503)
    def service_unavailable(exc):
        return jsonify({"error": str(exc.description), "status": 503}), 503

    # Catch-all for unhandled exceptions (Flask debug=False mode)
    @app.errorhandler(Exception)
    def handle_exception(exc):
        # Re-raise HTTP exceptions so Flask handles them normally
        from werkzeug.exceptions import HTTPException
        if isinstance(exc, HTTPException):
            return exc
            
        from sqlalchemy.exc import SQLAlchemyError
        if isinstance(exc, SQLAlchemyError):
            db.session.rollback()
            logger.error("Database Transaction Failed (Neon Resilience): %s", exc)
            return jsonify({
                "error": "Database Service Unavailable",
                "status": 503,
            }), 503
            
        if "GeminiServiceError" in type(exc).__name__ or "gemini" in str(exc).lower() or "generativeai" in str(type(exc)).lower():
            logger.error("AI Service Error (Gemini Resilience): %s", exc)
            return jsonify({
                "error": "AI Service Temporarily Unavailable: " + str(exc),
                "status": 503,
            }), 503
            
        logger.exception("Unhandled exception: %s", exc)
        return jsonify(
            {
                "error": "An unexpected error occurred.",
                "status": 500,
            }
        ), 500


def _register_request_hooks(app: Flask) -> None:
    """Register before/after request hooks for logging and diagnostics."""
    logger = logging.getLogger(__name__)

    @app.before_request
    def log_request():
        """Log every incoming API request."""
        if request.path.startswith("/api"):
            logger.debug(
                "→ %s %s | content_type=%s | content_length=%s",
                request.method,
                request.path,
                request.content_type,
                request.content_length,
            )

    @app.after_request
    def log_response(response):
        """Log every outgoing API response."""
        if request.path.startswith("/api"):
            logger.debug(
                "← %s %s %d",
                request.method,
                request.path,
                response.status_code,
            )
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


# ── Development server entry-point ─────────────────────────────────────────────
if __name__ == "__main__":
    flask_app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"

    logging.getLogger(__name__).info(
        "[SERVER] Dev server running at http://localhost:%d", port
    )
    flask_app.run(host="0.0.0.0", port=port, debug=debug)
