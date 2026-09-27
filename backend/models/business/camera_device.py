"""
DeadlineOS Business OS — Camera Device Model (Phase C4.5)
=========================================================
SQLAlchemy ORM model for `business_camera_devices`.
Represents ambient camera sensors, shelf cameras, overhead monitors,
and mobile scanning edge devices paired to workspace locations.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessCameraDevice(db.Model):
    """
    Represents a registered optical camera or edge device capturing visual telemetry.
    """
    __tablename__ = 'business_camera_devices'

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
    device_code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(50), nullable=False, default='SHELF_EDGE')
    # FIXED_OVERHEAD, SHELF_EDGE, MOBILE_TERMINAL
    api_key_hash = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True)
    # ACTIVE, INACTIVE, PAUSED
    firmware_version = db.Column(db.String(50), nullable=True)
    last_heartbeat_at = db.Column(db.DateTime(timezone=True), nullable=True)
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
        db.UniqueConstraint('workspace_id', 'device_code', name='uq_biz_cam_dev_ws_code'),
        db.Index('idx_biz_cam_dev_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_cam_dev_ws_loc', 'workspace_id', 'location_id'),
        db.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'PAUSED')", name='chk_biz_cam_dev_status'),
        db.CheckConstraint("device_type IN ('FIXED_OVERHEAD', 'SHELF_EDGE', 'MOBILE_TERMINAL')", name='chk_biz_cam_dev_type')
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('camera_devices', lazy='dynamic', cascade='all, delete-orphan'))
    location = db.relationship('BusinessLocation', backref=db.backref('camera_devices', lazy='dynamic', cascade='all, delete-orphan'))

    def serialize(self, include_token: bool = False) -> dict:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'device_code': self.device_code,
            'name': self.name,
            'device_type': self.device_type,
            'status': self.status,
            'firmware_version': self.firmware_version,
            'last_heartbeat_at': self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
