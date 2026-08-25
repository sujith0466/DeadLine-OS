"""
DeadlineOS — Activity Scheduling Service
=========================================
Handles deterministic scheduling of activities across multiple domains (Task, Goal, Habit, Course, Workout)
without modifying or coupling the underlying domain models.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from database.db import db
from models.schedule import ScheduleSlot
from models.task import Task
from models.goal import Goal, Habit
from services.scheduling.repository import SchedulingRepository
from utils.timezone import get_user_timezone, to_utc, to_user_local, utc_now


class ActivityScheduler:
    """Deterministic activity scheduling engine."""

    VALID_ENTITY_TYPES = {"TASK", "GOAL", "HABIT", "COURSE", "WORKOUT", "BREAK", "CUSTOM"}

    @classmethod
    def resolve_entity_details(cls, user_id: str, entity_type: str, entity_id: Optional[str]) -> Dict[str, Any]:
        """Resolves title, priority, and default duration from domain models without altering them."""
        entity_type_upper = (entity_type or "TASK").upper()
        
        details = {
            "title": "Scheduled Activity",
            "priority": 50,
            "duration_minutes": 60,
            "category": "general"
        }

        if not entity_id:
            return details

        if entity_type_upper == "TASK":
            task = Task.query.filter_by(user_id=user_id, id=entity_id).first()
            if task:
                details["title"] = task.title
                details["priority"] = getattr(task, "priority_score", 50) or 50
                details["duration_minutes"] = int((task.estimated_hours or 1.0) * 60)
                details["category"] = task.category or "work"
        elif entity_type_upper == "GOAL":
            goal = Goal.query.filter_by(user_id=user_id, id=entity_id).first()
            if goal:
                details["title"] = goal.title
                priority_map = {"High": 85, "Medium": 50, "Low": 25}
                details["priority"] = priority_map.get(goal.priority, 50)
                details["duration_minutes"] = 60
                details["category"] = goal.category or "goal"
        elif entity_type_upper == "HABIT":
            habit = Habit.query.filter_by(user_id=user_id, id=entity_id).first()
            if habit:
                details["title"] = habit.name
                details["priority"] = getattr(habit, "momentum_score", 60) or 60
                details["duration_minutes"] = 30
                details["category"] = habit.category or "habit"

        return details

    @classmethod
    def schedule_activity(
        cls,
        user_id: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
        priority: Optional[int] = None,
        focus_block: bool = False,
        is_break: bool = False,
        schedule_id: Optional[str] = None,
        status: str = "PLANNED"
    ) -> ScheduleSlot:
        """
        Deterministically schedules an activity slot with UTC storage and timezone safety.
        """
        entity_type_upper = (entity_type or "TASK").upper()
        if entity_type_upper not in cls.VALID_ENTITY_TYPES:
            entity_type_upper = "CUSTOM"

        # Resolve entity defaults
        entity_info = cls.resolve_entity_details(user_id, entity_type_upper, entity_id)
        slot_title = title or entity_info["title"]
        slot_priority = priority if priority is not None else entity_info["priority"]
        
        # Calculate start/end time
        if not start_time:
            start_time = utc_now()
        
        # Ensure UTC tzinfo
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        
        if not end_time:
            dur = duration_minutes or entity_info["duration_minutes"]
            end_time = start_time + timedelta(minutes=dur)
        elif end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        if end_time <= start_time:
            end_time = start_time + timedelta(minutes=duration_minutes or 30)

        # Build ScheduleSlot
        slot = ScheduleSlot(
            user_id=user_id,
            schedule_id=schedule_id,
            entity_type=entity_type_upper,
            entity_id=entity_id,
            task_id=entity_id if entity_type_upper == "TASK" else None,
            task_title=slot_title,
            start_time=start_time,
            end_time=end_time,
            window_start=window_start,
            window_end=window_end,
            priority=slot_priority,
            status=status,
            focus_block=focus_block,
            is_break=is_break
        )

        return SchedulingRepository.save_slot(slot)

    @classmethod
    def get_user_schedule(
        cls,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve user slots converted to localized format."""
        st = datetime.fromisoformat(start_date.replace("Z", "+00:00")) if start_date else None
        et = datetime.fromisoformat(end_date.replace("Z", "+00:00")) if end_date else None
        
        slots = SchedulingRepository.get_slots_by_user(user_id, st, et, status)
        return [s.to_dict() for s in slots]
