"""
DeadlineOS — Habit Health Service (Phase 7 Milestone 4)
=======================================================
Calculates deterministic habit consistency metrics, streak retention rates,
and long-term momentum indicators without clinical/medical claims.
Strictly read-only: does not mutate habit or domain records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import get_user_timezone
from services.analytics.foundation import AnalyticsTimeWindow
from models.goal import Habit, HabitLog


class HabitHealthService:
    """Computes explainable habit consistency & health metrics."""

    @staticmethod
    def calculate_habit_health(user_id: str) -> Dict[str, Any]:
        habits = Habit.query.filter(Habit.user_id == user_id, Habit.archived == False).all()
        user_tz = get_user_timezone(user_id)

        if not habits:
            return {
                "overall_health_score": 100,
                "overall_grade": "NO_HABITS",
                "active_habits_count": 0,
                "habits": [],
                "summary": "No active habits configured.",
                "is_ai_generated": False
            }

        habit_results = []
        total_momentum = 0

        for h in habits:
            logs = HabitLog.query.filter(HabitLog.habit_id == h.id).order_by(HabitLog.date.desc()).all()
            total_logs = len(logs)
            completed_logs = sum(1 for l in logs if l.completed)

            # Consistency score
            if total_logs > 0:
                consistency_pct = round((completed_logs / total_logs) * 100.0, 1)
            else:
                consistency_pct = float(h.completion_rate or 80.0)

            # Streak multiplier: reward streak up to 30 days
            streak_score = min(100.0, (h.current_streak or 0) * 10.0)
            
            # Habit Health = 50% consistency + 30% momentum + 20% streak score
            health_raw = (consistency_pct * 0.5) + ((h.momentum_score or 50) * 0.3) + (streak_score * 0.2)
            habit_health_score = int(round(min(100, max(0, health_raw))))
            total_momentum += habit_health_score

            if habit_health_score >= 80:
                trend = "STRONG_POSITIVE"
            elif habit_health_score >= 50:
                trend = "STABLE"
            else:
                trend = "NEEDS_ATTENTION"

            habit_results.append({
                "habit_id": h.id,
                "name": h.name,
                "category": h.category or "General",
                "frequency": h.frequency or "Daily",
                "current_streak": h.current_streak or 0,
                "longest_streak": h.longest_streak or 0,
                "consistency_percentage": consistency_pct,
                "momentum_score": h.momentum_score or 0,
                "health_score": habit_health_score,
                "trend": trend,
                "total_checkins": completed_logs,
                "last_checkin_date": h.last_checkin_date
            })

        avg_health = int(round(total_momentum / len(habits)))
        if avg_health >= 80:
            overall_grade = "OPTIMAL"
        elif avg_health >= 60:
            overall_grade = "BUILDING"
        else:
            overall_grade = "REBUILDING"

        return {
            "overall_health_score": avg_health,
            "overall_grade": overall_grade,
            "active_habits_count": len(habits),
            "habits": habit_results,
            "summary": f"Tracking {len(habits)} habits with an average execution health score of {avg_health}/100.",
            "is_ai_generated": False
        }
