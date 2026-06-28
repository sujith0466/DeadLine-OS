import logging
from flask import Blueprint, jsonify
from services.analytics_service import AnalyticsService
from utils.auth import require_auth

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics/overview", methods=["GET"])
@require_auth
def get_overview():
    return jsonify({"status": "success", "data": AnalyticsService.get_overview()}), 200

@analytics_bp.route("/analytics/productivity", methods=["GET"])
@require_auth
def get_productivity():
    return jsonify({"status": "success", "data": AnalyticsService.get_productivity_trends()}), 200

@analytics_bp.route("/analytics/contributions", methods=["GET"])
@require_auth
def get_contributions():
    return jsonify({"status": "success", "data": AnalyticsService.get_agent_contributions()}), 200

@analytics_bp.route("/analytics/intelligence", methods=["GET"])
@require_auth
def get_intelligence():
    return jsonify({"status": "success", "data": AnalyticsService.get_intelligence_reports()}), 200

@analytics_bp.route("/analytics/heatmap", methods=["GET"])
@require_auth
def get_heatmap():
    return jsonify({"status": "success", "data": AnalyticsService.get_productivity_heatmap()}), 200

@analytics_bp.route("/analytics/briefing", methods=["GET"])
@require_auth
def get_briefing():
    return jsonify({"status": "success", "data": AnalyticsService.generate_chief_of_staff_briefing()}), 200

@analytics_bp.route("/analytics/voice", methods=["GET"])
@require_auth
def get_voice_analytics():
    return jsonify({"status": "success", "data": AnalyticsService.get_agent_metrics("Voice Agent")}), 200

@analytics_bp.route("/analytics/vision", methods=["GET"])
@require_auth
def get_vision_analytics():
    return jsonify({"status": "success", "data": AnalyticsService.get_agent_metrics("Vision Agent")}), 200

@analytics_bp.route("/analytics/documents", methods=["GET"])
@require_auth
def get_documents_analytics():
    return jsonify({"status": "success", "data": AnalyticsService.get_agent_metrics("Document Agent")}), 200

@analytics_bp.route("/analytics/interventions", methods=["GET"])
@require_auth
def get_interventions_analytics():
    return jsonify({"status": "success", "data": AnalyticsService.get_intervention_metrics()}), 200

@analytics_bp.route("/analytics/twin-accuracy", methods=["GET"])
@require_auth
def get_twin_accuracy():
    return jsonify({"status": "success", "data": AnalyticsService.get_twin_accuracy()}), 200

@analytics_bp.route("/analytics/insights", methods=["GET"])
@require_auth
def get_insights():
    return jsonify({"status": "success", "data": AnalyticsService.get_insights()}), 200
