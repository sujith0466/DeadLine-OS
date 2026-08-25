"""
DeadlineOS — Digital Twin Learning Service
==========================================
Computes bounded, learned behavioral parameters (velocity multiplier, typical duration,
pause ratio) without claiming human duplication. Explicit user preferences always override learned values.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm.attributes import flag_modified
from database.db import db
from models.user_settings import UserSettings
from models.task import Task
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from utils.timezone import utc_now


class DigitalTwinLearningService:
    @classmethod
    def get_learned_profile(cls, user_id: str) -> Dict[str, Any]:
        """Retrieves learned behavioral profile."""
        settings = UserSettings.get_or_create(user_id)
        ai_pref = settings.ai or {}
        return ai_pref.get("learned_profile", {
            "velocity_multiplier": 1.0,
            "avg_session_minutes": 50,
            "pause_ratio": 0.05,
            "sample_count": 0,
            "confidence": 0,
            "last_updated": None
        })

    @classmethod
    def rebuild_learned_profile(cls, user_id: str) -> Dict[str, Any]:
        """Recomputes learned execution signals from completed tasks and runtime sessions."""
        settings = UserSettings.get_or_create(user_id)
        ai_pref = dict(settings.ai or {})

        # Compute task velocity (actual vs estimated hours)
        completed_tasks = Task.query.filter_by(user_id=user_id, status="completed").limit(30).all()
        task_velocities = []
        for t in completed_tasks:
            if t.estimated_hours and t.actual_hours and t.estimated_hours > 0:
                task_velocities.append(t.actual_hours / t.estimated_hours)

        velocity_mult = 1.0
        if task_velocities:
            velocity_mult = round(sum(task_velocities) / len(task_velocities), 2)
            velocity_mult = max(0.5, min(2.5, velocity_mult))

        # Compute session statistics
        states = RuntimeState.query.filter_by(user_id=user_id).all()
        state_ids = [st.id for st in states]
        sessions = RuntimeSession.query.filter(RuntimeSession.runtime_state_id.in_(state_ids)).limit(30).all() if state_ids else []

        durations = []
        pause_ratios = []
        for s in sessions:
            if s.planned_duration_sec and s.planned_duration_sec > 0:
                durations.append(s.planned_duration_sec / 60)
                pause_ratios.append(s.paused_duration_sec / s.planned_duration_sec)

        avg_dur = round(sum(durations) / len(durations), 1) if durations else 50.0
        avg_pause = round(sum(pause_ratios) / len(pause_ratios), 2) if pause_ratios else 0.05

        sample_count = len(completed_tasks) + len(sessions)
        confidence = min(95, 20 + sample_count * 5) if sample_count > 0 else 0

        profile = {
            "velocity_multiplier": velocity_mult,
            "avg_session_minutes": avg_dur,
            "pause_ratio": avg_pause,
            "sample_count": sample_count,
            "confidence": confidence,
            "last_updated": utc_now().isoformat()
        }

        ai_pref["learned_profile"] = profile
        settings.ai = dict(ai_pref)
        flag_modified(settings, "ai")
        settings.updated_at = utc_now()
        db.session.commit()

        return {
            "success": True,
            "learned_profile": profile
        }

    @classmethod
    def reset_learned_profile(cls, user_id: str) -> Dict[str, Any]:
        """Clears learned behavioral representation back to clean baseline."""
        settings = UserSettings.get_or_create(user_id)
        ai_pref = dict(settings.ai or {})

        profile = {
            "velocity_multiplier": 1.0,
            "avg_session_minutes": 50,
            "pause_ratio": 0.05,
            "sample_count": 0,
            "confidence": 0,
            "last_updated": None
        }

        ai_pref["learned_profile"] = profile
        settings.ai = dict(ai_pref)
        flag_modified(settings, "ai")
        settings.updated_at = utc_now()
        db.session.commit()

        return {
            "success": True,
            "learned_profile": profile
        }
