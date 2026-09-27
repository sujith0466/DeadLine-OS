"""
DeadlineOS Business OS — Camera Calibration Model (Phase C4.5)
==============================================================
SQLAlchemy ORM model for `business_camera_calibrations`.
Represents normalized geometric ROI bounding polygons, facing partition grids,
and projective homographies mapping 2D viewport coordinates to `BusinessShelfZone` fixtures.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessCameraCalibration(db.Model):
    """
    Represents an optical calibration profile linking a camera device to a physical shelf zone.
    Maintains strict monotonic versioning and ACTIVE/SUPERSEDED lifecycle.
    """
    __tablename__ = 'business_camera_calibrations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    camera_device_id = db.Column(
        db.String(36),
        db.ForeignKey('business_camera_devices.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    shelf_zone_id = db.Column(
        db.String(36),
        db.ForeignKey('business_shelf_zones.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    calibration_version = db.Column(db.Integer, nullable=False, default=1)
    roi_polygon = db.Column(db.JSON, nullable=False)  # Array of [[x0, y0], [x1, y1], ...] normalized [0,1]
    facing_divisions = db.Column(db.JSON, nullable=False, default=list)  # Array of split boundaries [0.25, 0.50, ...]
    homography_matrix = db.Column(db.JSON, nullable=True)  # Optional 3x3 transformation matrix

    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True)  # ACTIVE, SUPERSEDED

    calibrated_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
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
        db.UniqueConstraint('workspace_id', 'camera_device_id', 'shelf_zone_id', 'calibration_version', name='uq_biz_cam_calib_ver'),
        db.Index('idx_biz_cam_calib_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_cam_calib_dev', 'workspace_id', 'camera_device_id'),
        db.Index('idx_biz_cam_calib_zone', 'workspace_id', 'shelf_zone_id'),
        db.CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED')", name='chk_biz_cam_calib_status'),
        db.CheckConstraint("calibration_version >= 1", name='chk_biz_cam_calib_ver')
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('camera_calibrations', lazy='dynamic', cascade='all, delete-orphan'))
    camera_device = db.relationship('BusinessCameraDevice', backref=db.backref('calibrations', lazy='dynamic', cascade='all, delete-orphan'))
    shelf_zone = db.relationship('BusinessShelfZone', backref=db.backref('camera_calibrations', lazy='dynamic', cascade='all, delete-orphan'))
    calibrator = db.relationship('User', foreign_keys=[calibrated_by_user_id], backref=db.backref('calibrated_profiles', lazy='dynamic'))

    def serialize(self, include_relations: bool = True) -> dict:
        data = {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'camera_device_id': self.camera_device_id,
            'camera_device_code': self.camera_device.device_code if self.camera_device else None,
            'camera_device_name': self.camera_device.name if self.camera_device else None,
            'shelf_zone_id': self.shelf_zone_id,
            'shelf_zone_code': self.shelf_zone.zone_code if self.shelf_zone else None,
            'shelf_zone_name': self.shelf_zone.name if self.shelf_zone else None,
            'calibration_version': self.calibration_version,
            'roi_polygon': self.roi_polygon,
            'facing_divisions': self.facing_divisions,
            'homography_matrix': self.homography_matrix,
            'status': self.status,
            'calibrated_by_user_id': self.calibrated_by_user_id,
            'calibrator_name': (self.calibrator.full_name or self.calibrator.email) if self.calibrator else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        return data
