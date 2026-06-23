import logging
from flask import Blueprint, jsonify, request
from services.calendar_service import CalendarService

logger = logging.getLogger(__name__)
calendar_bp = Blueprint("calendar", __name__)

@calendar_bp.route("/calendar/events", methods=["GET"])
def get_events():
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    return jsonify({"status": "success", "data": CalendarService.get_events(start_date, end_date)}), 200

@calendar_bp.route("/calendar/intelligence", methods=["GET"])
def get_intelligence():
    return jsonify({"status": "success", "data": CalendarService.get_intelligence()}), 200

@calendar_bp.route("/calendar/reschedule", methods=["POST"])
def reschedule():
    data = request.json or {}
    event_id = data.get("id")
    start = data.get("start")
    end = data.get("end")
    
    success = CalendarService.reschedule_event(event_id, start, end)
    if success:
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400
