"""
DeadlineOS Business OS — Cross-Border Shipment Models (Phase C3.5)
==================================================================
SQLAlchemy ORM model for `business_cross_border_shipments`.
Represents international shipments, bills of lading, ports, customs clearance,
and carrier logistics correlated with POs, GRNs, and Landed Cost Vouchers.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from database.db import db


class BusinessCrossBorderShipment(db.Model):
    """
    Represents an international freight consignment bridging suppliers,
    customs declarations, transit milestones, and receiving warehouses.
    """
    __tablename__ = 'business_cross_border_shipments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    shipment_number = db.Column(db.String(50), nullable=False)
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
    landed_cost_voucher_id = db.Column(
        db.String(36),
        db.ForeignKey('business_landed_cost_vouchers.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    supplier_partner_id = db.Column(
        db.String(36),
        db.ForeignKey('business_commercial_partners.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    origin_country = db.Column(db.String(3), nullable=False)
    destination_country = db.Column(db.String(3), nullable=False)
    carrier_name = db.Column(db.String(100), nullable=True)
    transport_mode = db.Column(db.String(30), nullable=False, default='OCEAN')
    tracking_number = db.Column(db.String(100), nullable=True)
    bill_of_lading_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='PLANNED')
    customs_reference = db.Column(db.String(100), nullable=True)
    customs_status = db.Column(db.String(30), nullable=False, default='PENDING')
    declared_customs_value = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    declared_currency = db.Column(db.String(3), nullable=False, default='USD')
    estimated_departure_date = db.Column(db.Date, nullable=True)
    actual_departure_date = db.Column(db.Date, nullable=True)
    estimated_arrival_date = db.Column(db.Date, nullable=True)
    actual_arrival_date = db.Column(db.Date, nullable=True)
    customs_clearance_date = db.Column(db.Date, nullable=True)
    port_of_loading = db.Column(db.String(100), nullable=True)
    port_of_entry = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
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
        db.UniqueConstraint('workspace_id', 'shipment_number', name='uq_biz_cbs_ws_num'),
        db.CheckConstraint("status IN ('PLANNED', 'BOOKED', 'IN_TRANSIT', 'CUSTOMS_HOLD', 'CUSTOMS_CLEARED', 'DELIVERED', 'CANCELLED')", name='chk_biz_cbs_status'),
        db.CheckConstraint("customs_status IN ('PENDING', 'SUBMITTED', 'INSPECTION', 'CLEARED', 'REJECTED')", name='chk_biz_cbs_customs_status'),
        db.CheckConstraint("transport_mode IN ('OCEAN', 'AIR', 'ROAD', 'RAIL', 'MULTIMODAL')", name='chk_biz_cbs_mode'),
        db.CheckConstraint("declared_customs_value >= 0", name='chk_biz_cbs_value'),
        db.Index('idx_biz_cbs_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_cbs_ws_po', 'workspace_id', 'purchase_order_id'),
        db.Index('idx_biz_cbs_ws_grn', 'workspace_id', 'goods_receipt_id'),
        db.Index('idx_biz_cbs_ws_lcv', 'workspace_id', 'landed_cost_voucher_id'),
        db.Index('idx_biz_cbs_ws_supp', 'workspace_id', 'supplier_partner_id'),
    )

    # Relationships
    purchase_order = db.relationship('BusinessPurchaseOrder', lazy='select')
    goods_receipt = db.relationship('BusinessGoodsReceipt', lazy='select')
    landed_cost_voucher = db.relationship('BusinessLandedCostVoucher', lazy='select')
    supplier = db.relationship('CommercialPartner', lazy='select')
    creator = db.relationship('User', foreign_keys=[created_by_user_id], lazy='select')

    def is_active(self) -> bool:
        return self.status in ('PLANNED', 'BOOKED', 'IN_TRANSIT', 'CUSTOMS_HOLD')

    def is_cleared(self) -> bool:
        return self.customs_status == 'CLEARED' or self.status in ('CUSTOMS_CLEARED', 'DELIVERED')

    def serialize(self, include_relations: bool = False):
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'shipment_number': self.shipment_number,
            'purchase_order_id': self.purchase_order_id,
            'po_number': self.purchase_order.po_number if self.purchase_order else None,
            'goods_receipt_id': self.goods_receipt_id,
            'grn_number': self.goods_receipt.grn_number if self.goods_receipt else None,
            'landed_cost_voucher_id': self.landed_cost_voucher_id,
            'lcv_number': self.landed_cost_voucher.voucher_number if self.landed_cost_voucher else None,
            'supplier_partner_id': self.supplier_partner_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'origin_country': self.origin_country,
            'destination_country': self.destination_country,
            'carrier_name': self.carrier_name,
            'transport_mode': self.transport_mode,
            'tracking_number': self.tracking_number,
            'bill_of_lading_number': self.bill_of_lading_number,
            'status': self.status,
            'customs_reference': self.customs_reference,
            'customs_status': self.customs_status,
            'declared_customs_value': str(self.declared_customs_value),
            'declared_currency': self.declared_currency,
            'estimated_departure_date': self.estimated_departure_date.isoformat() if self.estimated_departure_date else None,
            'actual_departure_date': self.actual_departure_date.isoformat() if self.actual_departure_date else None,
            'estimated_arrival_date': self.estimated_arrival_date.isoformat() if self.estimated_arrival_date else None,
            'actual_arrival_date': self.actual_arrival_date.isoformat() if self.actual_arrival_date else None,
            'customs_clearance_date': self.customs_clearance_date.isoformat() if self.customs_clearance_date else None,
            'port_of_loading': self.port_of_loading,
            'port_of_entry': self.port_of_entry,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data['purchase_order'] = self.purchase_order.serialize(include_lines=True) if self.purchase_order else None
            data['goods_receipt'] = self.goods_receipt.serialize(include_lines=True) if self.goods_receipt else None
            data['landed_cost_voucher'] = self.landed_cost_voucher.serialize(include_items=True, include_allocations=True) if self.landed_cost_voucher else None
        return data
