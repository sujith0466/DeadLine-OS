"""
DeadlineOS Business OS — Stock Movement Ledger Model
====================================================
SQLAlchemy ORM model for `business_stock_movements`.
Append-only, immutable authoritative inventory movement ledger.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessStockMovement(db.Model):
    """
    Represents an immutable, append-only stock movement entry.
    Authoritative source of truth for all operational inventory changes.
    """
    __tablename__ = 'business_stock_movements'

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
    location_id = db.Column(
        db.String(36),
        db.ForeignKey('business_locations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    movement_type = db.Column(db.String(30), nullable=False)  # INITIAL_STOCK, PURCHASE_RECEIVED, SALE, TRANSFER_IN, TRANSFER_OUT, DAMAGED, RETURN, MANUAL_ADJUSTMENT
    direction = db.Column(db.String(10), nullable=False)  # IN, OUT
    quantity = db.Column(db.Numeric(15, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(15, 2), nullable=True)
    reference_type = db.Column(db.String(50), nullable=True)  # INVOICE, STAGED_EXTRACTION, TRANSFER_BATCH, PHYSICAL_AUDIT
    reference_id = db.Column(db.String(36), nullable=True, index=True)
    transfer_batch_id = db.Column(db.String(36), nullable=True, index=True)
    staged_extraction_id = db.Column(
        db.String(36),
        db.ForeignKey('business_staged_extractions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    actor_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    __table_args__ = (
        db.Index('idx_biz_sm_ws_prod_loc', 'workspace_id', 'product_id', 'location_id'),
        db.CheckConstraint("direction IN ('IN', 'OUT')", name='chk_biz_sm_dir'),
        db.CheckConstraint("quantity > 0", name='chk_biz_sm_qty'),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('stock_movements', lazy='dynamic', cascade='all, delete-orphan'))
    product = db.relationship('BusinessProduct', backref=db.backref('stock_movements', lazy='dynamic', cascade='all, delete-orphan'))
    location = db.relationship('BusinessLocation', backref=db.backref('stock_movements', lazy='dynamic', cascade='all, delete-orphan'))
    actor = db.relationship('User', backref=db.backref('recorded_stock_movements', lazy='dynamic'))
    staged_extraction = db.relationship('StagedExtraction', backref=db.backref('committed_stock_movements', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'movement_type': self.movement_type,
            'direction': self.direction,
            'quantity': str(self.quantity),
            'unit_cost': str(self.unit_cost) if self.unit_cost is not None else None,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'transfer_batch_id': self.transfer_batch_id,
            'staged_extraction_id': self.staged_extraction_id,
            'actor_user_id': self.actor_user_id,
            'actor_name': self.actor.full_name if self.actor and self.actor.full_name else (self.actor.email if self.actor else None),
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
