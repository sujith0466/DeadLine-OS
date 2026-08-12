"""
DeadlineOS — Today API (Phase 2)
=================================
Dedicated API for the Today Surface.
"""
from flask import Blueprint, jsonify, g
from utils.auth import require_auth
from utils.responses import success_response
from services.today_service import TodayService

today_bp = Blueprint("today", __name__)

@today_bp.route("/today", methods=["GET"])
@require_auth
def get_today_surface():
    """
    Fetch the aggregated execution state for the Today Surface.
    """
    data = TodayService.get_today_activities(g.user_id)
    return success_response("Today surface retrieved", data)
