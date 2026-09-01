"""business_os_operations_c1

Revision ID: k8h9i0j1k2l3
Revises: j7g8h9i0j1k2
Create Date: 2026-08-31 18:30:00.000000

Creates the 4 tables required for Phase C1 Business Operations Foundation:
1. `business_locations`
2. `business_products`
3. `business_stock_movements` (Append-Only Inventory Ledger)
4. `business_tasks`

Schema derived directly from:
- backend/models/business/location.py (BusinessLocation)
- backend/models/business/product.py (BusinessProduct)
- backend/models/business/stock_movement.py (BusinessStockMovement)
- backend/models/business/task.py (BusinessTask)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k8h9i0j1k2l3'
down_revision = 'j7g8h9i0j1k2'
branch_labels = None
depends_on = None


def upgrade():
    # -------------------------------------------------------------------------
    # 1. business_locations
    # -------------------------------------------------------------------------
    op.create_table(
        'business_locations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', sa.String(length=36), sa.ForeignKey('business_entities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location_type', sa.String(length=50), nullable=False, server_default='WAREHOUSE'),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('workspace_id', 'name', name='uq_biz_loc_ws_name'),
        sa.CheckConstraint("location_type IN ('WAREHOUSE', 'STORE', 'BRANCH', 'OFFICE', 'STORAGE_UNIT')", name='chk_biz_loc_type'),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name='chk_biz_loc_status')
    )
    op.create_index('idx_biz_locations_workspace_id', 'business_locations', ['workspace_id'])
    op.create_index('idx_biz_locations_ws_status', 'business_locations', ['workspace_id', 'status'])
    op.create_index('idx_biz_locations_entity', 'business_locations', ['entity_id'])

    # -------------------------------------------------------------------------
    # 2. business_products
    # -------------------------------------------------------------------------
    op.create_table(
        'business_products',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=30), nullable=False, server_default='UNIT'),
        sa.Column('reorder_level', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('safety_stock', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('cost_price', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('selling_price', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('preferred_supplier_partner_id', sa.String(length=36), sa.ForeignKey('business_commercial_partners.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('workspace_id', 'sku', name='uq_biz_prod_ws_sku'),
        sa.CheckConstraint("unit IN ('UNIT', 'PCS', 'KG', 'GRAM', 'LITER', 'ML', 'BOX', 'PACK', 'METER')", name='chk_biz_prod_unit'),
        sa.CheckConstraint("status IN ('ACTIVE', 'DISCONTINUED', 'ARCHIVED')", name='chk_biz_prod_status'),
        sa.CheckConstraint("reorder_level >= 0 AND safety_stock >= 0 AND cost_price >= 0 AND selling_price >= 0", name='chk_biz_prod_math')
    )
    op.create_index('idx_biz_products_workspace_id', 'business_products', ['workspace_id'])
    op.create_index('idx_biz_products_ws_status', 'business_products', ['workspace_id', 'status'])
    op.create_index('idx_biz_products_ws_category', 'business_products', ['workspace_id', 'category'])
    op.create_index('idx_biz_products_supplier', 'business_products', ['preferred_supplier_partner_id'])

    # -------------------------------------------------------------------------
    # 3. business_stock_movements (Append-Only Ledger)
    # -------------------------------------------------------------------------
    op.create_table(
        'business_stock_movements',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('business_products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('business_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('movement_type', sa.String(length=30), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=36), nullable=True),
        sa.Column('transfer_batch_id', sa.String(length=36), nullable=True),
        sa.Column('staged_extraction_id', sa.String(length=36), sa.ForeignKey('business_staged_extractions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("direction IN ('IN', 'OUT')", name='chk_biz_sm_dir'),
        sa.CheckConstraint("quantity > 0", name='chk_biz_sm_qty'),
        sa.CheckConstraint("movement_type IN ('INITIAL_STOCK', 'PURCHASE_RECEIVED', 'SALE', 'TRANSFER_IN', 'TRANSFER_OUT', 'DAMAGED', 'RETURN', 'MANUAL_ADJUSTMENT')", name='chk_biz_sm_type')
    )
    op.create_index('idx_biz_sm_workspace_id', 'business_stock_movements', ['workspace_id'])
    op.create_index('idx_biz_sm_ws_prod_loc', 'business_stock_movements', ['workspace_id', 'product_id', 'location_id'])
    op.create_index('idx_biz_sm_ws_created', 'business_stock_movements', ['workspace_id', 'created_at'])
    op.create_index('idx_biz_sm_ref', 'business_stock_movements', ['reference_type', 'reference_id'])
    op.create_index('idx_biz_sm_transfer_batch', 'business_stock_movements', ['transfer_batch_id'])

    # -------------------------------------------------------------------------
    # 4. business_tasks
    # -------------------------------------------------------------------------
    op.create_table(
        'business_tasks',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assignee_member_id', sa.String(length=36), sa.ForeignKey('business_workspace_members.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='TODO'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('entity_id', sa.String(length=36), sa.ForeignKey('business_entities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('location_id', sa.String(length=36), sa.ForeignKey('business_locations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('business_products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('parent_task_id', sa.String(length=36), sa.ForeignKey('business_tasks.id', ondelete='CASCADE'), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='GENERAL'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')", name='chk_biz_task_priority'),
        sa.CheckConstraint("status IN ('TODO', 'IN_PROGRESS', 'BLOCKED', 'DONE', 'CANCELLED')", name='chk_biz_task_status'),
        sa.CheckConstraint("category IN ('GENERAL', 'INVENTORY', 'PROCUREMENT', 'FACILITY', 'AUDIT', 'MAINTENANCE')", name='chk_biz_task_category')
    )
    op.create_index('idx_biz_tasks_workspace_id', 'business_tasks', ['workspace_id'])
    op.create_index('idx_biz_tasks_ws_status', 'business_tasks', ['workspace_id', 'status'])
    op.create_index('idx_biz_tasks_ws_due', 'business_tasks', ['workspace_id', 'due_date'])
    op.create_index('idx_biz_tasks_assignee', 'business_tasks', ['assignee_member_id'])
    op.create_index('idx_biz_tasks_entity', 'business_tasks', ['entity_id'])
    op.create_index('idx_biz_tasks_location', 'business_tasks', ['location_id'])


def downgrade():
    op.drop_table('business_tasks')
    op.drop_table('business_stock_movements')
    op.drop_table('business_products')
    op.drop_table('business_locations')
