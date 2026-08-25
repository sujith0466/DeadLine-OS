"""
DeadlineOS — Evening Reflection Service (Phase 7 Milestone 2)
=============================================================
Generates deterministic end-of-day execution retrospective for the user.
Calculates planned vs completed activities, focus time, paused duration,
recovery actions, missed items, and schedule adherence.
Strictly read-only: does not mutate runtime or domain state.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import utc_now, get_user_timezone, to_user_local
from services.analytics.foundation import AnalyticsTimeWindow
from services.analytics.repository import AnalyticsRepository
from models.task import Task
from models.schedule import ScheduleSlot
from models.recovery import RecoveryRecord, RecoveryActionType


class EveningReflectionService:
    """Computes deterministic evening retrospective execution metrics."""

    @staticmethod
    def generate_evening_reflection(user_id: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        start_utc, end_utc, resolved_date_str = AnalyticsTimeWindow.get_day_boundaries_utc(user_id, date_str)
        user_tz = get_user_timezone(user_id)

        # 1. Planned and completed slots for the day
        slots = AnalyticsRepository.get_schedule_slots(user_id, start_utc, end_utc)
        total_planned_slots = len(slots)
        completed_slots = [s for s in slots if s.get("status") in ["COMPLETED", "done"]]
        cancelled_or_missed = [s for s in slots if s.get("status") in ["CANCELLED", "MISSED"]]

        # 2. Runtime execution sessions
        sessions = AnalyticsRepository.get_sessions(user_id, start_utc, end_utc)
        total_focus_sec = sum(s.get("actual_duration_sec", 0) for s in sessions)
        total_paused_sec = sum(s.get("paused_duration_sec", 0) for s in sessions)
        total_planned_sec = sum(s.get("planned_duration_sec", 0) for s in sessions)
        interrupted_sessions = [s for s in sessions if s.get("status") == "INTERRUPTED" or s.get("paused_duration_sec", 0) > 600]

        # 3. Recovery actions executed today
        recoveries = AnalyticsRepository.get_recovery_records(user_id, start_utc, end_utc)
        skipped_count = sum(1 for r in recoveries if r.get("action_type") == RecoveryActionType.SKIP)
        rescheduled_count = sum(1 for r in recoveries if r.get("action_type") == RecoveryActionType.RESCHEDULE)

        # 4. Computed Ratios & Adherence
        slot_completion_rate = round((len(completed_slots) / total_planned_slots * 100), 1) if total_planned_slots > 0 else 100.0
        
        # Adherence score based on planned vs actual duration ratio and completed ratio
        if total_planned_sec > 0:
            duration_adherence = min(100.0, round((total_focus_sec / total_planned_sec * 100), 1))
        else:
            duration_adherence = 100.0 if total_focus_sec > 0 else 0.0

        adherence_pct = round((slot_completion_rate * 0.6 + duration_adherence * 0.4), 1)

        # 5. Deterministic Qualitative Highlights
        highlights = [
            f"You logged {round(total_focus_sec / 60, 1)} minutes of dedicated focus time today.",
            f"Completed {len(completed_slots)} out of {total_planned_slots} planned activities ({slot_completion_rate}% completion)."
        ]
        if skipped_count > 0:
            highlights.append(f"Recorded {skipped_count} intentional skip/recovery adjustments.")
        if len(interrupted_sessions) > 0:
            highlights.append(f"{len(interrupted_sessions)} session(s) encountered pauses or interruptions.")
        if adherence_pct >= 80:
            highlights.append("Strong execution day with high schedule adherence.")
        elif adherence_pct >= 50:
            highlights.append("Moderate execution day. Solid progress achieved on key commitments.")
        else:
            highlights.append("Challenging execution day. Consider reviewing workload capacity tomorrow.")

        return {
            "date": resolved_date_str,
            "timezone": user_tz,
            "total_planned_activities": total_planned_slots,
            "completed_activities_count": len(completed_slots),
            "missed_activities_count": len(cancelled_or_missed),
            "skipped_activities_count": skipped_count,
            "rescheduled_activities_count": rescheduled_count,
            "total_focus_duration_minutes": round(total_focus_sec / 60, 1),
            "total_paused_duration_minutes": round(total_paused_sec / 60, 1),
            "total_planned_duration_minutes": round(total_planned_sec / 60, 1),
            "completion_rate_pct": slot_completion_rate,
            "schedule_adherence_pct": adherence_pct,
            "sessions_count": len(sessions),
            "interrupted_sessions_count": len(interrupted_sessions),
            "recovery_records": recoveries,
            "narrative_highlights": highlights,
            "is_ai_generated": False
        }
