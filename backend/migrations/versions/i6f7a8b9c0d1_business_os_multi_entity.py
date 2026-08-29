"""business_os_multi_entity

Revision ID: i6f7a8b9c0d1
Revises: h5e6f7a8b9c0
Create Date: 2026-08-29 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i6f7a8b9c0d1'
down_revision = 'h5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'business_entities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('entity_code', sa.String(length=50), nullable=True),
        sa.Column('tax_identifier', sa.String(length=100), nullable=True),
        sa.Column('currency', sa.String(length=3), server_default='INR', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_entities_workspace_id'), 'business_entities', ['workspace_id'], unique=False)

    op.create_table(
        'business_inter_entity_transfers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_workspace_id', sa.String(length=36), nullable=False),
        sa.Column('source_entity_id', sa.String(length=36), nullable=True),
        sa.Column('destination_workspace_id', sa.String(length=36), nullable=False),
        sa.Column('destination_entity_id', sa.String(length=36), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='INR', nullable=False),
        sa.Column('transfer_date', sa.Date(), nullable=False),
        sa.Column('reference_note', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='SETTLED', nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['destination_workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_entity_id'], ['business_entities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['destination_entity_id'], ['business_entities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_inter_entity_transfers_source_workspace_id'), 'business_inter_entity_transfers', ['source_workspace_id'], unique=False)
    op.create_index(op.f('ix_business_inter_entity_transfers_destination_workspace_id'), 'business_inter_entity_transfers', ['destination_workspace_id'], unique=False)

    # Optional entity_id on invoices, transactions, recurring
    op.add_column('business_invoices', sa.Column('entity_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_invoices_entity', 'business_invoices', 'business_entities', ['entity_id'], ['id'], ondelete='SET NULL')

    op.add_column('business_transactions', sa.Column('entity_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_transactions_entity', 'business_transactions', 'business_entities', ['entity_id'], ['id'], ondelete='SET NULL')

    op.add_column('business_recurring_obligations', sa.Column('entity_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_recurring_entity', 'business_recurring_obligations', 'business_entities', ['entity_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_recurring_entity', 'business_recurring_obligations', type_='foreignkey')
    op.drop_column('business_recurring_obligations', 'entity_id')

    op.drop_constraint('fk_transactions_entity', 'business_transactions', type_='foreignkey')
    op.drop_column('business_transactions', 'entity_id')

    op.drop_constraint('fk_invoices_entity', 'business_invoices', type_='foreignkey')
    op.drop_column('business_invoices', 'entity_id')

    op.drop_index(op.f('ix_business_inter_entity_transfers_destination_workspace_id'), table_name='business_inter_entity_transfers')
    op.drop_index(op.f('ix_business_inter_entity_transfers_source_workspace_id'), table_name='business_inter_entity_transfers')
    op.drop_table('business_inter_entity_transfers')

    op.drop_index(op.f('ix_business_entities_workspace_id'), table_name='business_entities')
    op.drop_table('business_entities')
