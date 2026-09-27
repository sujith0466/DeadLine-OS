"""business_os_computer_vision_c4_1

Revision ID: u8v9w0x1y2z3
Revises: t7u8v9w0x1y2
Create Date: 2026-09-04 18:00:00.000000

Phase C4.1: Ambient Computer Vision & Shelf Monitoring Foundation
- Creates `business_shelf_zones` (Physical Shelf / Rack Fixture Master)
- Creates `business_visual_observations` (Visual Inference & Discrepancy Ledger)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'u8v9w0x1y2z3'
down_revision = 't7u8v9w0x1y2'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create `business_shelf_zones`
    op.create_table(
        'business_shelf_zones',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('business_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('zone_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('zone_type', sa.String(length=50), nullable=False, server_default='SHELF'),
        sa.Column('assigned_product_id', sa.String(length=36), sa.ForeignKey('business_products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('expected_capacity', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('target_facings', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('reorder_threshold', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('workspace_id', 'location_id', 'zone_code', name='uq_biz_shelf_ws_loc_code'),
        sa.CheckConstraint("expected_capacity >= 0 AND target_facings >= 0 AND reorder_threshold >= 0", name='chk_biz_shelf_capacity'),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE')", name='chk_biz_shelf_status'),
        sa.CheckConstraint("zone_type IN ('SHELF', 'RACK', 'PALLET_SLOT', 'BIN', 'ENDCAP', 'COOLER', 'DISPLAY')", name='chk_biz_shelf_type')
    )
    op.create_index('idx_biz_shelf_ws_status', 'business_shelf_zones', ['workspace_id', 'status'])
    op.create_index('idx_biz_shelf_ws_loc', 'business_shelf_zones', ['workspace_id', 'location_id'])
    op.create_index('idx_biz_shelf_ws_prod', 'business_shelf_zones', ['workspace_id', 'assigned_product_id'])

    # 2. Create `business_visual_observations`
    op.create_table(
        'business_visual_observations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('business_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shelf_zone_id', sa.String(length=36), sa.ForeignKey('business_shelf_zones.id', ondelete='SET NULL'), nullable=True),
        sa.Column('artifact_id', sa.String(length=36), sa.ForeignKey('business_ingestion_artifacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('capture_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('capture_device', sa.String(length=100), nullable=True),
        sa.Column('model_provider', sa.String(length=50), nullable=False, server_default='gemini'),
        sa.Column('model_name', sa.String(length=100), nullable=False, server_default='gemini-2.0-flash'),
        sa.Column('inference_latency_ms', sa.Integer(), nullable=True),
        sa.Column('detected_items', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('matched_product_id', sa.String(length=36), sa.ForeignKey('business_products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('visual_count', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('visual_facings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_confidence', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('anomaly_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('anomaly_type', sa.String(length=50), nullable=False, server_default='NONE'),
        sa.Column('system_stock_at_capture', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('discrepancy_quantity', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PROCESSED'),
        sa.Column('staged_extraction_id', sa.String(length=36), sa.ForeignKey('business_staged_extractions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('operational_alert_id', sa.String(length=36), sa.ForeignKey('business_operational_alerts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("visual_count >= 0", name='chk_biz_obs_count'),
        sa.CheckConstraint("visual_facings >= 0", name='chk_biz_obs_facings'),
        sa.CheckConstraint("overall_confidence >= 0 AND overall_confidence <= 100", name='chk_biz_obs_conf'),
        sa.CheckConstraint("status IN ('PROCESSED', 'REVIEW_REQUIRED', 'RECONCILED', 'DISMISSED')", name='chk_biz_obs_status'),
        sa.CheckConstraint("anomaly_type IN ('NONE', 'EMPTY_SHELF', 'MISPLACED_PRODUCT', 'OUT_OF_STOCK', 'FACING_DEFICIT', 'UNKNOWN_OBJECT', 'DAMAGED_PACKAGING')", name='chk_biz_obs_anomaly_type')
    )
    op.create_index('idx_biz_obs_ws_loc_time', 'business_visual_observations', ['workspace_id', 'location_id', 'capture_timestamp'])
    op.create_index('idx_biz_obs_ws_zone', 'business_visual_observations', ['workspace_id', 'shelf_zone_id'])
    op.create_index('idx_biz_obs_ws_anomaly', 'business_visual_observations', ['workspace_id', 'anomaly_detected', 'status'])
    op.create_index('idx_biz_obs_ws_prod', 'business_visual_observations', ['workspace_id', 'matched_product_id'])
    op.create_index('idx_biz_obs_ws_artifact', 'business_visual_observations', ['workspace_id', 'artifact_id'])


def downgrade():
    op.drop_table('business_visual_observations')
    op.drop_table('business_shelf_zones')
