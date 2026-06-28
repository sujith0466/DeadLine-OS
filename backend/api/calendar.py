import logging
from flask import Blueprint, jsonify, request, g
from services.calendar_service import CalendarService
from utils.auth import require_auth

logger = logging.getLogger(__name__)
calendar_bp = Blueprint("calendar", __name__)

@calendar_bp.route("/calendar/events", methods=["GET"])
@require_auth
def get_events():
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    return jsonify({"status": "success", "data": CalendarService.get_events(start_date=start_date, end_date=end_date)}), 200

@calendar_bp.route("/calendar/intelligence", methods=["GET"])
@require_auth
def get_intelligence():
    return jsonify({"status": "success", "data": CalendarService.get_intelligence()}), 200

@calendar_bp.route("/calendar/reschedule", methods=["POST"])
@require_auth
def reschedule():
    data = request.json or {}
    event_id = data.get("id")
    start = data.get("start")
    end = data.get("end")
    
    success = CalendarService.reschedule_event(event_id=event_id, new_start=start, new_end=end)
    if success:
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400
