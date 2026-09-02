"""
DeadlineOS Business OS — Serial Number Tracking & Unit Provenance Models
========================================================================
SQLAlchemy ORM models for `business_serial_numbers` and
`business_stock_movement_serials`.
Authoritative unit-level provenance registry and stock movement attributions.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessSerialNumber(db.Model):
    """
    Represents an individually serialized physical unit of a product.
    Authoritative entity for unit-level provenance, single-location invariant,
    and deterministic lifecycle state tracking.
    Never acts as a competing quantity ledger; quantity is derived strictly
    from business_stock_movements.
    """
    __tablename__ = 'business_serial_numbers'

    VALID_STATUSES = ('IN_STOCK', 'ALLOCATED', 'SHIPPED', 'CONSUMED', 'DEFECTIVE', 'DISPOSED')

    # Allowed state machine transitions: current_status -> set(valid_next_statuses)
    ALLOWED_TRANSITIONS = {
        'IN_STOCK': {'ALLOCATED', 'SHIPPED', 'DEFECTIVE', 'DISPOSED'},
        'ALLOCATED': {'IN_STOCK', 'SHIPPED', 'DEFECTIVE'},
        'SHIPPED': {'CONSUMED', 'DEFECTIVE'},  # e.g., returned defective
        'CONSUMED': set(),                      # Terminal state
        'DEFECTIVE': {'DISPOSED', 'IN_STOCK'},  # e.g., repaired/recertified -> IN_STOCK, or scrapped -> DISPOSED
        'DISPOSED': set(),                      # Terminal state
    }

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
    serial_number = db.Column(db.String(100), nullable=False)
    batch_id = db.Column(
        db.String(36),
        db.ForeignKey('business_batches.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    goods_receipt_id = db.Column(
        db.String(36),
        db.ForeignKey('business_goods_receipts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    current_location_id = db.Column(
        db.String(36),
        db.ForeignKey('business_locations.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    status = db.Column(db.String(20), nullable=False, default='IN_STOCK')
    received_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    allocated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    shipped_at = db.Column(db.DateTime(timezone=True), nullable=True)
    consumed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    defective_at = db.Column(db.DateTime(timezone=True), nullable=True)
    disposed_at = db.Column(db.DateTime(timezone=True), nullable=True)
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
        db.UniqueConstraint('workspace_id', 'product_id', 'serial_number', name='uq_biz_serial_ws_prod_num'),
        db.CheckConstraint(
            "status IN ('IN_STOCK', 'ALLOCATED', 'SHIPPED', 'CONSUMED', 'DEFECTIVE', 'DISPOSED')",
            name='chk_biz_serial_status'
        ),
        db.Index('idx_biz_serial_ws_prod_status', 'workspace_id', 'product_id', 'status'),
        db.Index('idx_biz_serial_ws_batch', 'workspace_id', 'batch_id'),
        db.Index('idx_biz_serial_ws_loc', 'workspace_id', 'current_location_id'),
    )

    product = db.relationship('BusinessProduct', lazy='select')
    batch = db.relationship('BusinessBatch', lazy='select')
    goods_receipt = db.relationship('BusinessGoodsReceipt', lazy='select')
    current_location = db.relationship('BusinessLocation', lazy='select')

    def can_transition_to(self, target_status: str) -> bool:
        """Checks if transition from self.status to target_status is permitted."""
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, set())
        return target_status in allowed

    def serialize(self, include_provenance: bool = False) -> dict:
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'product_id': self.product_id,
            'product_sku': self.product.sku if self.product else None,
            'product_name': self.product.name if self.product else None,
            'serial_number': self.serial_number,
            'batch_id': self.batch_id,
            'batch_number': self.batch.batch_number if self.batch else None,
            'goods_receipt_id': self.goods_receipt_id,
            'current_location_id': self.current_location_id,
            'current_location_name': self.current_location.name if self.current_location else None,
            'status': self.status,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'allocated_at': self.allocated_at.isoformat() if self.allocated_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'consumed_at': self.consumed_at.isoformat() if self.consumed_at else None,
            'defective_at': self.defective_at.isoformat() if self.defective_at else None,
            'disposed_at': self.disposed_at.isoformat() if self.disposed_at else None,
            'quarantine_reason': self.quarantine_reason,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        return data


class BusinessStockMovementSerial(db.Model):
    """
    Attribution ledger linking an authoritative stock movement to one or more serial numbers.
    Guarantees: Count of serialized units attributed == stock_movement.quantity.
    """
    __tablename__ = 'business_stock_movement_serials'

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
    serial_id = db.Column(
        db.String(36),
        db.ForeignKey('business_serial_numbers.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint('stock_movement_id', 'serial_id', name='uq_biz_sm_serial'),
        db.Index('idx_biz_sm_serial_ws_sm', 'workspace_id', 'stock_movement_id'),
        db.Index('idx_biz_sm_serial_ws_serial', 'workspace_id', 'serial_id'),
    )

    stock_movement = db.relationship('BusinessStockMovement', backref=db.backref('serial_attributions', cascade='all, delete-orphan', lazy='joined'))
    serial = db.relationship('BusinessSerialNumber', backref=db.backref('movement_attributions', lazy='dynamic'))

    def serialize(self) -> dict:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'stock_movement_id': self.stock_movement_id,
            'serial_id': self.serial_id,
            'serial_number': self.serial.serial_number if self.serial else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
