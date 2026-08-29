"""Business OS Capture & Staging - Artifacts & Staging Queue

Revision ID: e2b3c4d5e6f7
Revises: d1a2b3c4d5e6
Create Date: 2026-08-29 15:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2b3c4d5e6f7'
down_revision = 'd1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_ingestion_artifacts table
    op.create_table(
        'business_ingestion_artifacts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('uploader_user_id', sa.String(length=36), nullable=False),
        sa.Column('artifact_type', sa.String(length=20), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='STORED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_artifact_workspace', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploader_user_id'], ['users.id'], name='fk_biz_artifact_uploader', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_ingestion_artifacts', schema=None) as batch_op:
        batch_op.create_index('idx_biz_artifacts_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_artifacts_uploader', ['uploader_user_id'], unique=False)
        batch_op.create_index('idx_biz_artifacts_ws_hash', ['workspace_id', 'sha256_hash'], unique=False)

    # 2. Create business_staged_extractions table
    op.create_table(
        'business_staged_extractions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('artifact_id', sa.String(length=36), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=False),
        sa.Column('reviewed_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('source_channel', sa.String(length=20), nullable=False),
        sa.Column('candidate_type', sa.String(length=50), nullable=False, server_default='EXPENSE'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='NEEDS_REVIEW'),
        sa.Column('raw_extracted_data', sa.JSON(), nullable=True),
        sa.Column('normalized_data', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('confidence_breakdown', sa.JSON(), nullable=True),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workspace_id'], ['business_workspaces.id'], name='fk_biz_staged_workspace', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['artifact_id'], ['business_ingestion_artifacts.id'], name='fk_biz_staged_artifact', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_biz_staged_creator', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], name='fk_biz_staged_reviewer', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('business_staged_extractions', schema=None) as batch_op:
        batch_op.create_index('idx_biz_staged_ws', ['workspace_id'], unique=False)
        batch_op.create_index('idx_biz_staged_ws_status', ['workspace_id', 'status'], unique=False)
        batch_op.create_index('idx_biz_staged_artifact', ['artifact_id'], unique=False)


def downgrade():
    op.drop_table('business_staged_extractions')
    op.drop_table('business_ingestion_artifacts')
