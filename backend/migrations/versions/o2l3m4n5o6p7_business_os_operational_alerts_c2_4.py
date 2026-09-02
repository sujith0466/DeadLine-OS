"""business_os_operational_alerts_c2_4

Revision ID: o2l3m4n5o6p7
Revises: m0j1k2l3m4n5
Create Date: 2026-09-02 07:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'o2l3m4n5o6p7'
down_revision = 'm0j1k2l3m4n5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'business_operational_alerts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='WARNING'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('dedup_fingerprint', sa.String(length=128), nullable=False),
        sa.Column('cooldown_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recommended_action', sa.String(length=50), nullable=True),
        sa.Column('generated_task_id', sa.String(length=36), nullable=True),
        sa.Column('acknowledged_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_task_id'], ['business_tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['acknowledged_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_operational_alerts', schema=None) as batch_op:
        batch_op.create_index('ix_biz_alerts_ws_status', ['workspace_id', 'status'])
        batch_op.create_index('ix_biz_alerts_fingerprint', ['workspace_id', 'dedup_fingerprint'])
        batch_op.create_index('ix_biz_alerts_entity', ['entity_type', 'entity_id'])


def downgrade():
    with op.batch_alter_table('business_operational_alerts', schema=None) as batch_op:
        batch_op.drop_index('ix_biz_alerts_entity')
        batch_op.drop_index('ix_biz_alerts_fingerprint')
        batch_op.drop_index('ix_biz_alerts_ws_status')
    op.drop_table('business_operational_alerts')
