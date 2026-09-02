"""business_os_goods_receipts_c2_2

Revision ID: m0j1k2l3m4n5
Revises: l9i0j1k2l3m4
Create Date: 2026-09-02 07:05:00.000000

Phase C2.2 Goods Receiving / Goods Receipt Notes (GRN) Schema
Creates `business_goods_receipts` and `business_goods_receipt_lines`.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'm0j1k2l3m4n5'
down_revision = 'l9i0j1k2l3m4'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_goods_receipts
    op.create_table(
        'business_goods_receipts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('grn_number', sa.String(length=50), nullable=False),
        sa.Column('purchase_order_id', sa.String(length=36), nullable=False),
        sa.Column('supplier_partner_id', sa.String(length=36), nullable=False),
        sa.Column('destination_location_id', sa.String(length=36), nullable=False),
        sa.Column('receipt_date', sa.Date(), nullable=False),
        sa.Column('carrier_name', sa.String(length=100), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('delivery_note_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('staged_extraction_id', sa.String(length=36), nullable=True),
        sa.Column('received_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['business_purchase_orders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supplier_partner_id'], ['business_commercial_partners.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['destination_location_id'], ['business_locations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['staged_extraction_id'], ['business_staged_extractions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['received_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'grn_number', name='uq_biz_grn_ws_num')
    )
    op.create_index('idx_biz_grn_ws_id', 'business_goods_receipts', ['workspace_id'])
    op.create_index('idx_biz_grn_ws_status', 'business_goods_receipts', ['workspace_id', 'status'])
    op.create_index('idx_biz_grn_ws_po', 'business_goods_receipts', ['workspace_id', 'purchase_order_id'])

    # 2. Create business_goods_receipt_lines
    op.create_table(
        'business_goods_receipt_lines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('goods_receipt_id', sa.String(length=36), nullable=False),
        sa.Column('purchase_order_line_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('received_quantity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('accepted_quantity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('rejected_quantity', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('stock_movement_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['goods_receipt_id'], ['business_goods_receipts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_order_line_id'], ['business_purchase_order_lines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['business_products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['stock_movement_id'], ['business_stock_movements.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            'received_quantity >= 0 AND accepted_quantity >= 0 AND rejected_quantity >= 0 AND (accepted_quantity + rejected_quantity = received_quantity)',
            name='chk_biz_grnl_quantities'
        ),
        sa.CheckConstraint('unit_cost >= 0', name='chk_biz_grnl_unit_cost')
    )
    op.create_index('idx_biz_grnl_grn_id', 'business_goods_receipt_lines', ['goods_receipt_id'])
    op.create_index('idx_biz_grnl_pol_id', 'business_goods_receipt_lines', ['purchase_order_line_id'])
    op.create_index('idx_biz_grnl_product_id', 'business_goods_receipt_lines', ['product_id'])


def downgrade():
    op.drop_table('business_goods_receipt_lines')
    op.drop_table('business_goods_receipts')