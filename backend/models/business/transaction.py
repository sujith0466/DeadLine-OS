"""
DeadlineOS Business OS — Financial Transaction Model
=====================================================
Authoritative, append-only operational financial event ledger.
"""

from database.db import db
from datetime import datetime, timezone
import uuid


class BusinessTransaction(db.Model):
    __tablename__ = 'business_transactions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    transaction_type = db.Column(db.String(20), nullable=False)  # INCOME, EXPENSE, TRANSFER, ADJUSTMENT
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    settlement_date = db.Column(db.Date, nullable=True)
    partner_id = db.Column(
        db.String(36),
        db.ForeignKey('business_commercial_partners.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    entity_id = db.Column(
        db.String(36),
        db.ForeignKey('business_entities.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    payment_method = db.Column(db.String(50), nullable=True)  # BANK_TRANSFER, UPI, CARD, CASH, CHEQUE
    reference_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='CONFIRMED', index=True)  # CONFIRMED, REVERSED
    reversal_of_transaction_id = db.Column(
        db.String(36),
        db.ForeignKey('business_transactions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    created_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    staged_extraction_id = db.Column(
        db.String(36),
        db.ForeignKey('business_staged_extractions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    notes = db.Column(db.Text, nullable=True)

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

    workspace = db.relationship('Workspace', backref=db.backref('transactions', cascade='all, delete-orphan', lazy='dynamic'))
    partner = db.relationship('CommercialPartner', backref=db.backref('transactions', lazy='dynamic'))
    creator = db.relationship('User', backref=db.backref('created_transactions', lazy='dynamic'))
    allocations = db.relationship('PaymentAllocation', backref='transaction', cascade='all, delete-orphan', lazy='dynamic')

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'transaction_type': self.transaction_type,
            'amount': str(self.amount),
            'currency': self.currency,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'settlement_date': self.settlement_date.isoformat() if self.settlement_date else None,
            'partner_id': self.partner_id,
            'entity_id': self.entity_id,
            'partner_name': self.partner.name if self.partner else None,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'status': self.status,
            'reversal_of_transaction_id': self.reversal_of_transaction_id,
            'created_by_user_id': self.created_by_user_id,
            'staged_extraction_id': self.staged_extraction_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
