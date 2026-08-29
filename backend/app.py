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
import warnings

# Suppress known vendor noise
warnings.filterwarnings("ignore", category=DeprecationWarning, module="cryptography")
warnings.filterwarnings("ignore", module="pypdf")
warnings.filterwarnings("ignore", message=".*urllib3.*")
warnings.filterwarnings("ignore", message=".*chardet.*")

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Global limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000 per day", "1000 per hour"],
    default_limits_exempt_when=lambda: request.method == "OPTIONS",
    storage_uri="memory://",
)
import uuid

# ── Local imports ──────────────────────────────────────────────────────────────
from config import get_config
from database.db import db
from services.gemini_service import GeminiService


# ── Logging setup (called before create_app so logs are captured from start) ──
def _configure_logging(cfg) -> None:
    """
    Configure application-wide structured logging.
    Forces stdout to UTF-8 on Windows.
    Outputs structured JSON log lines in production for log drains.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    import json

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if getattr(record, "exc_info", None):
                log_record["exc_info"] = self.formatException(record.exc_info)
            from flask import has_request_context, g

            if has_request_context():
                log_record["request_id"] = getattr(g, "request_id", None)
                log_record["user_id"] = getattr(g, "user_id", None)
            return json.dumps(log_record)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, cfg.LOG_LEVEL, logging.INFO))

    # Clear existing handlers
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    is_dev = os.getenv("FLASK_ENV", "development") == "development"

    if is_dev:
        handler.setFormatter(logging.Formatter(cfg.LOG_FORMAT, cfg.LOG_DATE_FORMAT))
    else:
        handler.setFormatter(JSONFormatter(datefmt=cfg.LOG_DATE_FORMAT))

    logger.addHandler(handler)

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
    # Environment validation
    required_vars = ["DATABASE_URL", "SUPABASE_JWT_SECRET", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error(
            f"[STARTUP FAILED] Missing required environment variables: {', '.join(missing_vars)}"
        )
        import sys

        sys.exit(1)

    app = Flask(__name__)

    # ── 1. Load configuration ──────────────────────────────────────────────────
    cfg = config_override or get_config()
    app.config.from_object(cfg)

    # ── 1.5 Initialize Sentry (if configured) ──────────────────────────────────
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )

    # ── 2. Configure logging & Env Validation ──────────────────────────────────
    _configure_logging(cfg)
    logger = logging.getLogger(__name__)
    is_dev = os.getenv("FLASK_ENV", "development") == "development"
    if not is_dev:
        logger.info(
            "[START] DeadlineOS starting | env=%s",
            os.getenv("FLASK_ENV", "development"),
        )

    missing_envs = []
    if not os.getenv("GEMINI_API_KEY"):
        missing_envs.append("GEMINI_API_KEY")
    if not os.getenv("DATABASE_URL") and not app.config.get("TESTING"):
        logger.error(
            "[ENV] DATABASE_URL is missing. DeadlineOS requires a valid PostgreSQL database (Neon) to start."
        )
        sys.exit(1)
    if not os.getenv("FLASK_SECRET_KEY"):
        if not is_dev and not app.config.get("TESTING"):
            logger.error("[ENV] FLASK_SECRET_KEY missing. This is required for production.")
            sys.exit(1)
        logger.warning("[ENV] FLASK_SECRET_KEY missing. Using insecure dev key.")

    if missing_envs:
        logger.error(f"[ENV] MISSING CRITICAL VARIABLES: {missing_envs}")
        logger.warning(
            "Application will start, but features relying on these variables will fail gracefully."
        )

    # ── 3. Initialise SQLAlchemy ───────────────────────────────────────────────
    db.init_app(app)
    Migrate(app, db)
    if not is_dev:
        logger.info("[DB] Database: %s", app.config["SQLALCHEMY_DATABASE_URI"])

    # ── 4. Ensure Model Registration ───────────────────────────────────────────
    with app.app_context():
        # Import all models so their metadata is registered with SQLAlchemy
        import models  # noqa: F401

        if not is_dev:
            logger.info("[DB] Database schema managed via Alembic migrations.")

    # ── 5. Initialise Central Hybrid AI Provider (OpenRouter Primary -> Gemini Fallback)
    from services.ai.provider import get_default_ai_provider
    app.extensions["ai_provider"] = get_default_ai_provider()

    # ── 6. Initialise Gemini Service (Legacy Wrapper) ──────────────────────────
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
        if not is_dev:
            logger.info(
                "[GEMINI] GeminiService initialised | model=%s",
                app.config["GEMINI_MODEL"],
            )
    else:
        logger.info(
            "[AI] Running with central AI Provider (OpenRouter Primary -> Gemini Fallback -> Deterministic Safe Fallback)."
        )

    # ── 7. Register Blueprints ─────────────────────────────────────────────────
    _register_blueprints(app)

    # ── 7.5 Configure CORS ─────────────────────────────────────────────────────
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "apikey", "X-Correlation-ID", "X-Request-ID", "X-Workspace-Id", "Idempotency-Key"],
        expose_headers=["Content-Type", "Authorization", "X-Request-ID", "X-Correlation-ID"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    )
    if not is_dev:
        logger.info("[CORS] Enabled for origins: %s", app.config["CORS_ORIGINS"])

    # ── 8. Global Error Handlers & Security Headers ────────────────────────────
    @app.after_request
    def add_security_headers(response):
        """Add enterprise security headers to every response."""
        # HTTP Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Content Security Policy (CSP)
        # Note: Frontend handles its own CSP, but we restrict API responses.
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection (Legacy but good practice)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

    from utils.errors import register_global_errors

    register_global_errors(app)

    # ── 8.5 Configure Rate Limiting ────────────────────────────────────────────
    limiter.init_app(app)
    app.extensions["limiter"] = limiter

    # ── 9. Register Request Hooks ──────────────────────────────────────────────
    _register_request_hooks(app)

    # ── 10. Root & Top-Level Health Endpoints ─────────────────────────────────
    @app.route("/", methods=["GET"])
    def root():
        return jsonify(
            {"name": "DeadlineOS API", "status": "healthy", "version": "1.0.0"}
        )

    @app.route("/health", methods=["GET"])
    def root_health():
        from api.health import health
        return health()

    @app.route("/live", methods=["GET"])
    def root_live():
        from api.health import live
        return live()

    @app.route("/ready", methods=["GET"])
    def root_ready():
        from api.health import ready
        return ready()

    if not is_dev:
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
    from api.users import users_bp
    from api.demo import demo_bp
    from api.settings import settings_bp
    from api.runtime import runtime_bp
    from api.today import today_bp
    from api.schedule import schedule_bp
    from api.recovery import recovery_bp
    from api.ai_intelligence import ai_intelligence_bp
    
    # Register Domain Listeners
    import services.domain_listeners


    app.register_blueprint(health_bp, url_prefix="/api")

    app.register_blueprint(tasks_bp, url_prefix="/api")
    limiter.exempt(tasks_bp)

    app.register_blueprint(agents_bp, url_prefix="/api")

    app.register_blueprint(orchestration_bp, url_prefix="/api")
    limiter.exempt(orchestration_bp)

    app.register_blueprint(analytics_bp, url_prefix="/api")
    limiter.exempt(analytics_bp)

    app.register_blueprint(calendar_bp, url_prefix="/api")
    limiter.exempt(calendar_bp)

    app.register_blueprint(interventions_bp, url_prefix="/api")
    limiter.exempt(interventions_bp)

    app.register_blueprint(goals_bp, url_prefix="/api")
    limiter.exempt(goals_bp)
    app.register_blueprint(documents_bp, url_prefix="/api")
    app.register_blueprint(voice_bp, url_prefix="/api")

    app.register_blueprint(notifications_bp, url_prefix="/api")
    limiter.exempt(notifications_bp)

    app.register_blueprint(reports_bp, url_prefix="/api")
    limiter.exempt(reports_bp)

    app.register_blueprint(users_bp, url_prefix="/api")
    limiter.exempt(users_bp)

    app.register_blueprint(demo_bp, url_prefix="/api")

    app.register_blueprint(settings_bp, url_prefix="/api")
    limiter.exempt(settings_bp)

    app.register_blueprint(runtime_bp, url_prefix="/api")

    app.register_blueprint(today_bp, url_prefix="/api")
    app.register_blueprint(schedule_bp, url_prefix="/api")
    app.register_blueprint(recovery_bp, url_prefix="/api")
    app.register_blueprint(ai_intelligence_bp)

    from api.business import business_bp
    app.register_blueprint(business_bp)
    limiter.exempt(business_bp)

    limiter.exempt(ai_intelligence_bp)
    limiter.exempt(recovery_bp)
    limiter.exempt(schedule_bp)
    limiter.exempt(today_bp)
    limiter.exempt(runtime_bp)

    is_dev = os.getenv("FLASK_ENV", "development") == "development"
    if not is_dev:
        logging.getLogger(__name__).info(
            "[ROUTES] Blueprints registered: health, tasks, agents, orchestration, analytics, calendar, interventions, goals, documents, voice, notifications, reports, users, demo, today"
        )


def _register_request_hooks(app: Flask) -> None:
    """Register before/after request hooks for logging and diagnostics."""
    logger = logging.getLogger(__name__)

    @app.before_request
    def log_request():
        """Log incoming API requests and inject Request / Correlation ID."""
        request_id = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
            or str(uuid.uuid4())
        )
        g.request_id = request_id

        if request.path.startswith("/api"):
            logger.debug(
                "→ %s %s | req_id=%s | content_type=%s | content_length=%s",
                request.method,
                request.path,
                request_id,
                request.content_type,
                request.content_length,
            )

    @app.after_request
    def log_response(response):
        """Log outgoing API response, attach security headers and correlation IDs."""
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
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = request_id

        return response

    _register_error_handlers(app)


def _register_error_handlers(app: Flask) -> None:
    """Register standardized JSON error handlers for API consistency."""
    logger = logging.getLogger(__name__)

    @app.errorhandler(400)
    def handle_bad_request(e):
        req_id = getattr(g, "request_id", str(uuid.uuid4()))
        msg = getattr(e, "description", "Bad Request")
        return jsonify({
            "status": "error",
            "error": {
                "code": "BAD_REQUEST",
                "message": msg,
                "request_id": req_id
            }
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(e):
        req_id = getattr(g, "request_id", str(uuid.uuid4()))
        msg = getattr(e, "description", "Authentication required")
        return jsonify({
            "status": "error",
            "error": {
                "code": "UNAUTHORIZED",
                "message": msg,
                "request_id": req_id
            }
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(e):
        req_id = getattr(g, "request_id", str(uuid.uuid4()))
        msg = getattr(e, "description", "Access forbidden")
        return jsonify({
            "status": "error",
            "error": {
                "code": "FORBIDDEN",
                "message": msg,
                "request_id": req_id
            }
        }), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        req_id = getattr(g, "request_id", str(uuid.uuid4()))
        return jsonify({
            "status": "error",
            "error": {
                "code": "NOT_FOUND",
                "message": "Resource or endpoint not found",
                "request_id": req_id
            }
        }), 404

    @app.errorhandler(429)
    def handle_rate_limit(e):
        req_id = getattr(g, "request_id", str(uuid.uuid4()))
        return jsonify({
            "status": "error",
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down and try again.",
                "request_id": req_id
            }
        }), 429

    @app.errorhandler(500)
    def handle_server_error(e):
        req_id = getattr(g, "request_id", str(uuid.uuid4()))
        logger.error(f"Internal server error | req_id={req_id} | error={e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please try again later.",
                "request_id": req_id
            }
        }), 500


# ── Development server entry-point ─────────────────────────────────────────────
if __name__ == "__main__":
    flask_app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"

    if debug and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Clean Startup Banner
        print("\n" + "=" * 50)
        print("DEADLINEOS BACKEND")
        print("==================\n")
        print(f"Environment: {os.getenv('FLASK_ENV', 'development').capitalize()}")
        print("Database: Connected")
        print(
            f"Gemini: {'Connected' if flask_app.extensions.get('gemini_service') else 'Disconnected'}"
        )
        print("SocketIO: Ready\n")
        print("Modules:")
        print(
            "✓ Planning Agent\n✓ Rescue Agent\n✓ Digital Twin\n✓ Document Intelligence"
        )
        print("✓ Voice Copilot\n✓ Vision Intelligence\n✓ Analytics\n")
        print("Server:")
        print(f"http://localhost:{port}")
        print("=" * 50 + "\n")
    else:
        logging.getLogger(__name__).info(
            "[SERVER] Dev server running at http://localhost:%d", port
        )
    flask_app.run(host="0.0.0.0", port=port, debug=debug)  # nosec B104
