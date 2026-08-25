"""
DeadlineOS — Timeline Analytics Service (Phase 7 Milestone 7)
=============================================================
Aggregates and normalizes historical execution events across runtime sessions,
schedule slots, recovery actions, and notifications into a unified,
chronologically ordered timeline.
Strictly read-only: does not mutate runtime or domain records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import get_user_timezone, to_user_local
from services.analytics.foundation import AnalyticsTimeWindow
from services.analytics.repository import AnalyticsRepository


class TimelineAnalyticsService:
    """Computes unified, normalized execution timeline events."""

    @staticmethod
    def get_timeline(
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        user_tz = get_user_timezone(user_id)

        if start_date and end_date:
            start_utc, end_utc = AnalyticsTimeWindow.get_range_boundaries_utc(user_id, start_date, end_date)
        else:
            start_utc, end_utc, _ = AnalyticsTimeWindow.get_n_days_range_utc(user_id, days=7)

        events: List[Dict[str, Any]] = []

        # 1. Runtime Sessions
        sessions = AnalyticsRepository.get_sessions(user_id, start_utc, end_utc)
        for s in sessions:
            if s.get("started_at"):
                dt_utc = datetime.fromisoformat(s["started_at"])
                dt_local = to_user_local(dt_utc, user_tz)
                events.append({
                    "id": f"sess-{s['session_id']}-start",
                    "event_type": "SESSION_STARTED",
                    "entity_type": s.get("entity_type", "TASK"),
                    "entity_id": s.get("entity_id"),
                    "title": f"Started {s.get('entity_type', 'Activity')} session",
                    "timestamp_utc": dt_utc.isoformat(),
                    "timestamp_local": dt_local.isoformat(),
                    "details": {
                        "planned_duration_minutes": round(s.get("planned_duration_sec", 0) / 60, 1),
                        "status": s.get("status")
                    },
                    "severity": "info"
                })

            if s.get("ended_at"):
                dt_utc = datetime.fromisoformat(s["ended_at"])
                dt_local = to_user_local(dt_utc, user_tz)
                events.append({
                    "id": f"sess-{s['session_id']}-end",
                    "event_type": "SESSION_COMPLETED",
                    "entity_type": s.get("entity_type", "TASK"),
                    "entity_id": s.get("entity_id"),
                    "title": f"Completed {s.get('entity_type', 'Activity')} session",
                    "timestamp_utc": dt_utc.isoformat(),
                    "timestamp_local": dt_local.isoformat(),
                    "details": {
                        "actual_duration_minutes": round(s.get("actual_duration_sec", 0) / 60, 1),
                        "paused_duration_minutes": round(s.get("paused_duration_sec", 0) / 60, 1),
                        "completion_source": s.get("completion_source")
                    },
                    "severity": "success"
                })

        # 2. Recovery Records
        recoveries = AnalyticsRepository.get_recovery_records(user_id, start_utc, end_utc)
        for r in recoveries:
            if r.get("created_at"):
                dt_utc = datetime.fromisoformat(r["created_at"])
                dt_local = to_user_local(dt_utc, user_tz)
                events.append({
                    "id": f"rec-{r['id']}",
                    "event_type": f"RECOVERY_{r.get('action_type')}",
                    "entity_type": r.get("entity_type", "SCHEDULE"),
                    "entity_id": r.get("entity_id"),
                    "title": f"Recovery Action: {r.get('action_type')}",
                    "timestamp_utc": dt_utc.isoformat(),
                    "timestamp_local": dt_local.isoformat(),
                    "details": r.get("details", {}),
                    "severity": "warning"
                })

        # 3. Critical / High Notifications
        notifications = AnalyticsRepository.get_notifications(user_id, start_utc, end_utc)
        for n in notifications:
            if n.get("created_at") and n.get("severity") in ["critical", "high"]:
                dt_utc = datetime.fromisoformat(n["created_at"])
                dt_local = to_user_local(dt_utc, user_tz)
                events.append({
                    "id": f"notif-{n['id']}",
                    "event_type": "NOTIFICATION_ALERT",
                    "entity_type": n.get("entity_type", "SYSTEM"),
                    "entity_id": n.get("entity_id"),
                    "title": n.get("title", "Alert"),
                    "timestamp_utc": dt_utc.isoformat(),
                    "timestamp_local": dt_local.isoformat(),
                    "details": {"description": n.get("description"), "severity": n.get("severity")},
                    "severity": n.get("severity", "info")
                })

        # Sort descending by timestamp
        events.sort(key=lambda x: x["timestamp_utc"], reverse=True)
        paginated = events[:limit]

        return {
            "timezone": user_tz,
            "total_events_count": len(events),
            "returned_count": len(paginated),
            "events": paginated,
            "is_ai_generated": False
        }
