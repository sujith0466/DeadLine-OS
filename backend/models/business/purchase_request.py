"""
DeadlineOS Business OS — Purchase Request Model
================================================
SQLAlchemy ORM model for `business_purchase_requests`.
Allows workspace members to request product replenishment with administrative approval gates.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessPurchaseRequest(db.Model):
    """
    Represents an internal purchase/replenishment request raised by a member or automation.
    """
    __tablename__ = 'business_purchase_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    request_number = db.Column(db.String(50), nullable=False)
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
    requested_quantity = db.Column(db.Numeric(15, 2), nullable=False)
    estimated_unit_price = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    estimated_total_price = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    priority = db.Column(db.String(20), nullable=False, default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    status = db.Column(db.String(30), nullable=False, default='SUBMITTED')  # DRAFT, SUBMITTED, APPROVED, REJECTED, ORDERED, CANCELLED
    reason = db.Column(db.Text, nullable=True)
    requested_by_user_id = db.Column(
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
    approval_notes = db.Column(db.Text, nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    purchase_order_id = db.Column(db.String(36), nullable=True, index=True)
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
        db.UniqueConstraint('workspace_id', 'request_number', name='uq_biz_pr_ws_num'),
        db.Index('idx_biz_pr_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_pr_ws_prod', 'workspace_id', 'product_id'),
        db.CheckConstraint('requested_quantity > 0', name='chk_biz_pr_qty'),
        db.CheckConstraint('estimated_unit_price >= 0 AND estimated_total_price >= 0', name='chk_biz_pr_prices'),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('purchase_requests', lazy='dynamic', cascade='all, delete-orphan'))
    product = db.relationship('BusinessProduct', backref=db.backref('purchase_requests', lazy='dynamic'))
    location = db.relationship('BusinessLocation', backref=db.backref('purchase_requests', lazy='dynamic'))
    requester = db.relationship('User', foreign_keys=[requested_by_user_id], backref=db.backref('requested_purchase_requests', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approved_by_user_id], backref=db.backref('approved_purchase_requests', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'request_number': self.request_number,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'requested_quantity': str(self.requested_quantity),
            'estimated_unit_price': str(self.estimated_unit_price),
            'estimated_total_price': str(self.estimated_total_price),
            'currency': self.currency,
            'priority': self.priority,
            'status': self.status,
            'reason': self.reason,
            'requested_by_user_id': self.requested_by_user_id,
            'requester_name': (self.requester.full_name or self.requester.email) if self.requester else None,
            'approved_by_user_id': self.approved_by_user_id,
            'approver_name': (self.approver.full_name or self.approver.email) if self.approver else None,
            'approval_notes': self.approval_notes,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'purchase_order_id': self.purchase_order_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
