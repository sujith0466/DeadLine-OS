"""
DeadlineOS Business OS — Audit Event Model
==========================================
SQLAlchemy ORM model for `business_audit_events`.
Permanent, append-only, non-cascading forensic audit records.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class AuditEvent(db.Model):
    """
    Represents an immutable, permanent forensic audit record.
    """
    __tablename__ = 'business_audit_events'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), nullable=False, index=True)  # Logical reference, NO FK CASCADE
    actor_user_id = db.Column(db.String(36), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(36), nullable=False)
    before_state = db.Column(db.JSON, nullable=True)
    after_state = db.Column(db.JSON, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_biz_audit_ws_entity', 'workspace_id', 'entity_type', 'entity_id'),
        db.Index('idx_biz_audit_ws_created', 'workspace_id', 'created_at'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'actor_user_id': self.actor_user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'before_state': self.before_state,
            'after_state': self.after_state,
            'reason': self.reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
