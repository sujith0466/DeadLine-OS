"""business_os_cross_border_c3_5

Revision ID: t7u8v9w0x1y2
Revises: s6t7u8v9w0x1
Create Date: 2026-09-02 15:15:00.000000

Phase C3.5: Cross-Border Supply Chain Operations Hub & Copilot Grounding
- Creates `business_cross_border_shipments`
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 't7u8v9w0x1y2'
down_revision = 's6t7u8v9w0x1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'business_cross_border_shipments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shipment_number', sa.String(length=50), nullable=False),
        sa.Column('purchase_order_id', sa.String(length=36), sa.ForeignKey('business_purchase_orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('goods_receipt_id', sa.String(length=36), sa.ForeignKey('business_goods_receipts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('landed_cost_voucher_id', sa.String(length=36), sa.ForeignKey('business_landed_cost_vouchers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('supplier_partner_id', sa.String(length=36), sa.ForeignKey('business_commercial_partners.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('origin_country', sa.String(length=3), nullable=False),
        sa.Column('destination_country', sa.String(length=3), nullable=False),
        sa.Column('carrier_name', sa.String(length=100), nullable=True),
        sa.Column('transport_mode', sa.String(length=30), nullable=False, server_default='OCEAN'),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('bill_of_lading_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PLANNED'),
        sa.Column('customs_reference', sa.String(length=100), nullable=True),
        sa.Column('customs_status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('declared_customs_value', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('declared_currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('estimated_departure_date', sa.Date(), nullable=True),
        sa.Column('actual_departure_date', sa.Date(), nullable=True),
        sa.Column('estimated_arrival_date', sa.Date(), nullable=True),
        sa.Column('actual_arrival_date', sa.Date(), nullable=True),
        sa.Column('customs_clearance_date', sa.Date(), nullable=True),
        sa.Column('port_of_loading', sa.String(length=100), nullable=True),
        sa.Column('port_of_entry', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('workspace_id', 'shipment_number', name='uq_biz_cbs_ws_num'),
        sa.CheckConstraint("status IN ('PLANNED', 'BOOKED', 'IN_TRANSIT', 'CUSTOMS_HOLD', 'CUSTOMS_CLEARED', 'DELIVERED', 'CANCELLED')", name='chk_biz_cbs_status'),
        sa.CheckConstraint("customs_status IN ('PENDING', 'SUBMITTED', 'INSPECTION', 'CLEARED', 'REJECTED')", name='chk_biz_cbs_customs_status'),
        sa.CheckConstraint("transport_mode IN ('OCEAN', 'AIR', 'ROAD', 'RAIL', 'MULTIMODAL')", name='chk_biz_cbs_mode'),
        sa.CheckConstraint("declared_customs_value >= 0", name='chk_biz_cbs_value')
    )
    op.create_index('idx_biz_cbs_ws_status', 'business_cross_border_shipments', ['workspace_id', 'status'])
    op.create_index('idx_biz_cbs_ws_po', 'business_cross_border_shipments', ['workspace_id', 'purchase_order_id'])
    op.create_index('idx_biz_cbs_ws_grn', 'business_cross_border_shipments', ['workspace_id', 'goods_receipt_id'])
    op.create_index('idx_biz_cbs_ws_lcv', 'business_cross_border_shipments', ['workspace_id', 'landed_cost_voucher_id'])
    op.create_index('idx_biz_cbs_ws_supp', 'business_cross_border_shipments', ['workspace_id', 'supplier_partner_id'])


def downgrade():
    op.drop_table('business_cross_border_shipments')
