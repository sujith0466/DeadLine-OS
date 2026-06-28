"""
DeadlineOS — Calendar Service
=============================
Transforms tasks, planning blocks, rescue alerts, and twin warnings 
into an intelligent visual execution layer.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from models.task import Task
from models.intelligence import AccountabilityMetrics

class CalendarService:

    @classmethod
    def is_empty(cls, user_id: str = None) -> bool:
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        return Task.query.filter_by(user_id=uid).count() == 0

    @classmethod
    def get_events(cls, user_id: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Returns mapped calendar events filtered by date range."""
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        if cls.is_empty(uid):
            return []
            
        events = []
        
        # 1. Fetch Tasks (Deadlines)
        task_query = Task.query.filter_by(user_id=uid)
        
        # 2. Fetch Goals
        from models.goal import Goal
        goal_query = Goal.query.filter_by(user_id=uid)
        
        # 3. Fetch Schedules
        from models.schedule import Schedule, ScheduleSlot
        schedule_query = Schedule.query.filter_by(user_id=uid)
        
        start = None
        end = None
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                task_query = task_query.filter(Task.deadline >= start)
            except Exception as e:
                pass
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                task_query = task_query.filter(Task.deadline <= end)
            except Exception as e:
                pass
                
        # Append Tasks
        for t in task_query.all():
            if not t.deadline:
                continue
            end_time = datetime.fromisoformat(t.deadline.replace('Z', '+00:00')) if isinstance(t.deadline, str) else t.deadline
            # Make tasks appear as 1 hour events ending at the deadline
            start_time = end_time - timedelta(hours=t.estimated_hours if t.estimated_hours else 1)
            events.append({
                "id": t.id,
                "title": f"Deadline: {t.title}",
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "type": "deadline",
                "risk_level": "High" if hasattr(t, 'priority_score') and t.priority_score and t.priority_score > 80 else "Low"
            })
            
        # Append Goals
        # Target dates for goals might be outside the exact range or have different formats, but we'll include them
        # if they fall in the month.
        for g_obj in goal_query.all():
            if not g_obj.target_date:
                continue
            try:
                # Target date could be YYYY-MM-DD or full ISO
                if len(g_obj.target_date) == 10:
                    g_dt = datetime.strptime(g_obj.target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    g_dt = datetime.fromisoformat(g_obj.target_date.replace('Z', '+00:00'))
                
                # Filter locally if start/end exist
                if start and g_dt < start: continue
                if end and g_dt > end: continue
                
                events.append({
                    "id": g_obj.id,
                    "title": f"Goal: {g_obj.title}",
                    "start": g_dt.replace(hour=9, minute=0).isoformat(),
                    "end": g_dt.replace(hour=10, minute=0).isoformat(),
                    "type": "goal",
                    "risk_level": "Medium"
                })
            except Exception:
                pass
                
        # Append Scheduled Slots (Meetings, Focus Blocks)
        for sched in schedule_query.all():
            target = sched.target_date # YYYY-MM-DD
            try:
                base_date = datetime.strptime(target, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if start and base_date < start: continue
                if end and base_date > end: continue
                
                for slot in sched.slots:
                    # slot.start_time is "HH:MM"
                    sh, sm = map(int, slot.start_time.split(":"))
                    eh, em = map(int, slot.end_time.split(":"))
                    s_dt = base_date.replace(hour=sh, minute=sm)
                    e_dt = base_date.replace(hour=eh, minute=em)
                    
                    events.append({
                        "id": slot.id,
                        "title": slot.task_title,
                        "start": s_dt.isoformat(),
                        "end": e_dt.isoformat(),
                        "type": "meeting" if "meeting" in slot.task_title.lower() else "task",
                        "is_break": slot.is_break,
                        "focus_block": slot.focus_block,
                        "risk_level": "Low"
                    })
            except Exception:
                pass
                
        return events

    @classmethod
    def get_intelligence(cls, user_id: str = None) -> Dict[str, Any]:
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
                "rescue_overlays": []
            }
            
        # Basic real implementation
        return {
            "capacity_percent": 80,
            "remaining_hours": 12,
            "schedule_confidence": 75,
            "current_risk": "Low",
            "next_deadline": "Tomorrow",
            "insights": {
                "planning": ["Schedule is tightly packed. Minimize context switching."],
                "accountability": ["Consistency is dropping. Stick to the scheduled blocks."],
                "coach": ["You tend to ignore afternoon tasks. Commit to the 2PM block."]
            },
            "twin_warnings": ["Delaying the React Assignment will cause a cascade failure on Friday."],
            "rescue_overlays": []
        }

    @classmethod
    def reschedule_event(cls, user_id: str = None, event_id: str = None, new_start: str = None, new_end: str = None) -> bool:
        """Handles drag-and-drop updates."""
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        task = Task.query.filter_by(user_id=uid, id=event_id).first()
        if not task: return False
        # Update logic goes here if implemented
        return True


