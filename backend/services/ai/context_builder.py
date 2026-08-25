"""
DeadlineOS — AI Context & Evidence Builder
==========================================
Constructs sanitized, privacy-minimized context dictionaries for AI reasoning.
Enforces the Data Privacy Contract by stripping authentication tokens, passwords,
and raw database internals before model inference.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.task import Task
from models.goal import Goal, Habit
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.recovery import RecoveryRecord
from models.user_settings import UserSettings
from services.recovery.service import RecoveryService
from services.ai.safety import AISafety
from utils.timezone import utc_now, to_user_local, get_user_timezone


class AIContextBuilder:
    """Builder for constructing sanitized, explainable context payloads."""

    @classmethod
    def get_task_context(cls, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extracts minimal task execution properties."""
        tasks = Task.query.filter_by(user_id=user_id).filter(
            Task.status.in_(["pending", "in_progress", "overdue"])
        ).order_by(Task.deadline.asc()).limit(limit).all()

        results = []
        for t in tasks:
            results.append({
                "id": t.id,
                "title": AISafety.sanitize_user_input(t.title),
                "status": t.status,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "estimated_hours": t.estimated_hours or 1.0,
                "actual_hours": t.actual_hours or 0.0,
                "priority_score": getattr(t, "priority_score", 50)
            })
        return results

    @classmethod
    def get_schedule_context(cls, user_id: str, days: int = 1) -> List[Dict[str, Any]]:
        """Extracts minimal upcoming schedule slot properties."""
        now = utc_now()
        end_window = now + timedelta(days=days)
        slots = ScheduleSlot.query.filter(
            ScheduleSlot.user_id == user_id,
            ScheduleSlot.start_time >= now - timedelta(hours=2),
            ScheduleSlot.start_time <= end_window
        ).order_by(ScheduleSlot.start_time.asc()).all()

        results = []
        for s in slots:
            results.append({
                "id": s.id,
                "entity_id": s.entity_id,
                "entity_type": s.entity_type,
                "task_title": AISafety.sanitize_user_input(s.task_title or ""),
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "status": s.status,
                "priority_score": s.priority or 50
            })
        return results

    @classmethod
    def get_runtime_context(cls, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Extracts recent runtime execution telemetry."""
        states = RuntimeState.query.filter_by(user_id=user_id).order_by(
            RuntimeState.updated_at.desc()
        ).limit(limit).all()

        results = []
        for st in states:
            sessions = RuntimeSession.query.filter_by(runtime_state_id=st.id).order_by(
                RuntimeSession.started_at.desc()
            ).limit(3).all()

            sess_list = []
            for s in sessions:
                sess_list.append({
                    "id": s.id,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                    "planned_duration_sec": s.planned_duration_sec,
                    "paused_duration_sec": s.paused_duration_sec,
                    "completion_source": s.completion_source
                })

            results.append({
                "id": st.id,
                "entity_id": st.entity_id,
                "entity_type": st.entity_type,
                "status": st.status,
                "sessions": sess_list
            })
        return results

    @classmethod
    def get_recovery_context(cls, user_id: str) -> Dict[str, Any]:
        """Extracts user recovery state including Vacation and Emergency flags."""
        settings = UserSettings.get_or_create(user_id)
        planner = settings.planner or {}

        recent_records = RecoveryRecord.query.filter_by(user_id=user_id).order_by(
            RecoveryRecord.created_at.desc()
        ).limit(5).all()

        return {
            "is_vacation_mode": RecoveryService.is_user_on_vacation(user_id),
            "is_emergency_mode": RecoveryService.is_emergency_mode_active(user_id),
            "recent_actions": [r.to_dict() for r in recent_records]
        }

    @classmethod
    def get_user_preferences_context(cls, user_id: str) -> Dict[str, Any]:
        """Extracts configured notification, planner, and energy preferences."""
        settings = UserSettings.get_or_create(user_id)
        planner = settings.planner or {}
        notifs = settings.notifications or {}
        ai_pref = settings.ai or {}

        return {
            "timezone": get_user_timezone(user_id),
            "quiet_hours": notifs.get("quiet_hours", {"enabled": True, "start": "22:00", "end": "08:00"}),
            "energy_preferences": planner.get("energy_preferences", {
                "peak_focus_start": "09:00",
                "peak_focus_end": "12:00",
                "low_energy_start": "14:00",
                "low_energy_end": "16:00"
            }),
            "learned_profile": ai_pref.get("learned_profile", {})
        }

    @classmethod
    def build_unified_inference_context(cls, user_id: str) -> Dict[str, Any]:
        """Builds a complete, sanitized snapshot for multi-factor AI reasoning."""
        return {
            "tasks": cls.get_task_context(user_id),
            "schedule": cls.get_schedule_context(user_id),
            "runtime": cls.get_runtime_context(user_id),
            "recovery": cls.get_recovery_context(user_id),
            "preferences": cls.get_user_preferences_context(user_id),
            "generated_at": utc_now().isoformat()
        }
