"""
DeadlineOS — Schedule Model
=============================
SQLAlchemy ORM models for the `schedules`, `schedule_slots`, and enhanced scheduling.
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
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", name="fk_schedule_user"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    target_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    confidence_score = db.Column(db.Integer, nullable=False, default=100)
    sys_confidence = db.Column(db.Integer, nullable=False, default=100)
    daily_summary = db.Column(db.Text, nullable=True)
    strategy = db.Column(db.String(50), nullable=True)
    available_hours = db.Column(db.Integer, nullable=True)
    version = db.Column(db.Integer, default=1)
    generated_by = db.Column(
        db.String(50), default="local"
    )  # local, gemini, LOCAL_FALLBACK_RECOVERY
    planning_brief = db.Column(db.Text, nullable=True)  # JSON serialized string
    twin_simulation = db.Column(db.Text, nullable=True)  # JSON serialized string
    backlog = db.Column(
        db.Text, nullable=True
    )  # JSON serialized array of backlogged tasks

    slots = db.relationship(
        "ScheduleSlot",
        backref="schedule",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="ScheduleSlot.start_time",
    )

    def to_dict(self):
        import json

        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "target_date": self.target_date,
            "confidence_score": self.confidence_score,
            "sys_confidence": self.sys_confidence,
            "daily_summary": self.daily_summary,
            "strategy": self.strategy,
            "available_hours": self.available_hours,
            "version": self.version,
            "generated_by": self.generated_by,
            "planning_brief": (
                json.loads(self.planning_brief) if self.planning_brief else []
            ),
            "twin_simulation": (
                json.loads(self.twin_simulation) if self.twin_simulation else None
            ),
            "backlog": json.loads(self.backlog) if self.backlog else [],
            "schedule": [slot.to_dict() for slot in self.slots],
        }


class ScheduleSlot(db.Model):
    """
    Represents an individual task, activity, or break assigned to a time window.
    """

    __tablename__ = "schedule_slots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", name="fk_scheduleslot_user"),
        nullable=True,
        index=True,
    )
    schedule_id = db.Column(
        db.String(36), db.ForeignKey("schedules.id"), nullable=True
    )
    # Multi-domain activity references
    entity_type = db.Column(db.String(50), nullable=True, default="TASK")  # TASK, GOAL, HABIT, COURSE, WORKOUT, BREAK
    entity_id = db.Column(db.String(36), nullable=True)
    task_id = db.Column(db.String(36), nullable=True)  # Legacy compatibility
    task_title = db.Column(db.String(200), nullable=False)
    
    # Timing (stored strictly in UTC)
    start_time = db.Column(db.DateTime, nullable=False)  # UTC
    end_time = db.Column(db.DateTime, nullable=False)  # UTC
    
    # Flexible window constraints
    window_start = db.Column(db.DateTime, nullable=True)  # UTC
    window_end = db.Column(db.DateTime, nullable=True)  # UTC
    
    # Priority & Status
    priority = db.Column(db.Integer, default=50)
    status = db.Column(db.String(20), default="PLANNED")  # PLANNED, CONFIRMED, RESCHEDULED, COMPLETED, CANCELLED
    
    # Recurrence link
    recurrence_rule_id = db.Column(
        db.String(36), db.ForeignKey("recurrence_rules.id", name="fk_scheduleslot_recurrence"), nullable=True
    )
    
    focus_block = db.Column(db.Boolean, default=False)
    is_break = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        from utils.timezone import get_user_timezone, to_user_local, parse_datetime_safe

        user_tz = get_user_timezone(self.user_id)

        start_local = (
            to_user_local(self.start_time, user_tz) if self.start_time else None
        )
        end_local = to_user_local(self.end_time, user_tz) if self.end_time else None
        w_start_local = to_user_local(self.window_start, user_tz) if self.window_start else None
        w_end_local = to_user_local(self.window_end, user_tz) if self.window_end else None

        def _iso_utc(dt):
            if not dt:
                return None
            dt_obj = parse_datetime_safe(dt)
            if not dt_obj:
                return str(dt)
            if dt_obj.tzinfo is None:
                dt_obj = dt_obj.replace(tzinfo=timezone.utc)
            return dt_obj.astimezone(timezone.utc).isoformat()

        return {
            "id": self.id,
            "user_id": self.user_id,
            "schedule_id": self.schedule_id,
            "entity_type": self.entity_type or "TASK",
            "entity_id": self.entity_id or self.task_id,
            "task_id": self.task_id or self.entity_id,
            "task": self.task_title,
            "title": self.task_title,
            # Backward compatibility for frontend expecting HH:MM
            "start_time": start_local.strftime("%H:%M") if start_local else "",
            "end_time": end_local.strftime("%H:%M") if end_local else "",
            # Accurate ISO fields
            "start_time_utc": _iso_utc(self.start_time),
            "end_time_utc": _iso_utc(self.end_time),
            "window_start": w_start_local.isoformat() if w_start_local else None,
            "window_end": w_end_local.isoformat() if w_end_local else None,
            "window_start_utc": _iso_utc(self.window_start),
            "window_end_utc": _iso_utc(self.window_end),
            "priority": self.priority,
            "status": self.status,
            "recurrence_rule_id": self.recurrence_rule_id,
            "focus_block": self.focus_block,
            "is_break": self.is_break,
        }
