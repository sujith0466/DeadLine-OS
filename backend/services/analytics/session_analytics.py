"""
DeadlineOS — Session Analytics Service (Phase 7 Milestone 8)
============================================================
Calculates aggregated runtime session metrics: total focus time,
average session duration, pause ratio, planned vs actual duration,
and activity distribution across time.
Strictly read-only: does not mutate runtime state or session records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import get_user_timezone, to_user_local
from services.analytics.foundation import AnalyticsTimeWindow
from services.analytics.repository import AnalyticsRepository


class SessionAnalyticsService:
    """Computes comprehensive runtime session performance metrics."""

    @staticmethod
    def get_session_analytics(user_id: str, days: int = 30) -> Dict[str, Any]:
        start_utc, end_utc, _ = AnalyticsTimeWindow.get_n_days_range_utc(user_id, days=days)
        user_tz = get_user_timezone(user_id)

        sessions = AnalyticsRepository.get_sessions(user_id, start_utc, end_utc)
        total_sessions = len(sessions)

        if total_sessions == 0:
            return {
                "days_analyzed": days,
                "timezone": user_tz,
                "total_sessions": 0,
                "total_focus_hours": 0.0,
                "avg_session_minutes": 0.0,
                "total_paused_minutes": 0.0,
                "pause_rate_pct": 0.0,
                "duration_fidelity_pct": 100.0,
                "entity_distribution": {},
                "completion_sources": {},
                "summary": f"No runtime sessions found in the last {days} days.",
                "is_ai_generated": False
            }

        total_focus_sec = sum(s.get("actual_duration_sec", 0) for s in sessions)
        total_paused_sec = sum(s.get("paused_duration_sec", 0) for s in sessions)
        total_planned_sec = sum(s.get("planned_duration_sec", 0) for s in sessions)

        avg_session_min = round((total_focus_sec / total_sessions) / 60.0, 1)

        # Pause rate (paused time vs gross time)
        gross_time = total_focus_sec + total_paused_sec
        pause_rate = round((total_paused_sec / gross_time * 100.0), 1) if gross_time > 0 else 0.0

        # Duration fidelity (actual focus vs planned)
        if total_planned_sec > 0:
            fidelity = round(min(100.0, (total_focus_sec / total_planned_sec) * 100.0), 1)
        else:
            fidelity = 100.0

        # Activity Entity Distribution
        entity_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        for s in sessions:
            etype = s.get("entity_type", "TASK")
            entity_counts[etype] = entity_counts.get(etype, 0) + 1

            src = s.get("completion_source") or "Unknown"
            source_counts[src] = source_counts.get(src, 0) + 1

        return {
            "days_analyzed": days,
            "timezone": user_tz,
            "total_sessions": total_sessions,
            "total_focus_hours": round(total_focus_sec / 3600.0, 2),
            "total_focus_minutes": round(total_focus_sec / 60.0, 1),
            "avg_session_minutes": avg_session_min,
            "total_paused_minutes": round(total_paused_sec / 60.0, 1),
            "pause_rate_pct": pause_rate,
            "duration_fidelity_pct": fidelity,
            "entity_distribution": entity_counts,
            "completion_sources": source_counts,
            "summary": f"Analyzed {total_sessions} sessions totaling {round(total_focus_sec / 3600.0, 1)} focus hours.",
            "is_ai_generated": False
        }
