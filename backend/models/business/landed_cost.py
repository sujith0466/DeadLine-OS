"""
DeadlineOS Business OS — Landed Cost Models (Phase C3.4)
=========================================================
SQLAlchemy ORM models for landed cost vouchers, itemized acquisition costs,
and line-level proportional allocations.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from database.db import db


class BusinessLandedCostVoucher(db.Model):
    """
    Represents an operational Landed Cost Voucher consolidating international
    freight, customs, tariffs, and handling overhead for received procurement lines.
    """
    __tablename__ = 'business_landed_cost_vouchers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    voucher_number = db.Column(db.String(50), nullable=False)
    reference_number = db.Column(db.String(100), nullable=True)
    purchase_order_id = db.Column(
        db.String(36),
        db.ForeignKey('business_purchase_orders.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    goods_receipt_id = db.Column(
        db.String(36),
        db.ForeignKey('business_goods_receipts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    currency = db.Column(db.String(3), nullable=False, default='INR')
    base_currency = db.Column(db.String(3), nullable=False, default='INR')
    exchange_rate = db.Column(db.Numeric(18, 6), nullable=False, default=Decimal('1.000000'))
    effective_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    allocation_basis = db.Column(db.String(30), nullable=False, default='VALUE')
    status = db.Column(db.String(30), nullable=False, default='DRAFT')
    total_cost_source_currency = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    total_cost_base_currency = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    allocated_total_base_currency = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    approved_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reversed_by_voucher_id = db.Column(
        db.String(36),
        db.ForeignKey('business_landed_cost_vouchers.id', ondelete='SET NULL'),
        nullable=True
    )
    reversal_reason = db.Column(db.Text, nullable=True)
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
        db.UniqueConstraint('workspace_id', 'voucher_number', name='uq_biz_lcv_ws_num'),
        db.CheckConstraint("status IN ('DRAFT', 'ALLOCATED', 'APPROVED', 'REVERSED')", name='chk_biz_lcv_status'),
        db.CheckConstraint("allocation_basis IN ('VALUE', 'QUANTITY')", name='chk_biz_lcv_basis'),
        db.CheckConstraint("total_cost_source_currency >= 0 AND total_cost_base_currency >= 0 AND allocated_total_base_currency >= 0", name='chk_biz_lcv_amounts'),
        db.Index('idx_biz_lcv_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_lcv_ws_po', 'workspace_id', 'purchase_order_id'),
        db.Index('idx_biz_lcv_ws_grn', 'workspace_id', 'goods_receipt_id'),
    )

    # Relationships
    purchase_order = db.relationship('BusinessPurchaseOrder', lazy='select')
    goods_receipt = db.relationship('BusinessGoodsReceipt', lazy='select')
    creator = db.relationship('User', foreign_keys=[created_by_user_id], lazy='select')
    approver = db.relationship('User', foreign_keys=[approved_by_user_id], lazy='select')
    items = db.relationship('BusinessLandedCostVoucherItem', backref='voucher', cascade='all, delete-orphan', lazy='select')
    allocations = db.relationship('BusinessLandedCostAllocation', backref='voucher', cascade='all, delete-orphan', lazy='select')

    def can_edit(self) -> bool:
        return self.status == 'DRAFT'

    def can_allocate(self) -> bool:
        return self.status in ('DRAFT', 'ALLOCATED')

    def can_approve(self) -> bool:
        return self.status == 'ALLOCATED'

    def can_reverse(self) -> bool:
        return self.status == 'APPROVED'

    def serialize(self, include_items: bool = False, include_allocations: bool = False):
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'voucher_number': self.voucher_number,
            'reference_number': self.reference_number,
            'purchase_order_id': self.purchase_order_id,
            'po_number': self.purchase_order.po_number if self.purchase_order else None,
            'goods_receipt_id': self.goods_receipt_id,
            'grn_number': self.goods_receipt.grn_number if self.goods_receipt else None,
            'currency': self.currency,
            'base_currency': self.base_currency,
            'exchange_rate': str(self.exchange_rate),
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'allocation_basis': self.allocation_basis,
            'status': self.status,
            'total_cost_source_currency': str(self.total_cost_source_currency),
            'total_cost_base_currency': str(self.total_cost_base_currency),
            'allocated_total_base_currency': str(self.allocated_total_base_currency),
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'approved_by_user_id': self.approved_by_user_id,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'reversed_by_voucher_id': self.reversed_by_voucher_id,
            'reversal_reason': self.reversal_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            data['items'] = [item.serialize() for item in (self.items or [])]
        if include_allocations:
            data['allocations'] = [alloc.serialize() for alloc in (self.allocations or [])]
        return data


class BusinessLandedCostVoucherItem(db.Model):
    """
    Represents an itemized acquisition or logistics expenditure within a Landed Cost Voucher.
    """
    __tablename__ = 'business_landed_cost_voucher_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    voucher_id = db.Column(
        db.String(36),
        db.ForeignKey('business_landed_cost_vouchers.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    cost_category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    exchange_rate = db.Column(db.Numeric(18, 6), nullable=False, default=Decimal('1.000000'))
    base_currency_amount = db.Column(db.Numeric(15, 2), nullable=False)
    external_reference = db.Column(db.String(100), nullable=True)
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
        db.CheckConstraint("amount > 0 AND base_currency_amount > 0", name='chk_biz_lcvi_amount'),
        db.CheckConstraint("cost_category IN ('FREIGHT', 'CUSTOMS', 'DUTIES', 'INSURANCE', 'HANDLING', 'BROKERAGE', 'PORT_CHARGES', 'STORAGE', 'OTHER')", name='chk_biz_lcvi_category'),
        db.Index('idx_biz_lcvi_ws_voucher', 'workspace_id', 'voucher_id'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'voucher_id': self.voucher_id,
            'cost_category': self.cost_category,
            'description': self.description,
            'amount': str(self.amount),
            'currency': self.currency,
            'exchange_rate': str(self.exchange_rate),
            'base_currency_amount': str(self.base_currency_amount),
            'external_reference': self.external_reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BusinessLandedCostAllocation(db.Model):
    """
    Represents the derived cost apportionment assigned to an accepted Goods Receipt line.
    """
    __tablename__ = 'business_landed_cost_allocations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    voucher_id = db.Column(
        db.String(36),
        db.ForeignKey('business_landed_cost_vouchers.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    goods_receipt_line_id = db.Column(
        db.String(36),
        db.ForeignKey('business_goods_receipt_lines.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey('business_products.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    accepted_quantity = db.Column(db.Numeric(15, 2), nullable=False)
    line_base_value = db.Column(db.Numeric(15, 2), nullable=False)
    allocation_weight = db.Column(db.Numeric(18, 8), nullable=False)
    allocated_cost_base_currency = db.Column(db.Numeric(15, 2), nullable=False)
    landed_cost_per_unit = db.Column(db.Numeric(15, 4), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint('voucher_id', 'goods_receipt_line_id', name='uq_biz_lca_voucher_line'),
        db.CheckConstraint("allocated_cost_base_currency >= 0 AND landed_cost_per_unit >= 0", name='chk_biz_lca_amounts'),
        db.Index('idx_biz_lca_ws_voucher', 'workspace_id', 'voucher_id'),
        db.Index('idx_biz_lca_ws_grnl', 'workspace_id', 'goods_receipt_line_id'),
        db.Index('idx_biz_lca_ws_prod', 'workspace_id', 'product_id'),
    )

    # Relationships
    goods_receipt_line = db.relationship('BusinessGoodsReceiptLine', lazy='select')
    product = db.relationship('BusinessProduct', lazy='select')

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'voucher_id': self.voucher_id,
            'goods_receipt_line_id': self.goods_receipt_line_id,
            'product_id': self.product_id,
            'product_sku': self.product.sku if self.product else None,
            'product_name': self.product.name if self.product else None,
            'accepted_quantity': str(self.accepted_quantity),
            'line_base_value': str(self.line_base_value),
            'allocation_weight': str(self.allocation_weight),
            'allocated_cost_base_currency': str(self.allocated_cost_base_currency),
            'landed_cost_per_unit': str(self.landed_cost_per_unit),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
