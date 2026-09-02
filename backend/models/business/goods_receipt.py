"""
DeadlineOS Business OS — Goods Receipt Models (Phase C2.2)
===========================================================
SQLAlchemy ORM models for `business_goods_receipts` and `business_goods_receipt_lines`.
Represents physical goods delivery, quality inspection, accepted/rejected quantities,
and physical stock movement bridging.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessGoodsReceipt(db.Model):
    """
    Represents a Goods Receipt Note (GRN) recording the physical delivery of items
    against an approved/sent Purchase Order.
    """
    __tablename__ = 'business_goods_receipts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    grn_number = db.Column(db.String(50), nullable=False)
    purchase_order_id = db.Column(
        db.String(36),
        db.ForeignKey('business_purchase_orders.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
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
    receipt_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    carrier_name = db.Column(db.String(100), nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    delivery_note_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='COMPLETED')  # COMPLETED, CANCELLED
    notes = db.Column(db.Text, nullable=True)
    staged_extraction_id = db.Column(
        db.String(36),
        db.ForeignKey('business_staged_extractions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    received_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
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

    __table_args__ = (
        db.UniqueConstraint('workspace_id', 'grn_number', name='uq_biz_grn_ws_num'),
        db.Index('idx_biz_grn_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_grn_ws_po', 'workspace_id', 'purchase_order_id'),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('goods_receipts', lazy='dynamic', cascade='all, delete-orphan'))
    purchase_order = db.relationship('BusinessPurchaseOrder', backref=db.backref('goods_receipts', lazy='dynamic'))
    supplier = db.relationship('CommercialPartner', backref=db.backref('goods_receipts', lazy='dynamic'))
    destination_location = db.relationship('BusinessLocation', backref=db.backref('goods_receipts', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[received_by_user_id], backref=db.backref('received_goods_receipts', lazy='dynamic'))
    staged_extraction = db.relationship('StagedExtraction', backref=db.backref('originating_goods_receipts', lazy='dynamic'))
    lines = db.relationship('BusinessGoodsReceiptLine', backref='goods_receipt', lazy='joined', cascade='all, delete-orphan')

    def serialize(self, include_lines=True):
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'grn_number': self.grn_number,
            'purchase_order_id': self.purchase_order_id,
            'po_number': self.purchase_order.po_number if self.purchase_order else None,
            'supplier_partner_id': self.supplier_partner_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'destination_location_id': self.destination_location_id,
            'destination_location_name': self.destination_location.name if self.destination_location else None,
            'receipt_date': self.receipt_date.isoformat() if self.receipt_date else None,
            'carrier_name': self.carrier_name,
            'tracking_number': self.tracking_number,
            'delivery_note_number': self.delivery_note_number,
            'status': self.status,
            'notes': self.notes,
            'staged_extraction_id': self.staged_extraction_id,
            'received_by_user_id': self.received_by_user_id,
            'receiver_name': (self.receiver.full_name or self.receiver.email) if self.receiver else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_lines:
            data['lines'] = [line.serialize() for line in (self.lines or [])]
        return data


class BusinessGoodsReceiptLine(db.Model):
    """
    Represents an individual product delivery line within a Goods Receipt Note.
    Records physical quantity received, accepted quantity, and rejected quantity.
    """
    __tablename__ = 'business_goods_receipt_lines'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goods_receipt_id = db.Column(
        db.String(36),
        db.ForeignKey('business_goods_receipts.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    purchase_order_line_id = db.Column(
        db.String(36),
        db.ForeignKey('business_purchase_order_lines.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey('business_products.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    received_quantity = db.Column(db.Numeric(15, 2), nullable=False)
    accepted_quantity = db.Column(db.Numeric(15, 2), nullable=False)
    rejected_quantity = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    rejection_reason = db.Column(db.Text, nullable=True)
    unit_cost = db.Column(db.Numeric(15, 2), nullable=False)
    stock_movement_id = db.Column(
        db.String(36),
        db.ForeignKey('business_stock_movements.id', ondelete='SET NULL'),
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

    __table_args__ = (
        db.CheckConstraint(
            'received_quantity >= 0 AND accepted_quantity >= 0 AND rejected_quantity >= 0 AND (accepted_quantity + rejected_quantity = received_quantity)',
            name='chk_biz_grnl_quantities'
        ),
        db.CheckConstraint('unit_cost >= 0', name='chk_biz_grnl_unit_cost'),
    )

    # Relationships
    purchase_order_line = db.relationship('BusinessPurchaseOrderLine', backref=db.backref('receipt_lines', lazy='dynamic'))
    product = db.relationship('BusinessProduct', backref=db.backref('goods_receipt_lines', lazy='dynamic'))
    stock_movement = db.relationship('BusinessStockMovement', backref=db.backref('originating_receipt_line', uselist=False))

    def serialize(self):
        return {
            'id': self.id,
            'goods_receipt_id': self.goods_receipt_id,
            'purchase_order_line_id': self.purchase_order_line_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'product_unit': self.product.unit if self.product else None,
            'received_quantity': str(self.received_quantity),
            'accepted_quantity': str(self.accepted_quantity),
            'rejected_quantity': str(self.rejected_quantity),
            'rejection_reason': self.rejection_reason,
            'unit_cost': str(self.unit_cost),
            'stock_movement_id': self.stock_movement_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }