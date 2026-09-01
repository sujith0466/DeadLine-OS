"""
DeadlineOS Business OS — Physical Business Location Model
=========================================================
SQLAlchemy ORM model for `business_locations`.
Represents physical operating facilities, stores, warehouses, and branches.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessLocation(db.Model):
    """
    Represents a physical operating location (Warehouse, Store, Branch, Office, Storage) in a workspace.
    """
    __tablename__ = 'business_locations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    entity_id = db.Column(
        db.String(36),
        db.ForeignKey('business_entities.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    name = db.Column(db.String(255), nullable=False)
    location_type = db.Column(db.String(50), nullable=False, default='WAREHOUSE')
    address = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
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
        db.UniqueConstraint('workspace_id', 'name', name='uq_biz_loc_ws_name'),
        db.Index('idx_biz_locations_ws_status', 'workspace_id', 'status'),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('locations', lazy='dynamic', cascade='all, delete-orphan'))
    entity = db.relationship('BusinessEntity', backref=db.backref('locations', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'entity_id': self.entity_id,
            'entity_name': self.entity.name if self.entity else None,
            'name': self.name,
            'location_type': self.location_type,
            'address': self.address,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
