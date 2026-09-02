"""business_os_serials_c3_3

Revision ID: r5s6t7u8v9w0
Revises: q4r5s6t7u8v9
Create Date: 2026-09-02 14:42:00.000000

Phase C3.3: Serial Number Tracking & Unit-Level Provenance.
- Adds is_serialized flag to business_products
- Creates business_serial_numbers registry table
- Creates business_stock_movement_serials attribution table
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'r5s6t7u8v9w0'
down_revision = 'q4r5s6t7u8v9'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Extend business_products with is_serialized
    op.add_column(
        'business_products',
        sa.Column('is_serialized', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    op.create_index('idx_biz_products_ws_serialized', 'business_products', ['workspace_id', 'is_serialized'])

    # 2. Create business_serial_numbers
    op.create_table(
        'business_serial_numbers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('serial_number', sa.String(length=100), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=True),
        sa.Column('goods_receipt_id', sa.String(length=36), nullable=True),
        sa.Column('current_location_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='IN_STOCK'),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('allocated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('defective_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disposed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('quarantine_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['business_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['batch_id'], ['business_batches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['goods_receipt_id'], ['business_goods_receipts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['current_location_id'], ['business_locations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'product_id', 'serial_number', name='uq_biz_serial_ws_prod_num'),
        sa.CheckConstraint(
            "status IN ('IN_STOCK', 'ALLOCATED', 'SHIPPED', 'CONSUMED', 'DEFECTIVE', 'DISPOSED')",
            name='chk_biz_serial_status'
        )
    )
    op.create_index('idx_biz_serial_ws_prod_status', 'business_serial_numbers', ['workspace_id', 'product_id', 'status'])
    op.create_index('idx_biz_serial_ws_batch', 'business_serial_numbers', ['workspace_id', 'batch_id'])
    op.create_index('idx_biz_serial_ws_loc', 'business_serial_numbers', ['workspace_id', 'current_location_id'])

    # 3. Create business_stock_movement_serials
    op.create_table(
        'business_stock_movement_serials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('stock_movement_id', sa.String(length=36), nullable=False),
        sa.Column('serial_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_movement_id'], ['business_stock_movements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['serial_id'], ['business_serial_numbers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_movement_id', 'serial_id', name='uq_biz_sm_serial')
    )
    op.create_index('idx_biz_sm_serial_ws_sm', 'business_stock_movement_serials', ['workspace_id', 'stock_movement_id'])
    op.create_index('idx_biz_sm_serial_ws_serial', 'business_stock_movement_serials', ['workspace_id', 'serial_id'])


def downgrade():
    op.drop_table('business_stock_movement_serials')
    op.drop_table('business_serial_numbers')
    op.drop_index('idx_biz_products_ws_serialized', table_name='business_products')
    op.drop_column('business_products', 'is_serialized')
