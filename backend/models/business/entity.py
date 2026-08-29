"""
DeadlineOS Business OS — Multi-Entity & Inter-Entity Transfer Models
===================================================================
Models for legal operating entities, subsidiaries, and cross-entity transfers.
"""

from database.db import db
from datetime import datetime, timezone, date
import uuid


class BusinessEntity(db.Model):
    __tablename__ = 'business_entities'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False)
    legal_name = db.Column(db.String(255), nullable=True)
    entity_code = db.Column(db.String(50), nullable=True)
    tax_identifier = db.Column(db.String(100), nullable=True)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')  # 'ACTIVE', 'INACTIVE'

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('entities', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'name': self.name,
            'legal_name': self.legal_name,
            'entity_code': self.entity_code,
            'tax_identifier': self.tax_identifier,
            'currency': self.currency,
            'is_default': self.is_default,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class InterEntityTransfer(db.Model):
    __tablename__ = 'business_inter_entity_transfers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    source_entity_id = db.Column(db.String(36), db.ForeignKey('business_entities.id', ondelete='SET NULL'), nullable=True, index=True)

    destination_workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    destination_entity_id = db.Column(db.String(36), db.ForeignKey('business_entities.id', ondelete='SET NULL'), nullable=True, index=True)

    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    transfer_date = db.Column(db.Date, nullable=False, default=date.today)
    reference_note = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='SETTLED')  # 'PENDING', 'SETTLED', 'CANCELLED'

    created_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    source_workspace = db.relationship('Workspace', foreign_keys=[source_workspace_id])
    destination_workspace = db.relationship('Workspace', foreign_keys=[destination_workspace_id])
    source_entity = db.relationship('BusinessEntity', foreign_keys=[source_entity_id])
    destination_entity = db.relationship('BusinessEntity', foreign_keys=[destination_entity_id])

    def to_dict(self):
        return {
            'id': self.id,
            'source_workspace_id': self.source_workspace_id,
            'source_entity_id': self.source_entity_id,
            'source_entity_name': self.source_entity.name if self.source_entity else None,
            'destination_workspace_id': self.destination_workspace_id,
            'destination_entity_id': self.destination_entity_id,
            'destination_entity_name': self.destination_entity.name if self.destination_entity else None,
            'amount': str(self.amount),
            'currency': self.currency,
            'transfer_date': self.transfer_date.isoformat() if self.transfer_date else None,
            'reference_note': self.reference_note,
            'status': self.status,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
