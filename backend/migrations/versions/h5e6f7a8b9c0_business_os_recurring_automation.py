"""business_os_recurring_automation

Revision ID: h5e6f7a8b9c0
Revises: g4d5e6f7a8b9
Create Date: 2026-08-29 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h5e6f7a8b9c0'
down_revision = 'g4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'business_recurring_obligations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('obligation_type', sa.String(length=30), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='INR', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('next_due_date', sa.Date(), nullable=False),
        sa.Column('auto_generate', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['partner_id'], ['business_commercial_partners.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_recurring_obligations_workspace_id'), 'business_recurring_obligations', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_business_recurring_obligations_partner_id'), 'business_recurring_obligations', ['partner_id'], unique=False)
    op.create_index(op.f('ix_business_recurring_obligations_next_due_date'), 'business_recurring_obligations', ['next_due_date'], unique=False)

    op.create_table(
        'business_automation_execution_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('obligation_id', sa.String(length=36), nullable=False),
        sa.Column('execution_type', sa.String(length=30), nullable=False),
        sa.Column('execution_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('generated_entity_type', sa.String(length=30), nullable=True),
        sa.Column('generated_entity_id', sa.String(length=36), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['obligation_id'], ['business_recurring_obligations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_automation_execution_logs_workspace_id'), 'business_automation_execution_logs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_business_automation_execution_logs_obligation_id'), 'business_automation_execution_logs', ['obligation_id'], unique=False)
    op.create_index(op.f('ix_business_automation_execution_logs_execution_date'), 'business_automation_execution_logs', ['execution_date'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_business_automation_execution_logs_execution_date'), table_name='business_automation_execution_logs')
    op.drop_index(op.f('ix_business_automation_execution_logs_obligation_id'), table_name='business_automation_execution_logs')
    op.drop_index(op.f('ix_business_automation_execution_logs_workspace_id'), table_name='business_automation_execution_logs')
    op.drop_table('business_automation_execution_logs')

    op.drop_index(op.f('ix_business_recurring_obligations_next_due_date'), table_name='business_recurring_obligations')
    op.drop_index(op.f('ix_business_recurring_obligations_partner_id'), table_name='business_recurring_obligations')
    op.drop_index(op.f('ix_business_recurring_obligations_workspace_id'), table_name='business_recurring_obligations')
    op.drop_table('business_recurring_obligations')
