"""
DeadlineOS Business OS — Invoice Domain Models
==============================================
Manages customer and supplier commercial invoice contracts,
line items, and mathematical balance invariants.
"""

from database.db import db
from datetime import datetime, timezone
import uuid


class Invoice(db.Model):
    __tablename__ = 'business_invoices'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    invoice_number = db.Column(db.String(50), nullable=False)
    invoice_type = db.Column(db.String(20), nullable=False, default='RECEIVABLE')  # RECEIVABLE, PAYABLE
    partner_id = db.Column(
        db.String(36),
        db.ForeignKey('business_commercial_partners.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='INR')

    subtotal = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    tax_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    discount_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    paid_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    balance_due = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)

    status = db.Column(db.String(20), nullable=False, default='DRAFT', index=True)  # DRAFT, ISSUED, PARTIALLY_PAID, PAID, OVERDUE, VOID
    notes = db.Column(db.Text, nullable=True)
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

    workspace = db.relationship('Workspace', backref=db.backref('invoices', cascade='all, delete-orphan', lazy='dynamic'))
    partner = db.relationship('CommercialPartner', backref=db.backref('invoices', lazy='dynamic'))
    creator = db.relationship('User', backref=db.backref('created_invoices', lazy='dynamic'))
    staged_extraction = db.relationship('StagedExtraction', backref=db.backref('committed_invoices', lazy='dynamic'))
    items = db.relationship('InvoiceLineItem', backref='invoice', cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('workspace_id', 'invoice_number', name='uq_biz_inv_ws_num'),
        db.CheckConstraint(
            "subtotal >= 0 AND tax_amount >= 0 AND discount_amount >= 0 AND total_amount >= 0 AND "
            "discount_amount <= (subtotal + tax_amount) AND paid_amount >= 0 AND balance_due >= 0 AND "
            "(status = 'VOID' OR (paid_amount + balance_due = total_amount))",
            name='chk_biz_inv_math'
        ),
    )

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'invoice_number': self.invoice_number,
            'invoice_type': self.invoice_type,
            'partner_id': self.partner_id,
            'partner_name': self.partner.name if self.partner else None,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'currency': self.currency,
            'subtotal': str(self.subtotal),
            'tax_amount': str(self.tax_amount),
            'discount_amount': str(self.discount_amount),
            'total_amount': str(self.total_amount),
            'paid_amount': str(self.paid_amount),
            'balance_due': str(self.balance_due),
            'status': self.status,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'staged_extraction_id': self.staged_extraction_id,
            'items': [item.serialize() for item in self.items.all()],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class InvoiceLineItem(db.Model):
    __tablename__ = 'business_invoice_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(
        db.String(36),
        db.ForeignKey('business_invoices.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def serialize(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'workspace_id': self.workspace_id,
            'description': self.description,
            'quantity': str(self.quantity),
            'unit_price': str(self.unit_price),
            'amount': str(self.amount),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
