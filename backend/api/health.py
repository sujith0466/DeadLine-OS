"""
DeadlineOS — Health Check Blueprint
======================================
Provides system health endpoints used by monitoring tools,
load balancers, deployment pipelines, and the frontend status indicator.

Routes
------
GET  /api/health          →  Basic liveness probe
GET  /api/health/gemini   →  Gemini API connectivity check
GET  /api/health/db       →  Database connectivity check
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
    Basic liveness probe.

    Returns 200 if the Flask application is running.
    Used by Render / Vercel health checks and load balancers.

    Response
    --------
    {
        "status": "healthy",
        "service": "DeadlineOS",
        "version": "1.0.0",
        "timestamp": "<ISO 8601 UTC>"
    }
    """
    return jsonify(
        {
            "status": "healthy",
            "service": "DeadlineOS",
            "version": current_app.config.get("APP_VERSION", "1.0.0"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ), 200


@health_bp.route("/health/gemini", methods=["GET"])
def health_gemini():
    """
    Gemini API connectivity check.

    Sends a minimal prompt to verify that the API key is valid and
    the Google AI endpoint is reachable.

    Response
    --------
    {
        "status": "ok" | "error",
        "model": "<model name>",
        "message": "<result or error description>"
    }
    """
    gemini = current_app.extensions.get("gemini_service")

    if gemini is None:
        return jsonify(
            {
                "status": "error",
                "message": "GeminiService not initialised in app context.",
            }
        ), 503

    result = gemini.health_check()
    http_status = 200 if result.get("status") == "ok" else 503
    return jsonify(result), http_status


@health_bp.route("/health/db", methods=["GET"])
def health_db():
    """
    Database connectivity check.

    Executes a lightweight SQL query to confirm the database is reachable.

    Response
    --------
    {
        "status": "ok" | "error",
        "message": "<result or error description>"
    }
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok", "message": "Database reachable"}), 200
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 503
