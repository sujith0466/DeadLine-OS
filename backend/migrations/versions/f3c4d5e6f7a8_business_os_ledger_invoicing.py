"""Business OS Ledger & Invoicing - Invoices, Transactions & Allocations

Revision ID: f3c4d5e6f7a8
Revises: e2b3c4d5e6f7
Create Date: 2026-08-29 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3c4d5e6f7a8'
down_revision = 'e2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_invoices table
    op.create_table(
        'business_invoices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('invoice_type', sa.String(length=20), nullable=False, server_default='RECEIVABLE'),
        sa.Column('partner_id', sa.String(length=36), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('subtotal', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('paid_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('balance_due', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=False),
        sa.Column('staged_extraction_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "subtotal >= 0 AND tax_amount >= 0 AND discount_amount >= 0 AND total_amount >= 0 AND "
            "discount_amount <= (subtotal + tax_amount) AND paid_amount >= 0 AND balance_due >= 0 AND "
            "(status = 'VOID' OR (paid_amount + balance_due = total_amount))",
            name='chk_biz_inv_math'
        ),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_inv_workspace', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['partner_id'], ['business_commercial_partners.id'], name='fk_biz_inv_partner', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_biz_inv_creator', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['staged_extraction_id'], ['business_staged_extractions.id'], name='fk_biz_inv_staged', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'invoice_number', name='uq_biz_inv_ws_num')
    )
    with op.batch_alter_table('business_invoices', schema=None) as batch_op:
        batch_op.create_index('idx_biz_inv_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_inv_ws_status', ['workspace_id', 'status'], unique=False)
        batch_op.create_index('idx_biz_inv_partner', ['partner_id'], unique=False)

    # 2. Create business_invoice_items table
    op.create_table(
        'business_invoice_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1.00'),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['invoice_id'], ['business_invoices.id'], name='fk_biz_item_invoice', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_item_workspace', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_invoice_items', schema=None) as batch_op:
        batch_op.create_index('idx_biz_inv_items_inv', ['invoice_id'], unique=False)

    # 3. Create business_transactions table
    op.create_table(
        'business_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('settlement_date', sa.Date(), nullable=True),
        sa.Column('partner_id', sa.String(length=36), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CONFIRMED'),
        sa.Column('reversal_of_transaction_id', sa.String(length=36), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=False),
        sa.Column('staged_extraction_id', sa.String(length=36), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_tx_workspace', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['partner_id'], ['business_commercial_partners.id'], name='fk_biz_tx_partner', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reversal_of_transaction_id'], ['business_transactions.id'], name='fk_biz_tx_reversal', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_biz_tx_creator', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['staged_extraction_id'], ['business_staged_extractions.id'], name='fk_biz_tx_staged', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_transactions', schema=None) as batch_op:
        batch_op.create_index('idx_biz_tx_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_tx_ws_date', ['workspace_id', 'transaction_date'], unique=False)
        batch_op.create_index('idx_biz_tx_ws_status', ['workspace_id', 'status'], unique=False)
        batch_op.create_index('idx_biz_tx_partner', ['partner_id'], unique=False)

    # 4. Create business_payment_allocations table
    op.create_table(
        'business_payment_allocations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('allocated_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('allocated_by_user_id', sa.String(length=36), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('allocated_amount > 0', name='chk_biz_alloc_amount'),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_alloc_workspace', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['business_transactions.id'], name='fk_biz_alloc_tx', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['business_invoices.id'], name='fk_biz_alloc_inv', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['allocated_by_user_id'], ['users.id'], name='fk_biz_alloc_user', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_payment_allocations', schema=None) as batch_op:
        batch_op.create_index('idx_biz_alloc_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_alloc_tx', ['transaction_id'], unique=False)
        batch_op.create_index('idx_biz_alloc_inv', ['invoice_id'], unique=False)


def downgrade():
    op.drop_table('business_payment_allocations')
    op.drop_table('business_transactions')
    op.drop_table('business_invoice_items')
    op.drop_table('business_invoices')
