"""
DeadlineOS — Health & Readiness Check Blueprint
================================================
Provides standard system health, liveness, and readiness probes used by
load balancers, Kubernetes, Render, deployment pipelines, and frontend monitors.

Routes
------
GET  /api/health          →  Application health summary
GET  /api/live            →  Liveness probe (process is responsive)
GET  /api/ready           →  Readiness probe (database & dependencies available)
GET  /api/health/db       →  Database connectivity check
GET  /api/health/ai       →  AI Provider hierarchy status (lightweight inspection)
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify

from database.db import db

logger = logging.getLogger(__name__)

# Blueprint registered in app.py with url_prefix="/api"
health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    Standard application health probe.
    Returns 200 with service metadata and component statuses.
    """
    db_ok = True
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as exc:
        logger.warning("Health probe DB check failed: %s", exc)
        db_ok = False

    status = "healthy" if db_ok else "degraded"
    status_code = 200 if db_ok else 503

    return (
        jsonify(
            {
                "status": status,
                "service": "DeadlineOS",
                "version": current_app.config.get("APP_VERSION", "1.0.0"),
                "environment": current_app.config.get("FLASK_ENV", "production"),
                "database": "connected" if db_ok else "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        status_code,
    )


@health_bp.route("/live", methods=["GET"])
def live():
    """
    Liveness probe.
    Verifies that the application process is running and able to handle HTTP traffic.
    Never executes external network or database calls.
    """
    return (
        jsonify(
            {
                "status": "alive",
                "service": "DeadlineOS",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )


@health_bp.route("/ready", methods=["GET"])
def ready():
    """
    Readiness probe.
    Verifies that all essential dependencies (PostgreSQL database) are reachable
    before receiving client traffic.
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        return (
            jsonify(
                {
                    "status": "ready",
                    "service": "DeadlineOS",
                    "dependencies": {
                        "database": "ok",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return (
            jsonify(
                {
                    "status": "not_ready",
                    "service": "DeadlineOS",
                    "dependencies": {
                        "database": "error",
                    },
                    "error": "Database unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            503,
        )


@health_bp.route("/health/db", methods=["GET"])
def health_db():
    """
    Database connectivity check.
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok", "message": "Database reachable"}), 200
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return jsonify({"status": "error", "message": "Database unreachable"}), 503


@health_bp.route("/health/ai", methods=["GET"])
def health_ai():
    """
    Lightweight AI provider hierarchy status check.
    Inspects provider registration without calling expensive external APIs.
    """
    ai_provider = current_app.extensions.get("ai_provider")
    return (
        jsonify(
            {
                "status": "ok" if ai_provider else "degraded",
                "primary": "OpenRouter",
                "fallback": "Gemini",
                "deterministic": "Active",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )
