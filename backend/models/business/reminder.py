"""
DeadlineOS Business OS — Collection Reminder Model
==================================================
Represents tone-aware payment reminders grounded in verified invoice data.
"""

from database.db import db
from datetime import datetime, timezone
import uuid


class CollectionReminder(db.Model):
    __tablename__ = 'business_collection_reminders'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    invoice_id = db.Column(db.String(36), db.ForeignKey('business_invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    partner_id = db.Column(db.String(36), db.ForeignKey('business_commercial_partners.id', ondelete='SET NULL'), nullable=True, index=True)

    tone = db.Column(db.String(20), nullable=False, default='POLITE')  # GENTLE, POLITE, URGENT, LEGAL
    subject = db.Column(db.String(255), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    recipient_email = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='DRAFT')  # DRAFT, SENT, CANCELLED

    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('collection_reminders', lazy='dynamic', cascade='all, delete-orphan'))
    invoice = db.relationship('Invoice', backref=db.backref('collection_reminders', lazy='dynamic', cascade='all, delete-orphan'))
    partner = db.relationship('CommercialPartner', backref=db.backref('collection_reminders', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice.invoice_number if self.invoice else None,
            'partner_id': self.partner_id,
            'partner_name': self.partner.name if self.partner else None,
            'tone': self.tone,
            'subject': self.subject,
            'message_body': self.message_body,
            'recipient_email': self.recipient_email,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
