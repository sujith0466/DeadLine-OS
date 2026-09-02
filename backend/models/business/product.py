"""
DeadlineOS Business OS — Product & SKU Model
============================================
SQLAlchemy ORM model for `business_products`.
Represents commercial products, catalog SKUs, and inventory thresholds.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessProduct(db.Model):
    """
    Represents a product/SKU catalog item in a workspace.
    """
    __tablename__ = 'business_products'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    sku = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    unit = db.Column(db.String(30), nullable=False, default='UNIT')
    is_serialized = db.Column(db.Boolean, nullable=False, default=False)
    reorder_level = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    safety_stock = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    cost_price = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    selling_price = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    preferred_supplier_partner_id = db.Column(
        db.String(36),
        db.ForeignKey('business_commercial_partners.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    created_by_user_id = db.Column(
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
        db.UniqueConstraint('workspace_id', 'sku', name='uq_biz_prod_ws_sku'),
        db.Index('idx_biz_products_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_products_ws_category', 'workspace_id', 'category'),
        db.CheckConstraint(
            "reorder_level >= 0 AND safety_stock >= 0 AND cost_price >= 0 AND selling_price >= 0",
            name='chk_biz_prod_math'
        ),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('products', lazy='dynamic', cascade='all, delete-orphan'))
    supplier = db.relationship('CommercialPartner', backref=db.backref('supplied_products', lazy='dynamic'))
    creator = db.relationship('User', backref=db.backref('created_business_products', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'sku': self.sku,
            'name': self.name,
            'category': self.category,
            'unit': self.unit,
            'reorder_level': str(self.reorder_level),
            'safety_stock': str(self.safety_stock),
            'cost_price': str(self.cost_price),
            'selling_price': str(self.selling_price),
            'currency': self.currency,
            'preferred_supplier_partner_id': self.preferred_supplier_partner_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'is_serialized': self.is_serialized,
            'status': self.status,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
