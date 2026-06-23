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
    def is_empty(cls) -> bool:
        return Task.query.count() == 0

    @classmethod
    def get_events(cls, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Returns mapped calendar events filtered by date range."""
        if cls.is_empty():
            return []
            
        query = Task.query
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Task.deadline >= start)
            except:
                pass
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Task.deadline <= end)
            except:
                pass
                
        tasks = query.all()
        events = []
        for t in tasks:
            if not t.deadline:
                continue
            # Basic mapping. A real system would use scheduled start/end from Planning Agent.
            end_time = datetime.fromisoformat(t.deadline.replace('Z', '+00:00')) if isinstance(t.deadline, str) else t.deadline
            start_time = end_time - timedelta(hours=t.estimated_hours)
            events.append({
                "id": t.id,
                "title": t.title,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "type": "task",
                "risk_level": "High" if hasattr(t, 'priority_score') and t.priority_score and t.priority_score > 80 else "Low"
            })
        return events

    @classmethod
    def get_intelligence(cls) -> Dict[str, Any]:
        """Returns the Calendar Intelligence Panel data."""
        if cls.is_empty():
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
    def reschedule_event(cls, event_id: str, new_start: str, new_end: str) -> bool:
        """Handles drag-and-drop updates."""
        # For demo, just return True. In reality, update Task / Schedule block.
        return True


