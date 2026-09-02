"""
DeadlineOS Business OS — Operational Alert Model (Phase C2.4)
=============================================================
SQLAlchemy ORM model for `business_operational_alerts`.
Represents proactive operational signals, deduplicated threshold alerts,
and linkages to operational tasks.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessOperationalAlert(db.Model):
    """
    Represents an operational alert with lifecycle states, deduplication fingerprint,
    cooldown suppression, and task synthesis linkage.
    """
    __tablename__ = 'business_operational_alerts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    # STOCKOUT_IMMINENT, BELOW_SAFETY_STOCK, OVERDUE_PO, DELAYED_RECEIVING, QUALITY_DEGRADATION, DEAD_STOCK_ACCUMULATION
    severity = db.Column(db.String(20), nullable=False, default='WARNING')  # CRITICAL, WARNING, INFO
    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True)  # ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)  # PRODUCT, PURCHASE_ORDER, SUPPLIER, LOCATION, GOODS_RECEIPT
    entity_id = db.Column(db.String(36), nullable=False, index=True)
    dedup_fingerprint = db.Column(db.String(128), nullable=False, index=True)
    cooldown_until = db.Column(db.DateTime(timezone=True), nullable=True)
    recommended_action = db.Column(db.String(50), nullable=True)  # CREATE_PURCHASE_REQUEST, EXPEDITE_PO, INSPECT_INVENTORY, REVIEW_SUPPLIER
    generated_task_id = db.Column(
        db.String(36),
        db.ForeignKey('business_tasks.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    acknowledged_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    acknowledged_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolved_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('operational_alerts', lazy='dynamic', cascade='all, delete-orphan'))
    generated_task = db.relationship('BusinessTask', backref=db.backref('source_alert', uselist=False))
    acknowledged_by = db.relationship('User', foreign_keys=[acknowledged_by_user_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id])

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'status': self.status,
            'title': self.title,
            'description': self.description,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'dedup_fingerprint': self.dedup_fingerprint,
            'cooldown_until': self.cooldown_until.isoformat() if self.cooldown_until else None,
            'recommended_action': self.recommended_action,
            'generated_task_id': self.generated_task_id,
            'acknowledged_by_user_id': self.acknowledged_by_user_id,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_by_user_id': self.resolved_by_user_id,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_note': self.resolution_note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
