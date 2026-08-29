"""
DeadlineOS Business OS — Payment Allocation Model
=================================================
Manages settlement links between payments/transactions and invoices.
"""

from database.db import db
from datetime import datetime, timezone
import uuid


class PaymentAllocation(db.Model):
    __tablename__ = 'business_payment_allocations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    transaction_id = db.Column(
        db.String(36),
        db.ForeignKey('business_transactions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    invoice_id = db.Column(
        db.String(36),
        db.ForeignKey('business_invoices.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    allocated_amount = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True)  # ACTIVE, REVERSED
    allocated_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
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

    workspace = db.relationship('Workspace', backref=db.backref('payment_allocations', cascade='all, delete-orphan', lazy='dynamic'))
    invoice = db.relationship('Invoice', backref=db.backref('allocations', cascade='all, delete-orphan', lazy='dynamic'))
    allocator = db.relationship('User', backref=db.backref('performed_allocations', lazy='dynamic'))

    __table_args__ = (
        db.CheckConstraint('allocated_amount > 0', name='chk_biz_alloc_amount'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'transaction_id': self.transaction_id,
            'invoice_id': self.invoice_id,
            'allocated_amount': str(self.allocated_amount),
            'status': self.status,
            'allocated_by_user_id': self.allocated_by_user_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
