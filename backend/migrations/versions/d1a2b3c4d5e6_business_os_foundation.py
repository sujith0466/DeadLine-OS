"""Business OS Foundation - Tenancy, Members, Partners, Audit

Revision ID: d1a2b3c4d5e6
Revises: c5e8b123987f
Create Date: 2026-08-29 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1a2b3c4d5e6'
down_revision = 'c5e8b123987f'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_workspaces table
    op.create_table(
        'business_workspaces',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('tax_identifier', sa.String(length=100), nullable=True),
        sa.Column('base_currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='Asia/Kolkata'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create business_workspace_members table
    op.create_table(
        'business_workspace_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='MEMBER'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_member_workspace', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_biz_member_user', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_biz_ws_member')
    )
    with op.batch_alter_table('business_workspace_members', schema=None) as batch_op:
        batch_op.create_index('idx_biz_ws_member_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_ws_member_user', ['user_id'], unique=False)
        batch_op.create_index('idx_biz_ws_member_user_status', ['user_id', 'status'], unique=False)

    # 3. Create business_commercial_partners table
    op.create_table(
        'business_commercial_partners',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('partner_type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('tax_identifier', sa.String(length=100), nullable=True),
        sa.Column('credit_period_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_partner_workspace', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_commercial_partners', schema=None) as batch_op:
        batch_op.create_index('idx_biz_partners_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_partners_ws_type_status', ['workspace_id', 'partner_type', 'status'], unique=False)

    # 4. Create business_audit_events table (Non-cascading logical reference)
    op.create_table(
        'business_audit_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('actor_user_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_audit_events', schema=None) as batch_op:
        batch_op.create_index('idx_biz_audit_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_audit_actor', ['actor_user_id'], unique=False)
        batch_op.create_index('idx_biz_audit_ws_entity', ['workspace_id', 'entity_type', 'entity_id'], unique=False)
        batch_op.create_index('idx_biz_audit_ws_created', ['workspace_id', 'created_at'], unique=False)


def downgrade():
    op.drop_table('business_audit_events')
    op.drop_table('business_commercial_partners')
    op.drop_table('business_workspace_members')
    op.drop_table('business_workspaces')
