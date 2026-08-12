"""
DeadlineOS — Today Service (Phase 2)
=====================================
Aggregates tasks, habits, and goals for the Today Surface.
Integrates with the Phase 1 Runtime Engine for execution state.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from database.db import db
from models.task import Task
from models.goal import Goal
from models.runtime_state import RuntimeState
from models.user_settings import UserSettings
from utils.timezone import to_user_local

class TodayService:
    @classmethod
    def get_today_activities(cls, user_id: str) -> Dict[str, Any]:
        """
        Fetch all actionable items for the user's Today Surface.
        Returns them separated by category (running, upcoming, completed, etc.)
        """
        settings = UserSettings.query.get(user_id)
        tz_name = settings.profile.get("timezone", "UTC") if (settings and settings.profile) else "UTC"
        local_now = to_user_local(datetime.now(timezone.utc), tz_name)
        today_date = local_now.date()

        all_tasks = Task.query.filter_by(user_id=user_id).filter(Task.status.in_(['pending', 'in_progress'])).all()
        habits = Goal.query.filter_by(user_id=user_id, is_habit=True, status='active').all()
        
        active_runtimes = RuntimeState.query.filter_by(user_id=user_id).all()
        runtime_map = {rt.entity_id: rt.serialize() for rt in active_runtimes}
        
        activities = []
        
        for t in all_tasks:
            if t.deadline:
                task_date = to_user_local(t.deadline, tz_name).date()
                if task_date > today_date:
                    continue
                    
            activity = {
                "id": t.id,
                "type": "task",
                "title": t.title,
                "status": t.status,
                "priority_score": getattr(t, 'priority_score', 0),
                "ai_confidence": getattr(t, 'ai_confidence', None),
                "runtime": runtime_map.get(t.id)
            }
            activities.append(activity)
            
        for h in habits:
            activity = {
                "id": h.id,
                "type": "habit",
                "title": h.title,
                "status": h.status,
                "runtime": runtime_map.get(h.id)
            }
            activities.append(activity)
            
        running = [a for a in activities if a.get("runtime") and a["runtime"]["lifecycle_state"] == "RUNNING"]
        interrupted = [a for a in activities if a.get("runtime") and a["runtime"]["lifecycle_state"] == "INTERRUPTED"]
        paused = [a for a in activities if a.get("runtime") and a["runtime"]["lifecycle_state"] == "PAUSED"]
        
        active_ids = {a["id"] for a in running + interrupted + paused}
        upcoming = [a for a in activities if a["id"] not in active_ids]
        upcoming.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        
        return {
            "date": today_date.isoformat(),
            "timezone": tz_name,
            "running": running,
            "interrupted": interrupted,
            "paused": paused,
            "upcoming": upcoming,
            "completed": []
        }
