"""
DeadlineOS — Daily Score Service (Phase 7 Milestone 3)
======================================================
Computes deterministic, fully explainable 0-100 execution scores based on:
  1. Completion Rate (35%)
  2. Schedule Adherence (25%)
  3. Focus Time Depth (20%)
  4. Recovery Discipline (10%)
  5. Deadline Pressure Management (10%)
Strictly read-only: does not mutate runtime or domain records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import get_user_timezone
from services.analytics.foundation import AnalyticsTimeWindow
from services.analytics.repository import AnalyticsRepository
from models.task import Task


class DailyScoreService:
    """Computes explainable daily execution productivity score."""

    @staticmethod
    def calculate_daily_score(user_id: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        start_utc, end_utc, resolved_date_str = AnalyticsTimeWindow.get_day_boundaries_utc(user_id, date_str)
        user_tz = get_user_timezone(user_id)

        # 1. Gather component raw data
        slots = AnalyticsRepository.get_schedule_slots(user_id, start_utc, end_utc)
        sessions = AnalyticsRepository.get_sessions(user_id, start_utc, end_utc)
        recoveries = AnalyticsRepository.get_recovery_records(user_id, start_utc, end_utc)
        tasks = Task.query.filter(Task.user_id == user_id).all()

        total_slots = len(slots)
        completed_slots = [s for s in slots if s.get("status") in ["COMPLETED", "done"]]
        
        total_focus_sec = sum(s.get("actual_duration_sec", 0) for s in sessions)
        total_planned_sec = sum(s.get("planned_duration_sec", 0) for s in sessions)
        total_paused_sec = sum(s.get("paused_duration_sec", 0) for s in sessions)

        overdue_count = sum(1 for t in tasks if t.is_overdue)

        # 2. Compute Component Sub-Scores (0 to 100)
        
        # A. Completion Rate (Weight: 35%)
        if total_slots > 0:
            raw_completion = (len(completed_slots) / total_slots) * 100.0
        else:
            raw_completion = 85.0 if len(sessions) > 0 else 70.0
        score_completion = round(min(100.0, max(0.0, raw_completion)), 1)

        # B. Schedule Adherence (Weight: 25%)
        if total_planned_sec > 0:
            duration_ratio = (total_focus_sec / total_planned_sec) * 100.0
            score_adherence = round(min(100.0, max(0.0, duration_ratio)), 1)
        else:
            score_adherence = 90.0 if total_focus_sec > 0 else 70.0

        # C. Focus Depth (Weight: 20%) — benchmark: 4 hours (14400s) for full 100
        focus_benchmark_sec = 14400.0
        score_focus = round(min(100.0, (total_focus_sec / focus_benchmark_sec) * 100.0), 1)

        # D. Recovery Discipline (Weight: 10%)
        # Penalizes unmanaged skips/pauses while rewarding intentional recovery records
        pause_penalty = min(30.0, (total_paused_sec / 1800.0) * 10.0)
        score_recovery = round(max(50.0, 100.0 - pause_penalty), 1)

        # E. Deadline Pressure Management (Weight: 10%)
        score_deadline = 100.0 if overdue_count == 0 else max(20.0, 100.0 - (overdue_count * 20.0))

        # 3. Weighted Final Score
        final_score_raw = (
            score_completion * 0.35 +
            score_adherence * 0.25 +
            score_focus * 0.20 +
            score_recovery * 0.10 +
            score_deadline * 0.10
        )
        final_score = int(round(min(100, max(0, final_score_raw))))

        # 4. Grade & Explanations
        if final_score >= 85:
            grade = "EXCELLENT"
        elif final_score >= 70:
            grade = "STRONG"
        elif final_score >= 50:
            grade = "FAIR"
        else:
            grade = "NEEDS_FOCUS"

        explanations = [
            f"Completion component ({score_completion}/100, 35% weight): {len(completed_slots)}/{total_slots} planned activities completed.",
            f"Adherence component ({score_adherence}/100, 25% weight): execution fidelity aligned with scheduled durations.",
            f"Focus depth ({score_focus}/100, 20% weight): {round(total_focus_sec / 3600.0, 1)} hours of deep work logged.",
            f"Recovery discipline ({score_recovery}/100, 10% weight): {len(recoveries)} recovery events recorded.",
            f"Deadline health ({score_deadline}/100, 10% weight): {overdue_count} overdue task(s) active."
        ]

        return {
            "date": resolved_date_str,
            "timezone": user_tz,
            "score": final_score,
            "grade": grade,
            "data_coverage": total_slots > 0 or len(sessions) > 0,
            "components": {
                "completion_rate": {"score": score_completion, "weight": 0.35, "raw_pct": score_completion},
                "schedule_adherence": {"score": score_adherence, "weight": 0.25, "raw_pct": score_adherence},
                "focus_depth": {"score": score_focus, "weight": 0.20, "focus_hours": round(total_focus_sec / 3600.0, 1)},
                "recovery_discipline": {"score": score_recovery, "weight": 0.10, "paused_minutes": round(total_paused_sec / 60.0, 1)},
                "deadline_pressure": {"score": score_deadline, "weight": 0.10, "overdue_tasks": overdue_count}
            },
            "explanation": explanations,
            "is_ai_generated": False
        }
