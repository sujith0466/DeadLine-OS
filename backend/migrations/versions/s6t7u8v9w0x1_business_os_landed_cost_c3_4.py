"""business_os_landed_cost_c3_4

Revision ID: s6t7u8v9w0x1
Revises: r5s6t7u8v9w0
Create Date: 2026-09-02 15:00:00.000000

Phase C3.4: Landed Cost Allocation Engine
- Creates `business_landed_cost_vouchers`
- Creates `business_landed_cost_voucher_items`
- Creates `business_landed_cost_allocations`
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 's6t7u8v9w0x1'
down_revision = 'r5s6t7u8v9w0'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_landed_cost_vouchers table
    op.create_table(
        'business_landed_cost_vouchers',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voucher_number', sa.String(length=50), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('purchase_order_id', sa.String(length=36), sa.ForeignKey('business_purchase_orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('goods_receipt_id', sa.String(length=36), sa.ForeignKey('business_goods_receipts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('base_currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=6), nullable=False, server_default='1.000000'),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('allocation_basis', sa.String(length=30), nullable=False, server_default='VALUE'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('total_cost_source_currency', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_cost_base_currency', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('allocated_total_base_currency', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reversed_by_voucher_id', sa.String(length=36), sa.ForeignKey('business_landed_cost_vouchers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reversal_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('workspace_id', 'voucher_number', name='uq_biz_lcv_ws_num'),
        sa.CheckConstraint("status IN ('DRAFT', 'ALLOCATED', 'APPROVED', 'REVERSED')", name='chk_biz_lcv_status'),
        sa.CheckConstraint("allocation_basis IN ('VALUE', 'QUANTITY')", name='chk_biz_lcv_basis'),
        sa.CheckConstraint("total_cost_source_currency >= 0 AND total_cost_base_currency >= 0 AND allocated_total_base_currency >= 0", name='chk_biz_lcv_amounts')
    )
    op.create_index('idx_biz_lcv_ws_status', 'business_landed_cost_vouchers', ['workspace_id', 'status'])
    op.create_index('idx_biz_lcv_ws_po', 'business_landed_cost_vouchers', ['workspace_id', 'purchase_order_id'])
    op.create_index('idx_biz_lcv_ws_grn', 'business_landed_cost_vouchers', ['workspace_id', 'goods_receipt_id'])

    # 2. Create business_landed_cost_voucher_items table
    op.create_table(
        'business_landed_cost_voucher_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voucher_id', sa.String(length=36), sa.ForeignKey('business_landed_cost_vouchers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cost_category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('exchange_rate', sa.Numeric(precision=18, scale=6), nullable=False, server_default='1.000000'),
        sa.Column('base_currency_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('external_reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0 AND base_currency_amount > 0", name='chk_biz_lcvi_amount'),
        sa.CheckConstraint("cost_category IN ('FREIGHT', 'CUSTOMS', 'DUTIES', 'INSURANCE', 'HANDLING', 'BROKERAGE', 'PORT_CHARGES', 'STORAGE', 'OTHER')", name='chk_biz_lcvi_category')
    )
    op.create_index('idx_biz_lcvi_ws_voucher', 'business_landed_cost_voucher_items', ['workspace_id', 'voucher_id'])

    # 3. Create business_landed_cost_allocations table
    op.create_table(
        'business_landed_cost_allocations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voucher_id', sa.String(length=36), sa.ForeignKey('business_landed_cost_vouchers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('goods_receipt_line_id', sa.String(length=36), sa.ForeignKey('business_goods_receipt_lines.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('business_products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('accepted_quantity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('line_base_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('allocation_weight', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('allocated_cost_base_currency', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('landed_cost_per_unit', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('voucher_id', 'goods_receipt_line_id', name='uq_biz_lca_voucher_line'),
        sa.CheckConstraint("allocated_cost_base_currency >= 0 AND landed_cost_per_unit >= 0", name='chk_biz_lca_amounts')
    )
    op.create_index('idx_biz_lca_ws_voucher', 'business_landed_cost_allocations', ['workspace_id', 'voucher_id'])
    op.create_index('idx_biz_lca_ws_grnl', 'business_landed_cost_allocations', ['workspace_id', 'goods_receipt_line_id'])
    op.create_index('idx_biz_lca_ws_prod', 'business_landed_cost_allocations', ['workspace_id', 'product_id'])


def downgrade():
    op.drop_table('business_landed_cost_allocations')
    op.drop_table('business_landed_cost_voucher_items')
    op.drop_table('business_landed_cost_vouchers')
