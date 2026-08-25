"""Phase 2 to 7 Schema Evolution & Stabilization

Revision ID: c5e8b123987f
Revises: a37ac0618419
Create Date: 2026-08-25 15:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5e8b123987f'
down_revision = 'a37ac0618419'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create recurrence_rules table (Phase 3)
    op.create_table(
        'recurrence_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('interval', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('by_day', sa.String(length=50), nullable=True),
        sa.Column('by_hour', sa.Integer(), nullable=True),
        sa.Column('by_minute', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('exceptions', sa.JSON(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_recurrence_user'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('recurrence_rules', schema=None) as batch_op:
        batch_op.create_index('idx_recurrence_entity', ['entity_type', 'entity_id'], unique=False)
        batch_op.create_index('idx_recurrence_user', ['user_id'], unique=False)

    # 2. Create recovery_records table (Phase 5)
    op.create_table(
        'recovery_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('source_activity_type', sa.String(length=50), nullable=False),
        sa.Column('source_activity_id', sa.String(length=36), nullable=False),
        sa.Column('drift_reason', sa.String(length=100), nullable=False),
        sa.Column('recovery_action', sa.String(length=50), nullable=False),
        sa.Column('streak_protected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('schedule_adjusted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notification_adjusted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('action_taken_at', sa.DateTime(), nullable=False),
        sa.Column('action_payload', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_recovery_user'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('recovery_records', schema=None) as batch_op:
        batch_op.create_index('idx_recovery_user', ['user_id'], unique=False)
        batch_op.create_index('idx_recovery_source', ['source_activity_type', 'source_activity_id'], unique=False)

    # 3. Alter schedule_slots table
    with op.batch_alter_table('schedule_slots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('entity_type', sa.String(length=50), nullable=True, server_default='TASK'))
        batch_op.add_column(sa.Column('entity_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('window_start', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('window_end', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=True, server_default='50'))
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True, server_default='PLANNED'))
        batch_op.add_column(sa.Column('recurrence_rule_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))

    # 4. Alter notifications table
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notification_type', sa.String(length=50), nullable=True, server_default='TASK_REMINDER'))
        batch_op.add_column(sa.Column('scheduled_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('delivered_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('dismissed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('group_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('deduplication_key', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('requires_confirmation', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('confirmation_action', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('runtime_session_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('schedule_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True, server_default='UNREAD'))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('status')
        batch_op.drop_column('schedule_id')
        batch_op.drop_column('runtime_session_id')
        batch_op.drop_column('confirmation_action')
        batch_op.drop_column('requires_confirmation')
        batch_op.drop_column('deduplication_key')
        batch_op.drop_column('group_id')
        batch_op.drop_column('dismissed_at')
        batch_op.drop_column('acknowledged_at')
        batch_op.drop_column('delivered_at')
        batch_op.drop_column('scheduled_at')
        batch_op.drop_column('notification_type')

    with op.batch_alter_table('schedule_slots', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('recurrence_rule_id')
        batch_op.drop_column('status')
        batch_op.drop_column('priority')
        batch_op.drop_column('window_end')
        batch_op.drop_column('window_start')
        batch_op.drop_column('entity_id')
        batch_op.drop_column('entity_type')

    op.drop_table('recovery_records')
    op.drop_table('recurrence_rules')
