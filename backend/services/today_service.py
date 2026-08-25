"""
DeadlineOS — Today Service (Phase 2 & 3)
=========================================
Aggregates tasks, habits, goals, and smart schedule slots for the Today Surface.
Integrates with the Phase 1 Runtime Engine for execution state.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from database.db import db
from models.task import Task
from models.goal import Goal, Habit
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.user_settings import UserSettings
from services.scheduling.repository import SchedulingRepository
from utils.timezone import to_user_local, get_user_timezone, utc_now


class TodayService:
    @classmethod
    def get_today_activities(cls, user_id: str) -> Dict[str, Any]:
        """
        Fetch all actionable items for the user's Today Surface.
        Integrates scheduled slots with runtime states.
        """
        tz_name = get_user_timezone(user_id)
        local_now = to_user_local(utc_now(), tz_name)
        today_date = local_now.date()

        # Query pending tasks & active habits
        all_tasks = Task.query.filter_by(user_id=user_id).filter(Task.status.in_(['pending', 'in_progress'])).all()
        habits = Habit.query.filter_by(user_id=user_id, status='Active').all()
        
        # Runtime states
        active_runtimes = RuntimeState.query.filter_by(user_id=user_id).all()
        runtime_map = {rt.entity_id: {"lifecycle_state": rt.status} for rt in active_runtimes}
        
        # Scheduled slots for today
        day_start_utc = datetime(today_date.year, today_date.month, today_date.day, 0, 0, tzinfo=timezone.utc)
        day_end_utc = day_start_utc + timedelta(days=1)
        today_slots = SchedulingRepository.get_slots_by_user(user_id, day_start_utc, day_end_utc)
        slot_map = {s.entity_id: s.to_dict() for s in today_slots if s.entity_id}

        activities = []
        
        for t in all_tasks:
            if t.deadline:
                task_date = to_user_local(t.deadline, tz_name).date()
                if task_date > today_date and t.id not in slot_map:
                    continue
                    
            activity = {
                "id": t.id,
                "type": "task",
                "title": t.title,
                "status": t.status,
                "priority_score": getattr(t, 'priority_score', 0),
                "ai_confidence": getattr(t, 'ai_confidence', None),
                "runtime": runtime_map.get(t.id),
                "schedule_slot": slot_map.get(t.id)
            }
            activities.append(activity)
            
        for h in habits:
            activity = {
                "id": h.id,
                "type": "habit",
                "title": h.name,
                "status": h.status,
                "priority_score": getattr(h, 'momentum_score', 50),
                "runtime": runtime_map.get(h.id),
                "schedule_slot": slot_map.get(h.id)
            }
            activities.append(activity)

        # Include standalone scheduled slots (e.g. Courses, Breaks, Custom blocks)
        existing_entity_ids = {a["id"] for a in activities}
        for s in today_slots:
            if s.entity_id and s.entity_id in existing_entity_ids:
                continue
            activities.append({
                "id": s.id,
                "type": (s.entity_type or "TASK").lower(),
                "title": s.task_title,
                "status": s.status,
                "priority_score": s.priority,
                "runtime": runtime_map.get(s.id),
                "schedule_slot": s.to_dict()
            })
            
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
