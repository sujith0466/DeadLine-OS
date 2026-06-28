"""
DeadlineOS — Schedule Model
=============================
SQLAlchemy ORM models for the `schedules` and `schedule_slots` tables.
"""

import uuid
from datetime import datetime, timezone

from database.db import db

class Schedule(db.Model):
    """
    Represents a daily generated schedule in DeadlineOS.
    """
    __tablename__ = "schedules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_schedule_user'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    target_date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    confidence_score = db.Column(db.Integer, nullable=False, default=100)
    sys_confidence = db.Column(db.Integer, nullable=False, default=100)
    daily_summary = db.Column(db.Text, nullable=True)
    strategy = db.Column(db.String(50), nullable=True)
    available_hours = db.Column(db.Integer, nullable=True)
    version = db.Column(db.Integer, default=1)
    generated_by = db.Column(db.String(50), default="local") # local, gemini, LOCAL_FALLBACK_RECOVERY
    planning_brief = db.Column(db.Text, nullable=True) # JSON serialized string
    twin_simulation = db.Column(db.Text, nullable=True) # JSON serialized string
    backlog = db.Column(db.Text, nullable=True) # JSON serialized array of backlogged tasks

    slots = db.relationship("ScheduleSlot", backref="schedule", cascade="all, delete-orphan", lazy=True, order_by="ScheduleSlot.start_time")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "target_date": self.target_date,
            "confidence_score": self.confidence_score,
            "sys_confidence": self.sys_confidence,
            "daily_summary": self.daily_summary,
            "strategy": self.strategy,
            "available_hours": self.available_hours,
            "version": self.version,
            "generated_by": self.generated_by,
            "planning_brief": json.loads(self.planning_brief) if self.planning_brief else [],
            "twin_simulation": json.loads(self.twin_simulation) if self.twin_simulation else None,
            "backlog": json.loads(self.backlog) if self.backlog else [],
            "schedule": [slot.to_dict() for slot in self.slots]
        }

class ScheduleSlot(db.Model):
    """
    Represents an individual task or break assigned to a time window inside a schedule.
    """
    __tablename__ = "schedule_slots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_scheduleslot_user'), nullable=True, index=True)
    schedule_id = db.Column(db.String(36), db.ForeignKey("schedules.id"), nullable=False)
    task_id = db.Column(db.String(36), nullable=True) # None for breaks
    task_title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.String(5), nullable=False) # HH:MM
    end_time = db.Column(db.String(5), nullable=False) # HH:MM
    focus_block = db.Column(db.Boolean, default=False)
    is_break = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "task": self.task_title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "focus_block": self.focus_block,
            "is_break": self.is_break
        }
