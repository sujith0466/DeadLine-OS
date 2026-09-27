"""
DeadlineOS Business OS — Physical Shelf Zone Model (Phase C4.1)
===============================================================
SQLAlchemy ORM model for `business_shelf_zones`.
Represents physical shelf fixtures, racks, bins, planogram assignments,
and target facing capacities within physical locations.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessShelfZone(db.Model):
    """
    Represents a physical storage fixture, shelf tier, rack, or bin in a workspace location.
    """
    __tablename__ = 'business_shelf_zones'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    location_id = db.Column(
        db.String(36),
        db.ForeignKey('business_locations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    zone_code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    zone_type = db.Column(db.String(50), nullable=False, default='SHELF')  # SHELF, RACK, PALLET_SLOT, BIN, ENDCAP, COOLER, DISPLAY
    assigned_product_id = db.Column(
        db.String(36),
        db.ForeignKey('business_products.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    expected_capacity = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    target_facings = db.Column(db.Integer, nullable=False, default=1)
    reorder_threshold = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')  # ACTIVE, INACTIVE, MAINTENANCE
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
        db.UniqueConstraint('workspace_id', 'location_id', 'zone_code', name='uq_biz_shelf_ws_loc_code'),
        db.Index('idx_biz_shelf_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_shelf_ws_loc', 'workspace_id', 'location_id'),
        db.Index('idx_biz_shelf_ws_prod', 'workspace_id', 'assigned_product_id'),
        db.CheckConstraint("expected_capacity >= 0 AND target_facings >= 0 AND reorder_threshold >= 0", name='chk_biz_shelf_capacity'),
        db.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE')", name='chk_biz_shelf_status'),
        db.CheckConstraint("zone_type IN ('SHELF', 'RACK', 'PALLET_SLOT', 'BIN', 'ENDCAP', 'COOLER', 'DISPLAY')", name='chk_biz_shelf_type')
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('shelf_zones', lazy='dynamic', cascade='all, delete-orphan'))
    location = db.relationship('BusinessLocation', backref=db.backref('shelf_zones', lazy='dynamic', cascade='all, delete-orphan'))
    assigned_product = db.relationship('BusinessProduct', backref=db.backref('assigned_shelf_zones', lazy='dynamic'))

    def serialize(self, include_product: bool = True) -> dict:
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'zone_code': self.zone_code,
            'name': self.name,
            'zone_type': self.zone_type,
            'assigned_product_id': self.assigned_product_id,
            'expected_capacity': str(self.expected_capacity),
            'target_facings': self.target_facings,
            'reorder_threshold': str(self.reorder_threshold),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_product and self.assigned_product:
            data['assigned_product'] = {
                'id': self.assigned_product.id,
                'sku': self.assigned_product.sku,
                'name': self.assigned_product.name,
                'unit': self.assigned_product.unit
            }
        else:
            data['assigned_product'] = None
        return data
