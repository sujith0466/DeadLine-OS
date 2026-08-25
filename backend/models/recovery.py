"""
DeadlineOS — Recovery Models (Phase 5)
======================================
Defines recovery action types, statuses, and audit records for schedule and
execution recovery operations.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class RecoveryActionType:
    SKIP = "SKIP"
    DEFER = "DEFER"
    RESCHEDULE = "RESCHEDULE"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    RECOVER = "RECOVER"
    VACATION = "VACATION"
    EMERGENCY = "EMERGENCY"


class RecoveryRecord(db.Model):
    __tablename__ = "recovery_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", name="fk_recovery_user"),
        nullable=False,
        index=True
    )
    action_type = db.Column(db.String(50), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True, index=True)
    schedule_id = db.Column(db.String(36), nullable=True, index=True)
    
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        def _iso_utc(dt):
            if not dt:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()

        return {
            "id": self.id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "schedule_id": self.schedule_id,
            "details": self.details or {},
            "created_at": _iso_utc(self.created_at)
        }
