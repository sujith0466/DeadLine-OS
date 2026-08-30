"""business_os_auth_invitations

Revision ID: j7g8h9i0j1k2
Revises: i6f7a8b9c0d1
Create Date: 2026-08-30 15:05:00.000000

Creates the `business_workspace_invitations` table required for the B1-B12
Business OS Authentication invitation lifecycle (B7 – Invitation Acceptance).

This migration was identified as missing during the Final B1–B12 Release Audit
(FINDING-001 / P0). The previous test suite passed because tests used
`db.create_all()` (SQLAlchemy metadata) rather than the Alembic migration chain.
This migration ensures a production database upgraded through `alembic upgrade head`
contains the invitation table.

Schema derived directly from:
    backend/models/business/invitation.py  (WorkspaceInvitation)

Columns
-------
id                  : String(36) PK — UUIDv4 string
workspace_id        : String(36) FK → business_workspaces.id  (CASCADE DELETE)
email               : String(255) NOT NULL — invitee email address
role                : String(20) NOT NULL — assigned RBAC role (default MEMBER)
token               : String(64) NOT NULL UNIQUE — cryptographic URL-safe token
status              : String(20) NOT NULL — state machine (default PENDING)
invited_by_user_id  : String(36) FK → users.id  (SET NULL ON DELETE) NULLABLE
expires_at          : DateTime(TZ) NOT NULL — invitation expiry timestamp
created_at          : DateTime(TZ) NOT NULL — row creation timestamp
updated_at          : DateTime(TZ) NOT NULL — last mutation timestamp

Constraints
-----------
PK: id
FK: workspace_id → business_workspaces.id  (ondelete=CASCADE)
FK: invited_by_user_id → users.id  (ondelete=SET NULL)
UNIQUE: token  (named: uq_biz_inv_token)

Indexes
-------
idx_biz_inv_workspace_id        → workspace_id
idx_biz_inv_email               → email
idx_biz_inv_token               → token  (supporting the unique constraint)
idx_biz_inv_ws_email_status     → (workspace_id, email, status)  — composite

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j7g8h9i0j1k2'
down_revision = 'i6f7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'business_workspace_invitations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='MEMBER'),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('invited_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['business_workspaces.id'],
            name='fk_biz_inv_workspace',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['invited_by_user_id'],
            ['users.id'],
            name='fk_biz_inv_invited_by',
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_biz_inv_token'),
    )

    # Individual column indexes
    with op.batch_alter_table('business_workspace_invitations', schema=None) as batch_op:
        batch_op.create_index('idx_biz_inv_workspace_id', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_inv_email', ['email'], unique=False)
        batch_op.create_index('idx_biz_inv_token', ['token'], unique=False)
        # Composite index matching __table_args__ on the model
        batch_op.create_index(
            'idx_biz_inv_ws_email_status',
            ['workspace_id', 'email', 'status'],
            unique=False
        )


def downgrade():
    with op.batch_alter_table('business_workspace_invitations', schema=None) as batch_op:
        batch_op.drop_index('idx_biz_inv_ws_email_status')
        batch_op.drop_index('idx_biz_inv_token')
        batch_op.drop_index('idx_biz_inv_email')
        batch_op.drop_index('idx_biz_inv_workspace_id')

    op.drop_table('business_workspace_invitations')
