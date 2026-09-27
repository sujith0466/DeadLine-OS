"""business_os_camera_calibration_c4_5

Revision ID: v9w0x1y2z3a4
Revises: u8v9w0x1y2z3
Create Date: 2026-09-27 11:15:00.000000

Phase C4.5: Ambient Camera Calibration & Edge Synchronization
- Creates `business_camera_devices` (Ambient Edge Camera Device Master & Tokens)
- Creates `business_camera_calibrations` (Spatial Geometric Calibration & Versioning Profiles)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'v9w0x1y2z3a4'
down_revision = 'u8v9w0x1y2z3'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create `business_camera_devices`
    op.create_table(
        'business_camera_devices',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('business_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False, server_default='SHELF_EDGE'),
        sa.Column('api_key_hash', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('firmware_version', sa.String(length=50), nullable=True),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('workspace_id', 'device_code', name='uq_biz_cam_dev_ws_code'),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'PAUSED')", name='chk_biz_cam_dev_status'),
        sa.CheckConstraint("device_type IN ('FIXED_OVERHEAD', 'SHELF_EDGE', 'MOBILE_TERMINAL')", name='chk_biz_cam_dev_type')
    )
    op.create_index('idx_biz_cam_dev_ws_status', 'business_camera_devices', ['workspace_id', 'status'])
    op.create_index('idx_biz_cam_dev_ws_loc', 'business_camera_devices', ['workspace_id', 'location_id'])

    # 2. Create `business_camera_calibrations`
    op.create_table(
        'business_camera_calibrations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('camera_device_id', sa.String(length=36), sa.ForeignKey('business_camera_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shelf_zone_id', sa.String(length=36), sa.ForeignKey('business_shelf_zones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calibration_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('roi_polygon', sa.JSON(), nullable=False),
        sa.Column('facing_divisions', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('homography_matrix', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('calibrated_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('workspace_id', 'camera_device_id', 'shelf_zone_id', 'calibration_version', name='uq_biz_cam_calib_ver'),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED')", name='chk_biz_cam_calib_status'),
        sa.CheckConstraint("calibration_version >= 1", name='chk_biz_cam_calib_ver')
    )
    op.create_index('idx_biz_cam_calib_ws_status', 'business_camera_calibrations', ['workspace_id', 'status'])
    op.create_index('idx_biz_cam_calib_dev', 'business_camera_calibrations', ['workspace_id', 'camera_device_id'])
    op.create_index('idx_biz_cam_calib_zone', 'business_camera_calibrations', ['workspace_id', 'shelf_zone_id'])


def downgrade():
    op.drop_table('business_camera_calibrations')
    op.drop_table('business_camera_devices')
