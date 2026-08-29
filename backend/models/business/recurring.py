"""
DeadlineOS Business OS — Recurring Obligations & Automation Models
==================================================================
Models for recurring commercial contracts, tax compliance schedules,
and automation execution logs.
"""

from database.db import db
from datetime import datetime, timezone, date
import uuid


class RecurringObligation(db.Model):
    __tablename__ = 'business_recurring_obligations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    partner_id = db.Column(db.String(36), db.ForeignKey('business_commercial_partners.id', ondelete='SET NULL'), nullable=True, index=True)
    entity_id = db.Column(db.String(36), db.ForeignKey('business_entities.id', ondelete='SET NULL'), nullable=True, index=True)

    title = db.Column(db.String(255), nullable=False)
    obligation_type = db.Column(db.String(30), nullable=False)  # 'RECEIVABLE', 'PAYABLE', 'TAX_COMPLIANCE', 'PAYROLL'
    frequency = db.Column(db.String(20), nullable=False)        # 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUALLY'

    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='INR')

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    next_due_date = db.Column(db.Date, nullable=False, index=True)

    auto_generate = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')  # 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED'
    notes = db.Column(db.Text, nullable=True)

    created_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('recurring_obligations', lazy='dynamic', cascade='all, delete-orphan'))
    partner = db.relationship('CommercialPartner', backref=db.backref('recurring_obligations', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'partner_id': self.partner_id,
            'entity_id': self.entity_id,
            'partner_name': self.partner.name if self.partner else None,
            'title': self.title,
            'obligation_type': self.obligation_type,
            'frequency': self.frequency,
            'amount': str(self.amount),
            'currency': self.currency,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'auto_generate': self.auto_generate,
            'status': self.status,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AutomationExecutionLog(db.Model):
    __tablename__ = 'business_automation_execution_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    obligation_id = db.Column(db.String(36), db.ForeignKey('business_recurring_obligations.id', ondelete='CASCADE'), nullable=False, index=True)

    execution_type = db.Column(db.String(30), nullable=False)   # 'INVOICE_GENERATION', 'STATUS_CHECK'
    execution_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)           # 'SUCCESS', 'SKIPPED', 'FAILED'

    generated_entity_type = db.Column(db.String(30), nullable=True)
    generated_entity_id = db.Column(db.String(36), nullable=True)
    details = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('automation_logs', lazy='dynamic', cascade='all, delete-orphan'))
    obligation = db.relationship('RecurringObligation', backref=db.backref('execution_logs', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'obligation_id': self.obligation_id,
            'execution_type': self.execution_type,
            'execution_date': self.execution_date.isoformat() if self.execution_date else None,
            'status': self.status,
            'generated_entity_type': self.generated_entity_type,
            'generated_entity_id': self.generated_entity_id,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
