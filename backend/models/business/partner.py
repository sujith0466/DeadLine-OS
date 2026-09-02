"""
DeadlineOS Business OS — Commercial Partner Model
=================================================
SQLAlchemy ORM model for `business_commercial_partners`.
Stores Customer and Supplier entities.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class CommercialPartner(db.Model):
    """
    Represents a commercial counterparty (Customer, Supplier, or Both) in a workspace.
    """
    __tablename__ = 'business_commercial_partners'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    partner_type = db.Column(db.String(20), nullable=False)  # 'CUSTOMER', 'SUPPLIER', 'BOTH'
    name = db.Column(db.String(255), nullable=False)
    legal_name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    tax_identifier = db.Column(db.String(100), nullable=True)
    credit_period_days = db.Column(db.Integer, nullable=False, default=30)
    default_currency = db.Column(db.String(3), nullable=False, default='INR')
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_biz_partners_ws_type_status', 'workspace_id', 'partner_type', 'status'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'partner_type': self.partner_type,
            'name': self.name,
            'legal_name': self.legal_name,
            'phone': self.phone,
            'email': self.email,
            'tax_identifier': self.tax_identifier,
            'credit_period_days': self.credit_period_days,
            'default_currency': self.default_currency,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
