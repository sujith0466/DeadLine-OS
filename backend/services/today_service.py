"""
DeadlineOS — Today Service (Phase 2, 3 & 5)
===========================================
Aggregates tasks, habits, goals, and smart schedule slots for the Today Surface.
Integrates with Phase 1 Runtime, Phase 3 Scheduling, and Phase 5 Recovery.
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
from services.recovery.service import RecoveryService
from utils.timezone import to_user_local, get_user_timezone, utc_now


class TodayService:
    @classmethod
    def get_today_activities(cls, user_id: str) -> Dict[str, Any]:
        """
        Fetch all actionable items for the user's Today Surface.
        Respects Vacation Mode, Emergency Mode, and Recovery states.
        """
        tz_name = get_user_timezone(user_id)
        local_now = to_user_local(utc_now(), tz_name)
        today_date = local_now.date()

        # Check Vacation Mode
        is_vacation = RecoveryService.is_user_on_vacation(user_id)
        is_emergency = RecoveryService.is_emergency_mode_active(user_id)

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
            slot = slot_map.get(t.id)
            if slot and slot.get("status") in ("SKIPPED", "PAUSED"):
                continue  # Exclude skipped/paused slots from active today list

            if is_emergency and getattr(t, 'priority_score', 0) < 70 and not slot:
                continue  # Filter low priority tasks during Emergency Mode

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
                "schedule_slot": slot
            }
            activities.append(activity)
            
        for h in habits:
            slot = slot_map.get(h.id)
            if slot and slot.get("status") in ("SKIPPED", "PAUSED"):
                continue

            if is_emergency:
                continue  # Habits deferred during Emergency Mode

            activity = {
                "id": h.id,
                "type": "habit",
                "title": h.name,
                "status": h.status,
                "priority_score": getattr(h, 'momentum_score', 50),
                "runtime": runtime_map.get(h.id),
                "schedule_slot": slot
            }
            activities.append(activity)

        return {
            "date": today_date.isoformat(),
            "timezone": tz_name,
            "is_vacation_mode": is_vacation,
            "is_emergency_mode": is_emergency,
            "activities_count": len(activities),
            "activities": activities,
            "upcoming": activities,
            "in_progress": [a for a in activities if (a.get("runtime") or {}).get("lifecycle_state") == "RUNNING"]
        }
