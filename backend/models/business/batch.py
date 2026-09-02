"""
DeadlineOS Business OS — Batch, Lot & Expiry Lifecycle Models
=============================================================
SQLAlchemy ORM models for `business_batches` and
`business_stock_movement_batches`.
Authoritative batch metadata, expiry tracking, and stock movement attribution.
"""

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from database.db import db


class BusinessBatch(db.Model):
    """
    Represents a specific manufacturing batch / lot of a product.
    Authoritative entity for batch lifecycle, quarantine state, and expiry tracking.
    Never stores mutable inventory balances directly (derived dynamically via stock movement attributions).
    """
    __tablename__ = 'business_batches'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey('business_products.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    batch_number = db.Column(db.String(50), nullable=False)
    supplier_partner_id = db.Column(
        db.String(36),
        db.ForeignKey('business_commercial_partners.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    goods_receipt_id = db.Column(
        db.String(36),
        db.ForeignKey('business_goods_receipts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    manufacture_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')  # ACTIVE, QUARANTINED, EXHAUSTED
    quarantine_reason = db.Column(db.Text, nullable=True)
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

    __table_args__ = (
        db.UniqueConstraint('workspace_id', 'product_id', 'batch_number', name='uq_biz_batch_ws_prod_num'),
        db.Index('idx_biz_batch_ws_prod_exp', 'workspace_id', 'product_id', 'expiry_date'),
        db.Index('idx_biz_batch_ws_status', 'workspace_id', 'status'),
    )

    product = db.relationship('BusinessProduct', lazy='joined')
    supplier = db.relationship('CommercialPartner', lazy='joined')
    goods_receipt = db.relationship('BusinessGoodsReceipt', lazy='select')

    def get_derived_status(self, warning_horizon_days: int = 30) -> str:
        """
        Determines deterministic lifecycle status based on quarantine, expiry date,
        and current date.
        """
        if self.status == 'QUARANTINED':
            return 'QUARANTINED'
        today = datetime.now(timezone.utc).date()
        if self.expiry_date and today > self.expiry_date:
            return 'EXPIRED'
        if self.status == 'EXHAUSTED':
            return 'EXHAUSTED'
        if self.expiry_date and today <= self.expiry_date:
            from datetime import timedelta
            if self.expiry_date <= (today + timedelta(days=warning_horizon_days)):
                return 'EXPIRING_SOON'
        return 'ACTIVE'

    def serialize(self, available_quantity: Decimal = None) -> dict:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'batch_number': self.batch_number,
            'product_id': self.product_id,
            'product_sku': self.product.sku if self.product else None,
            'product_name': self.product.name if self.product else None,
            'product_unit': self.product.unit if self.product else None,
            'supplier_partner_id': self.supplier_partner_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'goods_receipt_id': self.goods_receipt_id,
            'manufacture_date': self.manufacture_date.isoformat() if self.manufacture_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status,
            'derived_status': self.get_derived_status(),
            'quarantine_reason': self.quarantine_reason,
            'notes': self.notes,
            'available_quantity': str(available_quantity) if available_quantity is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BusinessStockMovementBatch(db.Model):
    """
    Attribution ledger linking an authoritative stock movement to one or more batches.
    Guarantees: SUM(attributions for movement) == stock_movement.quantity.
    """
    __tablename__ = 'business_stock_movement_batches'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    stock_movement_id = db.Column(
        db.String(36),
        db.ForeignKey('business_stock_movements.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    batch_id = db.Column(
        db.String(36),
        db.ForeignKey('business_batches.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    quantity = db.Column(db.Numeric(15, 2), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint('stock_movement_id', 'batch_id', name='uq_biz_sm_batch'),
        db.CheckConstraint('quantity > 0', name='chk_biz_sm_batch_qty'),
        db.Index('idx_biz_sm_batch_ws_batch', 'workspace_id', 'batch_id'),
    )

    stock_movement = db.relationship('BusinessStockMovement', backref=db.backref('batch_attributions', cascade='all, delete-orphan', lazy='joined'))
    batch = db.relationship('BusinessBatch', backref=db.backref('movement_attributions', lazy='dynamic'))

    def serialize(self) -> dict:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'stock_movement_id': self.stock_movement_id,
            'batch_id': self.batch_id,
            'quantity': str(self.quantity),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
