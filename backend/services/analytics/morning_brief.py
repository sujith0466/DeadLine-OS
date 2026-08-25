"""
DeadlineOS — Morning Brief Service (Phase 7 Milestone 1)
========================================================
Generates a deterministic, explainable daily execution briefing for the current user.
Aggregates today's planned slots, high-priority tasks, active/interrupted sessions,
deadline proximity, recovery recommendations, and schedule conflict signals.
Strictly read-only: does not mutate runtime or domain records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from utils.timezone import utc_now, get_user_timezone, to_user_local
from services.analytics.foundation import AnalyticsTimeWindow
from services.analytics.repository import AnalyticsRepository
from models.task import Task
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.recovery import RecoveryRecord
from models.notification import Notification


class MorningBriefService:
    """Generates deterministic morning execution brief for the user."""

    @staticmethod
    def generate_morning_brief(user_id: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        start_utc, end_utc, resolved_date_str = AnalyticsTimeWindow.get_day_boundaries_utc(user_id, date_str)
        user_tz = get_user_timezone(user_id)
        now_utc = utc_now()
        now_local = to_user_local(now_utc, user_tz)

        # 1. Planned schedule slots for today
        slots = AnalyticsRepository.get_schedule_slots(user_id, start_utc, end_utc)
        planned_count = len(slots)
        high_priority_slots = [s for s in slots if (s.get("priority") or 50) >= 70]

        # 2. Urgent / High-pressure Tasks
        pending_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.status != "done"
        ).order_by(Task.deadline.asc()).all()

        overdue_tasks = [t.to_dict() for t in pending_tasks if t.is_overdue]
        upcoming_24h_tasks = [
            t.to_dict() for t in pending_tasks
            if not t.is_overdue and t.deadline and (t.deadline.replace(tzinfo=timezone.utc) <= now_utc + timedelta(hours=24))
        ]

        total_workload_hours = sum(t.estimated_hours or 1.0 for t in pending_tasks)

        # 3. Active / Interrupted Runtime Sessions
        active_states = (
            RuntimeState.query
            .filter(
                RuntimeState.user_id == user_id,
                RuntimeState.status.in_(["RUNNING", "INTERRUPTED", "PAUSED"])
            )
            .all()
        )
        active_sessions = [
            {
                "runtime_state_id": s.id,
                "entity_type": s.entity_type,
                "entity_id": s.entity_id,
                "status": s.status,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in active_states
        ]

        # 4. Recent / Pending Recovery Actions
        recovery_start = start_utc - timedelta(days=1)
        recent_recovery = AnalyticsRepository.get_recovery_records(user_id, recovery_start, end_utc)

        # 5. Critical / High Notifications
        notifications = (
            Notification.query
            .filter(
                Notification.user_id == user_id,
                Notification.read == False,
                Notification.severity.in_(["critical", "high"])
            )
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )
        notif_items = [n.to_dict() for n in notifications]

        # 6. Schedule Congestion & Execution Risk Assessment
        risk_indicators = []
        if overdue_tasks:
            risk_indicators.append(f"{len(overdue_tasks)} task(s) currently overdue.")
        if len(active_sessions) > 0:
            risk_indicators.append(f"{len(active_sessions)} session(s) currently in {active_sessions[0]['status']} state.")
        if total_workload_hours > 8.0:
            risk_indicators.append(f"High pending workload: {round(total_workload_hours, 1)} estimated hours.")
        if planned_count == 0:
            risk_indicators.append("No activities scheduled for today.")

        # 7. Deterministic Narrative Highlights
        highlights = [
            f"Good morning! You have {planned_count} planned activities scheduled for {resolved_date_str}.",
            f"{len(high_priority_slots)} high-priority items require focus today."
        ]
        if upcoming_24h_tasks:
            highlights.append(f"{len(upcoming_24h_tasks)} task deadline(s) approaching within 24 hours.")
        if not risk_indicators:
            highlights.append("Your schedule is balanced with no immediate overdue risks.")

        return {
            "date": resolved_date_str,
            "timezone": user_tz,
            "planned_activities_count": planned_count,
            "high_priority_count": len(high_priority_slots),
            "planned_slots": slots,
            "high_priority_slots": high_priority_slots,
            "overdue_tasks_count": len(overdue_tasks),
            "overdue_tasks": overdue_tasks,
            "upcoming_24h_tasks": upcoming_24h_tasks,
            "total_pending_workload_hours": round(total_workload_hours, 1),
            "active_interrupted_sessions": active_sessions,
            "recent_recovery_events_count": len(recent_recovery),
            "critical_notifications": notif_items,
            "risk_indicators": risk_indicators,
            "narrative_highlights": highlights,
            "is_ai_generated": False
        }
