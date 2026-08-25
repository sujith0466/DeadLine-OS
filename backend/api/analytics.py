"""
DeadlineOS — Analytics API Blueprint
====================================
Exposes all analytics endpoints:
- Executive Scorecard & Agent Telemetry (overview, briefing, productivity, etc.)
- Phase 7 Execution Analytics (morning-brief, evening-reflection, daily-score,
  habit-health, goal-progress, deadline-heatmap, timeline, sessions, trends, ai/interpret).
"""

import logging
from flask import Blueprint, jsonify, request, g
from utils.auth import require_auth
from services.analytics_service import AnalyticsService

# Phase 7 Services
from services.analytics.morning_brief import MorningBriefService
from services.analytics.evening_reflection import EveningReflectionService
from services.analytics.daily_score import DailyScoreService
from services.analytics.habit_health import HabitHealthService
from services.analytics.goal_progress import GoalProgressService
from services.analytics.deadline_heatmap import DeadlineHeatmapService
from services.analytics.timeline import TimelineAnalyticsService
from services.analytics.session_analytics import SessionAnalyticsService
from services.analytics.trends import TrendsAnalyticsService
from services.analytics.ai_interpretation import AnalyticsAIInterpretationService

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics_bp", __name__)


# ── Executive Scorecard & Agent Intelligence Endpoints ─────────────────────────

@analytics_bp.route("/analytics/overview", methods=["GET"])
@require_auth
def get_overview():
    return jsonify({"status": "success", "data": AnalyticsService.get_overview()}), 200


@analytics_bp.route("/analytics/productivity", methods=["GET"])
@require_auth
def get_productivity():
    return (
        jsonify(
            {"status": "success", "data": AnalyticsService.get_productivity_trends()}
        ),
        200,
    )


@analytics_bp.route("/analytics/contributions", methods=["GET"])
@require_auth
def get_contributions():
    return (
        jsonify(
            {"status": "success", "data": AnalyticsService.get_agent_contributions()}
        ),
        200,
    )


@analytics_bp.route("/analytics/intelligence", methods=["GET"])
@require_auth
def get_intelligence():
    return (
        jsonify(
            {"status": "success", "data": AnalyticsService.get_intelligence_reports()}
        ),
        200,
    )


@analytics_bp.route("/analytics/heatmap", methods=["GET"])
@require_auth
def get_heatmap():
    return (
        jsonify(
            {"status": "success", "data": AnalyticsService.get_productivity_heatmap()}
        ),
        200,
    )


@analytics_bp.route("/analytics/briefing", methods=["GET"])
@require_auth
def get_briefing():
    return (
        jsonify(
            {
                "status": "success",
                "data": AnalyticsService.generate_chief_of_staff_briefing(),
            }
        ),
        200,
    )


@analytics_bp.route("/analytics/voice", methods=["GET"])
@require_auth
def get_voice_analytics():
    return (
        jsonify(
            {
                "status": "success",
                "data": AnalyticsService.get_agent_metrics("Voice Agent"),
            }
        ),
        200,
    )


@analytics_bp.route("/analytics/vision", methods=["GET"])
@require_auth
def get_vision_analytics():
    return (
        jsonify(
            {
                "status": "success",
                "data": AnalyticsService.get_agent_metrics("Vision Agent"),
            }
        ),
        200,
    )


@analytics_bp.route("/analytics/documents", methods=["GET"])
@require_auth
def get_documents_analytics():
    return (
        jsonify(
            {
                "status": "success",
                "data": AnalyticsService.get_agent_metrics("Document Agent"),
            }
        ),
        200,
    )


@analytics_bp.route("/analytics/interventions", methods=["GET"])
@require_auth
def get_interventions_analytics():
    return (
        jsonify(
            {"status": "success", "data": AnalyticsService.get_intervention_metrics()}
        ),
        200,
    )


@analytics_bp.route("/analytics/twin-accuracy", methods=["GET"])
@require_auth
def get_twin_accuracy():
    return (
        jsonify({"status": "success", "data": AnalyticsService.get_twin_accuracy()}),
        200,
    )


@analytics_bp.route("/analytics/insights", methods=["GET"])
@require_auth
def get_insights():
    return jsonify({"status": "success", "data": AnalyticsService.get_insights()}), 200


# ── Phase 7: Deterministic Analytics & Insights Endpoints ─────────────────────

@analytics_bp.route("/analytics/morning-brief", methods=["GET"])
@require_auth
def get_morning_brief():
    """Returns deterministic morning briefing for today (or requested date)."""
    user_id = g.user_id
    date_str = request.args.get("date")  # YYYY-MM-DD (optional)
    brief = MorningBriefService.generate_morning_brief(user_id, date_str)
    return jsonify({"success": True, "data": brief}), 200


@analytics_bp.route("/analytics/evening-reflection", methods=["GET"])
@require_auth
def get_evening_reflection():
    """Returns deterministic evening retrospective for today (or requested date)."""
    user_id = g.user_id
    date_str = request.args.get("date")  # YYYY-MM-DD (optional)
    reflection = EveningReflectionService.generate_evening_reflection(user_id, date_str)
    return jsonify({"success": True, "data": reflection}), 200


@analytics_bp.route("/analytics/daily-score", methods=["GET"])
@require_auth
def get_daily_score():
    """Returns deterministic daily execution score for today (or requested date)."""
    user_id = g.user_id
    date_str = request.args.get("date")  # YYYY-MM-DD (optional)
    score = DailyScoreService.calculate_daily_score(user_id, date_str)
    return jsonify({"success": True, "data": score}), 200


@analytics_bp.route("/analytics/habit-health", methods=["GET"])
@require_auth
def get_habit_health():
    """Returns deterministic habit health scores and streak analytics."""
    user_id = g.user_id
    health_data = HabitHealthService.calculate_habit_health(user_id)
    return jsonify({"success": True, "data": health_data}), 200


@analytics_bp.route("/analytics/goal-progress", methods=["GET"])
@require_auth
def get_goal_progress():
    """Returns deterministic goal progress and execution risk intelligence."""
    user_id = g.user_id
    progress_data = GoalProgressService.calculate_goal_progress(user_id)
    return jsonify({"success": True, "data": progress_data}), 200


@analytics_bp.route("/analytics/deadline-heatmap", methods=["GET"])
@require_auth
def get_deadline_heatmap():
    """Returns deterministic deadline density and execution heatmap."""
    user_id = g.user_id
    days = int(request.args.get("days", 30))
    heatmap_data = DeadlineHeatmapService.generate_deadline_heatmap(user_id, days=days)
    return jsonify({"success": True, "data": heatmap_data}), 200


@analytics_bp.route("/analytics/timeline", methods=["GET"])
@require_auth
def get_timeline():
    """Returns normalized chronological execution timeline events."""
    user_id = g.user_id
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    limit = int(request.args.get("limit", 50))
    timeline_data = TimelineAnalyticsService.get_timeline(user_id, start_date=start_date, end_date=end_date, limit=limit)
    return jsonify({"success": True, "data": timeline_data}), 200


@analytics_bp.route("/analytics/sessions", methods=["GET"])
@require_auth
def get_sessions_analytics():
    """Returns aggregated runtime session performance analytics."""
    user_id = g.user_id
    days = int(request.args.get("days", 30))
    session_data = SessionAnalyticsService.get_session_analytics(user_id, days=days)
    return jsonify({"success": True, "data": session_data}), 200


@analytics_bp.route("/analytics/trends", methods=["GET"])
@require_auth
def get_trends_analytics():
    """Returns multi-day completion and recovery trends across 7/14/30/90 days."""
    user_id = g.user_id
    days = int(request.args.get("days", 30))
    trends_data = TrendsAnalyticsService.get_trends(user_id, days=days)
    return jsonify({"success": True, "data": trends_data}), 200


@analytics_bp.route("/analytics/ai/interpret", methods=["POST"])
@require_auth
def interpret_analytics():
    """Returns AI-guided interpretation of pre-computed execution analytics."""
    user_id = g.user_id
    payload = request.get_json(silent=True) or {}
    days = int(payload.get("days", 7))
    interpretation = AnalyticsAIInterpretationService.interpret_analytics(user_id, days=days)
    return jsonify({"success": True, "data": interpretation}), 200
