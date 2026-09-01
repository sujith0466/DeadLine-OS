"""
DeadlineOS Business OS — Purchase Order Models
===============================================
SQLAlchemy ORM models for `business_purchase_orders` and `business_purchase_order_lines`.
Represents formal supplier purchasing contracts with line items and fulfillment tracking.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessPurchaseOrder(db.Model):
    """
    Represents a formal commercial Purchase Order issued to a supplier.
    """
    __tablename__ = 'business_purchase_orders'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    po_number = db.Column(db.String(50), nullable=False)
    supplier_partner_id = db.Column(
        db.String(36),
        db.ForeignKey('business_commercial_partners.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    destination_location_id = db.Column(
        db.String(36),
        db.ForeignKey('business_locations.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    order_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    expected_delivery_date = db.Column(db.Date, nullable=True)
    subtotal_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    tax_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    payment_terms = db.Column(db.String(50), nullable=False, default='NET_30')
    status = db.Column(db.String(30), nullable=False, default='DRAFT')  # DRAFT, APPROVED, SENT_TO_SUPPLIER, ACKNOWLEDGED, PARTIALLY_RECEIVED, FULLY_RECEIVED, CLOSED, CANCELLED
    notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    approved_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

    __table_args__ = (
        db.UniqueConstraint('workspace_id', 'po_number', name='uq_biz_po_ws_num'),
        db.Index('idx_biz_po_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_po_ws_supplier', 'workspace_id', 'supplier_partner_id'),
        db.CheckConstraint('subtotal_amount >= 0 AND tax_amount >= 0 AND total_amount >= 0', name='chk_biz_po_amounts'),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('purchase_orders', lazy='dynamic', cascade='all, delete-orphan'))
    supplier = db.relationship('CommercialPartner', backref=db.backref('purchase_orders', lazy='dynamic'))
    destination_location = db.relationship('BusinessLocation', backref=db.backref('destination_purchase_orders', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('created_purchase_orders', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approved_by_user_id], backref=db.backref('approved_purchase_orders', lazy='dynamic'))
    lines = db.relationship('BusinessPurchaseOrderLine', backref='purchase_order', lazy='joined', cascade='all, delete-orphan')

    def serialize(self, include_lines=True):
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'po_number': self.po_number,
            'supplier_partner_id': self.supplier_partner_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'destination_location_id': self.destination_location_id,
            'destination_location_name': self.destination_location.name if self.destination_location else None,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'subtotal_amount': str(self.subtotal_amount),
            'tax_amount': str(self.tax_amount),
            'total_amount': str(self.total_amount),
            'currency': self.currency,
            'payment_terms': self.payment_terms,
            'status': self.status,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'creator_name': (self.creator.full_name or self.creator.email) if self.creator else None,
            'approved_by_user_id': self.approved_by_user_id,
            'approver_name': (self.approver.full_name or self.approver.email) if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_lines:
            data['lines'] = [line.serialize() for line in (self.lines or [])]
        return data


class BusinessPurchaseOrderLine(db.Model):
    """
    Represents an individual product line item within a Purchase Order.
    """
    __tablename__ = 'business_purchase_order_lines'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id = db.Column(
        db.String(36),
        db.ForeignKey('business_purchase_orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey('business_products.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    ordered_quantity = db.Column(db.Numeric(15, 2), nullable=False)
    received_quantity = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    unit_price = db.Column(db.Numeric(15, 2), nullable=False)
    total_price = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='PENDING')  # PENDING, PARTIALLY_RECEIVED, FULLY_RECEIVED, CANCELLED
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

    __table_args__ = (
        db.CheckConstraint('ordered_quantity > 0 AND received_quantity >= 0', name='chk_biz_pol_qty'),
        db.CheckConstraint('unit_price >= 0 AND total_price >= 0', name='chk_biz_pol_prices'),
    )

    # Relationships
    product = db.relationship('BusinessProduct', backref=db.backref('purchase_order_lines', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'purchase_order_id': self.purchase_order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'product_unit': self.product.unit if self.product else None,
            'ordered_quantity': str(self.ordered_quantity),
            'received_quantity': str(self.received_quantity),
            'unit_price': str(self.unit_price),
            'total_price': str(self.total_price),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
