"""
DeadlineOS — Notification Model (Phase 4)
==========================================
SQLAlchemy ORM model for notifications with lifecycle tracking,
deduplication keys, UTC timestamps, and action confirmation metadata.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class NotificationStatus:
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    DELIVERED = "DELIVERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DISMISSED = "DISMISSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class NotificationType:
    PRE_ALERT = "PRE_ALERT"
    REMINDER = "REMINDER"
    RUNNING_SESSION = "RUNNING_SESSION"
    CHECKIN = "CHECKIN"
    ESCALATION = "ESCALATION"
    CONFIRMATION = "CONFIRMATION"
    SYSTEM = "SYSTEM"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", name="fk_notification_user"),
        nullable=True,
        index=True,
    )
    
    # ── Notification Metadata ──────────────────────────────────
    notification_type = db.Column(db.String(50), default=NotificationType.SYSTEM, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), default="info")  # critical, high, medium, low, info
    priority = db.Column(db.String(20), default="info")
    
    # ── Domain & Scheduling Linkages ───────────────────────────
    module = db.Column(db.String(50), nullable=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True, index=True)
    schedule_id = db.Column(db.String(36), nullable=True, index=True)
    runtime_session_id = db.Column(db.String(36), nullable=True)
    
    # ── Lifecycle Timestamps (UTC) ─────────────────────────────
    scheduled_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # ── Lifecycle State ────────────────────────────────────────
    status = db.Column(db.String(30), default=NotificationStatus.DELIVERED, nullable=False, index=True)
    read = db.Column(db.Boolean, default=False, index=True)
    
    # ── Deduplication & Reliability ───────────────────────────
    deduplication_key = db.Column(db.String(255), nullable=True, unique=False, index=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    group_id = db.Column(db.String(36), nullable=True, index=True)

    # ── Action & Confirmation ─────────────────────────────────
    action_url = db.Column(db.String(255), nullable=True)
    requires_confirmation = db.Column(db.Boolean, default=False)
    confirmation_action = db.Column(db.JSON, nullable=True)
    
    # ── UI Styling ────────────────────────────────────────────
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    category = db.Column(db.String(50), nullable=True)

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
            "notification_type": self.notification_type,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "priority": self.priority,
            "module": self.module,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "schedule_id": self.schedule_id,
            "runtime_session_id": self.runtime_session_id,
            "scheduled_at": _iso_utc(self.scheduled_at),
            "delivered_at": _iso_utc(self.delivered_at),
            "acknowledged_at": _iso_utc(self.acknowledged_at),
            "dismissed_at": _iso_utc(self.dismissed_at),
            "created_at": _iso_utc(self.created_at),
            "updated_at": _iso_utc(self.updated_at),
            "status": self.status,
            "read": self.read,
            "deduplication_key": self.deduplication_key,
            "retry_count": self.retry_count,
            "group_id": self.group_id,
            "action_url": self.action_url,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_action": self.confirmation_action,
            "icon": self.icon,
            "color": self.color,
            "category": self.category,
        }
