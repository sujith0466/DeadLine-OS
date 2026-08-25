"""
DeadlineOS — Recovery API Blueprint (Phase 5)
=============================================
REST endpoints for schedule recovery, skip today, activity pause/resume,
vacation mode, and emergency mode.
"""

import logging
from flask import Blueprint, jsonify, request, g
from utils.auth import require_auth
from utils.responses import success_response, error_response
from services.recovery.service import RecoveryService

logger = logging.getLogger(__name__)
recovery_bp = Blueprint("recovery", __name__)


@recovery_bp.route("/recovery/skip-today", methods=["POST"])
@require_auth
def skip_today():
    """Skip an activity for today without deleting the underlying object."""
    data = request.get_json(silent=True) or {}
    entity_id = data.get("entity_id")
    entity_type = data.get("entity_type", "TASK")
    schedule_id = data.get("schedule_id")
    reason = data.get("reason")

    if not entity_id:
        return error_response("entity_id is required", status_code=400)

    try:
        result = RecoveryService.skip_today(
            user_id=g.user_id,
            entity_id=entity_id,
            entity_type=entity_type,
            schedule_id=schedule_id,
            reason=reason
        )
        return success_response("Activity skipped for today", result)
    except Exception as e:
        logger.error(f"Failed to skip activity for today: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/pause-activity", methods=["POST"])
@require_auth
def pause_activity():
    """Pause an activity from scheduling and pre-alerts."""
    data = request.get_json(silent=True) or {}
    entity_id = data.get("entity_id")
    entity_type = data.get("entity_type", "TASK")
    reason = data.get("reason")

    if not entity_id:
        return error_response("entity_id is required", status_code=400)

    try:
        result = RecoveryService.pause_activity(
            user_id=g.user_id,
            entity_id=entity_id,
            entity_type=entity_type,
            reason=reason
        )
        return success_response("Activity paused", result)
    except Exception as e:
        logger.error(f"Failed to pause activity: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/resume-activity", methods=["POST"])
@require_auth
def resume_activity():
    """Resume a paused activity."""
    data = request.get_json(silent=True) or {}
    entity_id = data.get("entity_id")
    entity_type = data.get("entity_type", "TASK")

    if not entity_id:
        return error_response("entity_id is required", status_code=400)

    try:
        result = RecoveryService.resume_activity(
            user_id=g.user_id,
            entity_id=entity_id,
            entity_type=entity_type
        )
        return success_response("Activity resumed", result)
    except Exception as e:
        logger.error(f"Failed to resume activity: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/items", methods=["GET"])
@require_auth
def get_recovery_items():
    """Get all recoverable items (missed, interrupted, overdue, skipped)."""
    try:
        data = RecoveryService.get_recoverable_items(user_id=g.user_id)
        return success_response("Recoverable items retrieved", data)
    except Exception as e:
        logger.error(f"Failed to fetch recovery items: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/action", methods=["POST"])
@require_auth
def execute_recovery_action():
    """Execute a recovery action on an activity."""
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    entity_id = data.get("entity_id")
    entity_type = data.get("entity_type", "TASK")
    schedule_id = data.get("schedule_id")
    params = data.get("params", {})

    if not action or not entity_id:
        return error_response("action and entity_id are required", status_code=400)

    try:
        result = RecoveryService.execute_recovery_action(
            user_id=g.user_id,
            action=action,
            entity_id=entity_id,
            entity_type=entity_type,
            schedule_id=schedule_id,
            params=params
        )
        return success_response("Recovery action executed", result)
    except Exception as e:
        logger.error(f"Failed to execute recovery action: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/smart-recommendations", methods=["GET"])
@require_auth
def get_smart_recommendations():
    """Generate deterministic, explainable smart recovery strategies."""
    from services.recovery.smart_recovery import SmartRecoveryService
    try:
        data = SmartRecoveryService.evaluate_recommendations(user_id=g.user_id)
        return success_response("Smart recovery recommendations generated", data)
    except Exception as e:
        logger.error(f"Failed to generate smart recommendations: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/vacation/start", methods=["POST"])
@require_auth
def start_vacation():
    """Activate Vacation Mode."""
    data = request.get_json(silent=True) or {}
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    suppress_notifications = data.get("suppress_notifications", True)
    reason = data.get("reason")

    if not start_date or not end_date:
        return error_response("start_date and end_date are required (YYYY-MM-DD)", status_code=400)

    try:
        result = RecoveryService.set_vacation_mode(
            user_id=g.user_id,
            start_date=start_date,
            end_date=end_date,
            suppress_notifications=suppress_notifications,
            reason=reason
        )
        return success_response("Vacation mode activated", result)
    except Exception as e:
        logger.error(f"Failed to start vacation mode: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/vacation/end", methods=["POST"])
@require_auth
def end_vacation():
    """Deactivate Vacation Mode."""
    try:
        result = RecoveryService.end_vacation_mode(user_id=g.user_id)
        return success_response("Vacation mode deactivated", result)
    except Exception as e:
        logger.error(f"Failed to end vacation mode: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/vacation/status", methods=["GET"])
@require_auth
def get_vacation_status():
    """Get current Vacation Mode status."""
    try:
        from models.user_settings import UserSettings
        settings = UserSettings.get_or_create(g.user_id)
        vacation = (settings.planner or {}).get("vacation_mode", {"enabled": False})
        is_active = RecoveryService.is_user_on_vacation(g.user_id)
        return success_response("Vacation status retrieved", {
            "vacation_mode": vacation,
            "is_active_today": is_active
        })
    except Exception as e:
        logger.error(f"Failed to get vacation status: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/emergency/activate", methods=["POST"])
@require_auth
def activate_emergency():
    """Activate Emergency Mode."""
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")
    auto_skip_non_critical = data.get("auto_skip_non_critical", False)

    try:
        result = RecoveryService.activate_emergency_mode(
            user_id=g.user_id,
            reason=reason,
            auto_skip_non_critical=auto_skip_non_critical
        )
        return success_response("Emergency mode activated", result)
    except Exception as e:
        logger.error(f"Failed to activate emergency mode: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/emergency/deactivate", methods=["POST"])
@require_auth
def deactivate_emergency():
    """Deactivate Emergency Mode."""
    try:
        result = RecoveryService.deactivate_emergency_mode(user_id=g.user_id)
        return success_response("Emergency mode deactivated", result)
    except Exception as e:
        logger.error(f"Failed to deactivate emergency mode: {e}")
        return error_response(str(e), status_code=500)


@recovery_bp.route("/recovery/emergency/status", methods=["GET"])
@require_auth
def get_emergency_status():
    """Get current Emergency Mode status."""
    try:
        from models.user_settings import UserSettings
        settings = UserSettings.get_or_create(g.user_id)
        emergency = (settings.planner or {}).get("emergency_mode", {"enabled": False})
        is_active = RecoveryService.is_emergency_mode_active(g.user_id)
        return success_response("Emergency status retrieved", {
            "emergency_mode": emergency,
            "is_active": is_active
        })
    except Exception as e:
        logger.error(f"Failed to get emergency status: {e}")
        return error_response(str(e), status_code=500)
