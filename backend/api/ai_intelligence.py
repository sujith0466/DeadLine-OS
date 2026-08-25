"""
DeadlineOS — AI Intelligence API Blueprint (Phase 6)
====================================================
Exposes authenticated, rate-limited endpoints for all 9 AI features.
"""

from flask import Blueprint, request, jsonify, g
from utils.auth import require_auth
from services.ai.delay_detection import DelayDetectionService
from services.ai.miss_prediction import MissPredictionService
from services.ai.reminder_intelligence import AdaptiveReminderService
from services.ai.workload_balancer import WorkloadBalancerService
from services.ai.workload_strain import WorkloadStrainService
from services.ai.energy_preferences import EnergyPreferencesService
from services.ai.digital_twin_learning import DigitalTwinLearningService
from services.ai.weekly_coach import WeeklyAICoachService
from services.ai.accountability_partner import AccountabilityPartnerService

ai_intelligence_bp = Blueprint("ai_intelligence", __name__, url_prefix="/api/ai")


@ai_intelligence_bp.route("/delay-risk", methods=["POST"])
@require_auth
def delay_risk():
    user_id = g.user_id
    data = request.get_json(silent=True) or {}
    entity_id = data.get("entity_id")
    result = DelayDetectionService.evaluate_delay_risk(user_id, entity_id)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/miss-prediction", methods=["POST"])
@require_auth
def miss_prediction():
    user_id = g.user_id
    result = MissPredictionService.predict_miss_risk(user_id)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/reminder-timing", methods=["POST"])
@require_auth
def reminder_timing():
    user_id = g.user_id
    data = request.get_json(silent=True) or {}
    duration = data.get("slot_duration_minutes", 60)
    priority = data.get("priority_score", 50)
    result = AdaptiveReminderService.recommend_reminder_timing(user_id, duration, priority)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/workload-balancer", methods=["POST"])
@require_auth
def workload_balancer():
    user_id = g.user_id
    result = WorkloadBalancerService.evaluate_workload(user_id)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/workload-strain", methods=["POST"])
@require_auth
def workload_strain():
    user_id = g.user_id
    result = WorkloadStrainService.evaluate_workload_strain(user_id)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/energy-preferences", methods=["GET"])
@require_auth
def get_energy_preferences():
    user_id = g.user_id
    result = EnergyPreferencesService.get_energy_preferences(user_id)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/energy-preferences", methods=["PUT"])
@require_auth
def update_energy_preferences():
    user_id = g.user_id
    data = request.get_json(silent=True) or {}
    result = EnergyPreferencesService.set_energy_preferences(
        user_id=user_id,
        peak_focus_start=data.get("peak_focus_start"),
        peak_focus_end=data.get("peak_focus_end"),
        low_energy_start=data.get("low_energy_start"),
        low_energy_end=data.get("low_energy_end"),
        preferred_session_duration_minutes=data.get("preferred_session_duration_minutes"),
        preferred_break_duration_minutes=data.get("preferred_break_duration_minutes")
    )
    return jsonify(result), 200


@ai_intelligence_bp.route("/digital-twin/profile", methods=["GET"])
@require_auth
def get_twin_profile():
    user_id = g.user_id
    result = DigitalTwinLearningService.get_learned_profile(user_id)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/digital-twin/rebuild", methods=["POST"])
@require_auth
def rebuild_twin_profile():
    user_id = g.user_id
    result = DigitalTwinLearningService.rebuild_learned_profile(user_id)
    return jsonify(result), 200


@ai_intelligence_bp.route("/digital-twin/reset", methods=["POST"])
@require_auth
def reset_twin_profile():
    user_id = g.user_id
    result = DigitalTwinLearningService.reset_learned_profile(user_id)
    return jsonify(result), 200


@ai_intelligence_bp.route("/coach/weekly", methods=["POST"])
@require_auth
def coach_weekly():
    user_id = g.user_id
    data = request.get_json(silent=True) or {}
    persist = data.get("persist", True)
    result = WeeklyAICoachService.generate_weekly_report(user_id, persist=persist)
    return jsonify({"success": True, "data": result}), 200


@ai_intelligence_bp.route("/accountability/chat", methods=["POST"])
@require_auth
def accountability_chat():
    user_id = g.user_id
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    history = data.get("history", [])
    result = AccountabilityPartnerService.chat(user_id, message, history)
    return jsonify({"success": True, "data": result}), 200
