"""
DeadlineOS Business OS — Workspace Model
========================================
SQLAlchemy ORM model for `business_workspaces`.
Represents a multi-tenant business organization.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class Workspace(db.Model):
    """
    Represents a tenant workspace in DeadlineOS Business OS.
    """
    __tablename__ = 'business_workspaces'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    legal_name = db.Column(db.String(255), nullable=True)
    tax_identifier = db.Column(db.String(100), nullable=True)
    base_currency = db.Column(db.String(3), nullable=False, default='INR')
    timezone = db.Column(db.String(50), nullable=False, default='Asia/Kolkata')
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    members = db.relationship('WorkspaceMember', backref='workspace', lazy=True, cascade='all, delete-orphan')
    partners = db.relationship('CommercialPartner', backref='workspace', lazy=True, cascade='all, delete-orphan')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'legal_name': self.legal_name,
            'tax_identifier': self.tax_identifier,
            'base_currency': self.base_currency,
            'timezone': self.timezone,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
