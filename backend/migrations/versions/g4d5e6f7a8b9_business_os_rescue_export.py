"""business_os_rescue_export

Revision ID: g4d5e6f7a8b9
Revises: f3c4d5e6f7a8
Create Date: 2026-08-29 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g4d5e6f7a8b9'
down_revision = 'f3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'business_collection_reminders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=True),
        sa.Column('tone', sa.String(length=20), server_default='POLITE', nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('message_body', sa.Text(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['business_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['partner_id'], ['business_commercial_partners.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_collection_reminders_workspace_id'), 'business_collection_reminders', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_business_collection_reminders_invoice_id'), 'business_collection_reminders', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_business_collection_reminders_partner_id'), 'business_collection_reminders', ['partner_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_business_collection_reminders_partner_id'), table_name='business_collection_reminders')
    op.drop_index(op.f('ix_business_collection_reminders_invoice_id'), table_name='business_collection_reminders')
    op.drop_index(op.f('ix_business_collection_reminders_workspace_id'), table_name='business_collection_reminders')
    op.drop_table('business_collection_reminders')
