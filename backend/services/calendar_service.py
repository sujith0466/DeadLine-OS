"""
DeadlineOS — Calendar Service
=============================
Transforms tasks, planning blocks, rescue alerts, and twin warnings
into an intelligent visual execution layer.
Enhanced in Phase 3 for Smart Scheduling & Recurrence.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from models.task import Task
from models.goal import Goal
from models.schedule import Schedule, ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from utils.timezone import get_user_timezone, to_user_local, to_utc


class CalendarService:

    @classmethod
    def is_empty(cls, user_id: Optional[str] = None) -> bool:
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        has_tasks = Task.query.filter_by(user_id=uid).count() > 0
        has_slots = ScheduleSlot.query.filter_by(user_id=uid).count() > 0
        return not (has_tasks or has_slots)

    @classmethod
    def get_events(
        cls, start_date: Optional[str] = None, end_date: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns mapped calendar events filtered by date range."""
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        if cls.is_empty(uid):
            return []

        events: List[Dict[str, Any]] = []
        user_tz = get_user_timezone(uid)

        start = None
        end = None

        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except Exception:
                pass
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except Exception:
                pass

        # 1. Fetch Tasks (Deadlines)
        task_query = Task.query.filter_by(user_id=uid)
        if start:
            task_query = task_query.filter(Task.deadline >= start)
        if end:
            task_query = task_query.filter(Task.deadline <= end)

        for t in task_query.all():
            if not t.deadline:
                continue
            end_time = (
                datetime.fromisoformat(t.deadline.replace("Z", "+00:00"))
                if isinstance(t.deadline, str)
                else t.deadline
            )
            start_time = end_time - timedelta(
                hours=t.estimated_hours if t.estimated_hours else 1
            )
            events.append(
                {
                    "id": f"task-dl-{t.id}",
                    "title": f"Deadline: {t.title}",
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "type": "deadline",
                    "entity_id": t.id,
                    "risk_level": (
                        "High"
                        if hasattr(t, "priority_score")
                        and t.priority_score
                        and t.priority_score > 80
                        else "Low"
                    ),
                }
            )

        # 2. Fetch Goals
        goal_query = Goal.query.filter_by(user_id=uid)
        for g_obj in goal_query.all():
            if not g_obj.target_date:
                continue
            try:
                if len(g_obj.target_date) == 10:
                    g_dt = datetime.strptime(g_obj.target_date, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                else:
                    g_dt = datetime.fromisoformat(
                        g_obj.target_date.replace("Z", "+00:00")
                    )

                if start and g_dt < start:
                    continue
                if end and g_dt > end:
                    continue

                events.append(
                    {
                        "id": f"goal-{g_obj.id}",
                        "title": f"Goal: {g_obj.title}",
                        "start": g_dt.replace(hour=9, minute=0).isoformat(),
                        "end": g_dt.replace(hour=10, minute=0).isoformat(),
                        "type": "goal",
                        "entity_id": g_obj.id,
                        "risk_level": "Medium",
                    }
                )
            except Exception:
                pass

        # 3. Fetch Scheduled Slots (Smart Scheduling)
        slots = SchedulingRepository.get_slots_by_user(uid, start, end)
        for s in slots:
            s_start = s.start_time.replace(tzinfo=timezone.utc) if s.start_time.tzinfo is None else s.start_time
            s_end = s.end_time.replace(tzinfo=timezone.utc) if s.end_time.tzinfo is None else s.end_time
            
            events.append({
                "id": s.id,
                "title": s.task_title,
                "start": s_start.isoformat(),
                "end": s_end.isoformat(),
                "type": (
                    "break" if s.is_break else
                    "meeting" if "meeting" in s.task_title.lower() else
                    s.entity_type.lower() if s.entity_type else "task"
                ),
                "entity_type": s.entity_type,
                "entity_id": s.entity_id or s.task_id,
                "status": s.status,
                "focus_block": s.focus_block,
                "is_break": s.is_break,
                "recurrence_rule_id": s.recurrence_rule_id,
                "risk_level": "Low"
            })

        return events

    @classmethod
    def get_intelligence(cls, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns the Calendar Intelligence Panel data."""
        from flask import g

        uid = user_id or getattr(g, "user_id", None)
        if cls.is_empty(uid):
            return {
                "capacity_percent": 0,
                "remaining_hours": 0,
                "schedule_confidence": 0,
                "current_risk": "Low",
                "next_deadline": "None",
                "insights": {},
                "twin_warnings": [],
                "rescue_overlays": [],
            }

        return {
            "capacity_percent": 80,
            "remaining_hours": 12,
            "schedule_confidence": 85,
            "current_risk": "Low",
            "next_deadline": "Tomorrow",
            "insights": {
                "planning": ["Smart schedule is optimized across your priority windows."],
                "accountability": ["Consistency is on track."],
                "coach": ["Focus blocks are balanced with recovery breaks."],
            },
            "twin_warnings": [],
            "rescue_overlays": [],
        }

    @classmethod
    def reschedule_event(
        cls,
        event_id: Optional[str] = None,
        new_start: Optional[str] = None,
        new_end: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Handles drag-and-drop or manual rescheduling for both Tasks and ScheduleSlots."""
        from flask import g
        from database.db import db
        from services.scheduling.rescheduling_engine import ReschedulingEngine

        uid = user_id or getattr(g, "user_id", None)
        if not event_id or not (new_start or new_end):
            return False

        target_start = datetime.fromisoformat(new_start.replace("Z", "+00:00")) if new_start else None
        target_end = datetime.fromisoformat(new_end.replace("Z", "+00:00")) if new_end else None

        # Check if event_id is a ScheduleSlot
        slot = SchedulingRepository.get_slot_by_id(event_id)
        if slot and slot.user_id == uid:
            res = ReschedulingEngine.reschedule_slot(
                user_id=uid,
                slot_id=slot.id,
                new_start_time=target_start or target_end,
                new_end_time=target_end,
                force_cascade=True
            )
            return res.get("success", False)

        # Fallback to Task deadline update
        clean_id = event_id.replace("task-dl-", "")
        task = Task.query.filter_by(user_id=uid, id=clean_id).first()
        if not task:
            return False

        try:
            task.deadline = target_end or target_start
            task.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return True
        except Exception:
            return False
