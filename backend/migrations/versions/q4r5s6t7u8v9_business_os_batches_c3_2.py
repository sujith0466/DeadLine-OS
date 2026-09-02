"""business_os_batches_c3_2

Revision ID: q4r5s6t7u8v9
Revises: p3m4n5o6p7q8
Create Date: 2026-09-02 14:26:00.000000

Phase C3.2 — Batch, Lot & Expiry Lifecycle Management:
- business_batches (batch master registry, quarantine, expiry tracking)
- business_stock_movement_batches (movement-to-batch attribution ledger)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'q4r5s6t7u8v9'
down_revision = 'p3m4n5o6p7q8'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_batches
    op.create_table(
        'business_batches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_partner_id', sa.String(length=36), nullable=True),
        sa.Column('goods_receipt_id', sa.String(length=36), nullable=True),
        sa.Column('manufacture_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('quarantine_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['business_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_partner_id'], ['business_commercial_partners.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['goods_receipt_id'], ['business_goods_receipts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'product_id', 'batch_number', name='uq_biz_batch_ws_prod_num')
    )
    op.create_index('idx_biz_batch_ws_prod_exp', 'business_batches', ['workspace_id', 'product_id', 'expiry_date'], unique=False)
    op.create_index('idx_biz_batch_ws_status', 'business_batches', ['workspace_id', 'status'], unique=False)
    op.create_index('ix_business_batches_workspace_id', 'business_batches', ['workspace_id'], unique=False)
    op.create_index('ix_business_batches_product_id', 'business_batches', ['product_id'], unique=False)
    op.create_index('ix_business_batches_supplier_partner_id', 'business_batches', ['supplier_partner_id'], unique=False)
    op.create_index('ix_business_batches_goods_receipt_id', 'business_batches', ['goods_receipt_id'], unique=False)
    op.create_index('ix_business_batches_expiry_date', 'business_batches', ['expiry_date'], unique=False)

    # 2. Create business_stock_movement_batches
    op.create_table(
        'business_stock_movement_batches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('stock_movement_id', sa.String(length=36), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quantity > 0', name='chk_biz_sm_batch_qty'),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_movement_id'], ['business_stock_movements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['batch_id'], ['business_batches.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_movement_id', 'batch_id', name='uq_biz_sm_batch')
    )
    op.create_index('idx_biz_sm_batch_ws_batch', 'business_stock_movement_batches', ['workspace_id', 'batch_id'], unique=False)
    op.create_index('ix_business_stock_movement_batches_workspace_id', 'business_stock_movement_batches', ['workspace_id'], unique=False)
    op.create_index('ix_business_stock_movement_batches_stock_movement_id', 'business_stock_movement_batches', ['stock_movement_id'], unique=False)
    op.create_index('ix_business_stock_movement_batches_batch_id', 'business_stock_movement_batches', ['batch_id'], unique=False)


def downgrade():
    op.drop_table('business_stock_movement_batches')
    op.drop_table('business_batches')
