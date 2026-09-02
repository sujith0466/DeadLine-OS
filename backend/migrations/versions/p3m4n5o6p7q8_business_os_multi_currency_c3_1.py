"""business_os_multi_currency_c3_1

Revision ID: p3m4n5o6p7q8
Revises: o2l3m4n5o6p7
Create Date: 2026-09-02 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'p3m4n5o6p7q8'
down_revision = 'o2l3m4n5o6p7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_exchange_rates table
    op.create_table(
        'business_exchange_rates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('from_currency', sa.String(length=3), nullable=False),
        sa.Column('to_currency', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('rate_source', sa.String(length=30), nullable=False, server_default='MANUAL_OVERRIDE'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'from_currency', 'to_currency', 'effective_date', name='uq_biz_fx_ws_curr_date'),
        sa.CheckConstraint('rate > 0', name='chk_biz_fx_rate_positive')
    )
    with op.batch_alter_table('business_exchange_rates', schema=None) as batch_op:
        batch_op.create_index('idx_biz_fx_ws_pair', ['workspace_id', 'from_currency', 'to_currency'])

    # 2. Add default_currency to business_commercial_partners
    with op.batch_alter_table('business_commercial_partners', schema=None) as batch_op:
        batch_op.add_column(sa.Column('default_currency', sa.String(length=3), nullable=False, server_default='INR'))

    # 3. Add exchange_rate and base_currency_total to business_purchase_orders
    with op.batch_alter_table('business_purchase_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('exchange_rate', sa.Numeric(precision=18, scale=6), nullable=False, server_default='1.000000'))
        batch_op.add_column(sa.Column('base_currency_total', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'))


def downgrade():
    with op.batch_alter_table('business_purchase_orders', schema=None) as batch_op:
        batch_op.drop_column('base_currency_total')
        batch_op.drop_column('exchange_rate')

    with op.batch_alter_table('business_commercial_partners', schema=None) as batch_op:
        batch_op.drop_column('default_currency')

    with op.batch_alter_table('business_exchange_rates', schema=None) as batch_op:
        batch_op.drop_index('idx_biz_fx_ws_pair')
    op.drop_table('business_exchange_rates')
