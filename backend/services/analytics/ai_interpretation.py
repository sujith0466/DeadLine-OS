"""
DeadlineOS — Analytics AI Interpretation Service (Phase 7 Milestone 10)
=======================================================================
Provides grounded, advisory natural language interpretation of computed
analytics metrics using the Phase 6 AI Provider Abstraction (OpenRouter Primary ->
Gemini Fallback -> Deterministic Baseline).
Strictly advisory: never queries database directly or mutates application state.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.safety import AISafety
from services.analytics.daily_score import DailyScoreService
from services.analytics.trends import TrendsAnalyticsService
from services.analytics.habit_health import HabitHealthService
from services.analytics.goal_progress import GoalProgressService

logger = logging.getLogger(__name__)

INTERPRETATION_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "key_insights": {
            "type": "array",
            "items": {"type": "string"}
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"}
        },
        "growth_areas": {
            "type": "array",
            "items": {"type": "string"}
        },
        "actionable_takeaway": {"type": "string"},
        "confidence_score": {"type": "integer"}
    },
    "required": ["headline", "key_insights", "strengths", "growth_areas", "actionable_takeaway"]
}


class AnalyticsAIInterpretationService:
    """Explains deterministic analytics facts using bounded AI inference."""

    @staticmethod
    def interpret_analytics(
        user_id: str,
        days: int = 7,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        ai_provider = provider or get_default_ai_provider()

        # 1. Gather authoritative pre-computed analytics facts
        daily_score = DailyScoreService.calculate_daily_score(user_id)
        trends = TrendsAnalyticsService.get_trends(user_id, days=days)
        habits = HabitHealthService.calculate_habit_health(user_id)
        goals = GoalProgressService.calculate_goal_progress(user_id)

        # 2. Minimize & Sanitize Context for Prompt
        sanitized_facts = {
            "timeframe_days": days,
            "today_score": daily_score.get("score"),
            "today_grade": daily_score.get("grade"),
            "overall_completion_rate_pct": trends.get("overall_completion_rate_pct"),
            "total_focus_hours": trends.get("total_focus_hours"),
            "trend_direction": trends.get("trend_direction"),
            "active_habits_count": habits.get("active_habits_count"),
            "habit_health_score": habits.get("overall_health_score"),
            "active_goals_count": goals.get("active_goals_count"),
            "at_risk_goals_count": goals.get("at_risk_goals_count")
        }

        user_prompt = json.dumps(sanitized_facts, indent=2)
        system_prompt = (
            "You are the DeadlineOS Senior Execution & Productivity Analyst. "
            "Analyze the following verified execution facts. Provide an explainable, motivating, "
            "and objective breakdown of execution trends, strengths, and areas requiring focus. "
            "Do NOT make medical/clinical claims. Do NOT invent ungrounded data. "
            "Format strictly as JSON conforming to the requested schema."
        )

        def fallback_fn():
            direction = trends.get("trend_direction", "STABLE")
            comp = trends.get("overall_completion_rate_pct", 100.0)
            return {
                "headline": f"Execution Momentum: {direction.capitalize()} ({comp}% Completion)",
                "key_insights": [
                    f"Overall completion rate over {days} days is {comp}%.",
                    f"Logged {trends.get('total_focus_hours', 0)} total focus hours with {habits.get('overall_health_score', 100)}/100 habit health.",
                    f"Today's execution score is {daily_score.get('score', 100)}/100 ({daily_score.get('grade', 'EXCELLENT')})."
                ],
                "strengths": [
                    "Consistent execution tracking and active session logging.",
                    "Disciplined adherence to daily planned focus windows."
                ],
                "growth_areas": [
                    "Maintain recovery discipline during high workload congestion.",
                    "Ensure approaching milestones are scheduled early."
                ],
                "actionable_takeaway": "Focus on high-priority activities during your morning peak energy window.",
                "confidence_score": 90,
                "_provider": "deterministic_fallback",
                "_fallback_used": True
            }

        response = ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=INTERPRETATION_SCHEMA,
            fallback_fn=fallback_fn
        )

        response["grounding_facts"] = sanitized_facts
        response["is_ai_generated"] = True
        return response
