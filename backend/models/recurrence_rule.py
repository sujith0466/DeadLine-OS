"""
DeadlineOS — Recurrence Rule Model
====================================
Stores deterministic recurrence definitions for scheduled activities.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class RecurrenceRule(db.Model):
    __tablename__ = "recurrence_rules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", name="fk_recurrence_user"),
        nullable=False,
        index=True,
    )
    frequency = db.Column(db.String(20), nullable=False)  # DAILY, WEEKLY, WEEKDAYS, CUSTOM_DAYS, INTERVAL_DAYS
    interval = db.Column(db.Integer, default=1)  # Every N days / weeks
    by_weekdays = db.Column(db.String(50), nullable=True)  # JSON or comma-separated e.g. "MO,TU,WE,TH,FR"
    start_date = db.Column(db.DateTime, nullable=False)  # UTC
    end_date = db.Column(db.DateTime, nullable=True)  # UTC
    occurrence_count = db.Column(db.Integer, nullable=True)  # Max occurrences
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "frequency": self.frequency,
            "interval": self.interval,
            "by_weekdays": self.by_weekdays.split(",") if self.by_weekdays else [],
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "occurrence_count": self.occurrence_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
