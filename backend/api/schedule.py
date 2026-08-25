"""
DeadlineOS — Schedule Blueprint
=================================
REST API endpoints for Smart Scheduling.
"""

import logging
from flask import Blueprint, jsonify, request, g
from datetime import datetime, timezone
from utils.auth import require_auth
from utils.responses import success_response, error_response
from services.scheduling.activity_scheduler import ActivityScheduler
from services.scheduling.repository import SchedulingRepository

logger = logging.getLogger(__name__)
schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.route("/schedule/slots", methods=["GET"])
@require_auth
def get_slots():
    """Get scheduled slots for the current user."""
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    status = request.args.get("status")

    slots = ActivityScheduler.get_user_schedule(
        user_id=g.user_id,
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    return success_response("Schedule slots retrieved", slots)


@schedule_bp.route("/schedule/slots", methods=["POST"])
@require_auth
def create_slot():
    """Schedule an activity slot."""
    data = request.get_json(silent=True) or {}
    
    entity_type = data.get("entity_type", "TASK")
    entity_id = data.get("entity_id")
    title = data.get("title")
    
    start_str = data.get("start_time")
    end_str = data.get("end_time")
    
    start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00")) if start_str else None
    end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else None
    
    duration = data.get("duration_minutes")
    priority = data.get("priority")
    focus_block = data.get("focus_block", False)
    is_break = data.get("is_break", False)
    schedule_id = data.get("schedule_id")

    slot = ActivityScheduler.schedule_activity(
        user_id=g.user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration,
        priority=priority,
        focus_block=focus_block,
        is_break=is_break,
        schedule_id=schedule_id
    )

    return success_response("Activity scheduled successfully", slot.to_dict(), status_code=201)


@schedule_bp.route("/schedule/slots/<slot_id>", methods=["DELETE"])
@require_auth
def delete_slot(slot_id):
    """Delete a scheduled slot."""
    slot = SchedulingRepository.get_slot_by_id(slot_id)
    if not slot or slot.user_id != g.user_id:
        return error_response("Slot not found", status_code=404)
    
    SchedulingRepository.delete_slot(slot_id)
    return success_response("Slot deleted successfully")

@schedule_bp.route("/schedule/validate-conflicts", methods=["POST"])
@require_auth
def validate_conflicts():
    """Check whether a proposed schedule slot conflicts with existing commitments."""
    data = request.get_json(silent=True) or {}
    
    start_str = data.get("start_time")
    end_str = data.get("end_time")
    
    if not start_str or not end_str:
        return error_response("start_time and end_time are required", status_code=400)
        
    start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
    
    w_start_str = data.get("window_start")
    w_end_str = data.get("window_end")
    window_start = datetime.fromisoformat(w_start_str.replace("Z", "+00:00")) if w_start_str else None
    window_end = datetime.fromisoformat(w_end_str.replace("Z", "+00:00")) if w_end_str else None
    
    entity_id = data.get("entity_id")
    exclude_slot_id = data.get("exclude_slot_id")

    from services.scheduling.conflict_service import ConflictDetectionService
    report = ConflictDetectionService.check_conflicts(
        user_id=g.user_id,
        start_time=start_time,
        end_time=end_time,
        entity_id=entity_id,
        window_start=window_start,
        window_end=window_end,
        exclude_slot_id=exclude_slot_id,
        allow_past=data.get("allow_past", False)
    )

    return success_response("Conflict evaluation complete", report)

@schedule_bp.route("/schedule/priority-plan", methods=["POST"])
@require_auth
def priority_plan():
    """Generate a deterministic priority-ordered schedule plan."""
    data = request.get_json(silent=True) or {}
    activities = data.get("activities", [])
    
    w_start_str = data.get("window_start")
    w_end_str = data.get("window_end")
    
    if not w_start_str or not w_end_str:
        return error_response("window_start and window_end are required", status_code=400)

    window_start = datetime.fromisoformat(w_start_str.replace("Z", "+00:00"))
    window_end = datetime.fromisoformat(w_end_str.replace("Z", "+00:00"))
    buffer_minutes = data.get("buffer_minutes", 10)
    persist = data.get("persist", False)

    from services.scheduling.priority_scheduler import PriorityScheduler
    plan = PriorityScheduler.plan_priority_schedule(
        user_id=g.user_id,
        activities=activities,
        window_start=window_start,
        window_end=window_end,
        buffer_minutes=buffer_minutes,
        persist=persist
    )

    return success_response("Priority schedule synthesized", plan)

@schedule_bp.route("/schedule/reschedule", methods=["POST"])
@require_auth
def reschedule_slot():
    """Reschedule an existing activity slot safely."""
    data = request.get_json(silent=True) or {}
    slot_id = data.get("slot_id")
    start_str = data.get("start_time")
    end_str = data.get("end_time")
    duration = data.get("duration_minutes")
    force_cascade = data.get("force_cascade", False)

    if not slot_id or not start_str:
        return error_response("slot_id and start_time are required", status_code=400)

    start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else None

    from services.scheduling.rescheduling_engine import ReschedulingEngine
    res = ReschedulingEngine.reschedule_slot(
        user_id=g.user_id,
        slot_id=slot_id,
        new_start_time=start_time,
        new_end_time=end_time,
        duration_minutes=duration,
        force_cascade=force_cascade
    )

    if not res.get("success"):
        return error_response("Reschedule conflict or error", details=res, status_code=409)

    return success_response("Slot rescheduled successfully", res)

@schedule_bp.route("/schedule/checkin/evaluate", methods=["POST"])
@require_auth
def evaluate_checkins():
    """Evaluate and trigger auto check-ins for unstarted scheduled activities."""
    data = request.get_json(silent=True) or {}
    grace = data.get("grace_minutes", 10)

    from services.notifications.checkin_service import CheckInService
    checkins = CheckInService.evaluate_unstarted_activities(
        user_id=g.user_id,
        grace_minutes=grace
    )

    return success_response("Check-in evaluation complete", {
        "checkins_created": len(checkins),
        "notifications": [c.to_dict() for c in checkins]
    })
