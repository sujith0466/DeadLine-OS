"""business_os_procurement_c2

Revision ID: l9i0j1k2l3m4
Revises: k8h9i0j1k2l3
Create Date: 2026-09-01 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'l9i0j1k2l3m4'
down_revision = 'k8h9i0j1k2l3'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_purchase_requests
    op.create_table(
        'business_purchase_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_number', sa.String(50), nullable=False),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('business_products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.String(36), sa.ForeignKey('business_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_quantity', sa.Numeric(15, 2), nullable=False),
        sa.Column('estimated_unit_price', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        sa.Column('estimated_total_price', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(30), nullable=False, server_default='SUBMITTED'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('requested_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('purchase_order_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('workspace_id', 'request_number', name='uq_biz_pr_ws_num'),
        sa.CheckConstraint('requested_quantity > 0', name='chk_biz_pr_qty'),
        sa.CheckConstraint('estimated_unit_price >= 0 AND estimated_total_price >= 0', name='chk_biz_pr_prices')
    )
    op.create_index('idx_biz_pr_ws_status', 'business_purchase_requests', ['workspace_id', 'status'])
    op.create_index('idx_biz_pr_ws_prod', 'business_purchase_requests', ['workspace_id', 'product_id'])

    # 2. Create business_purchase_orders
    op.create_table(
        'business_purchase_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('po_number', sa.String(50), nullable=False),
        sa.Column('supplier_partner_id', sa.String(36), sa.ForeignKey('business_commercial_partners.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('destination_location_id', sa.String(36), sa.ForeignKey('business_locations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('subtotal_amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('payment_terms', sa.String(50), nullable=False, server_default='NET_30'),
        sa.Column('status', sa.String(30), nullable=False, server_default='DRAFT'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('workspace_id', 'po_number', name='uq_biz_po_ws_num'),
        sa.CheckConstraint('subtotal_amount >= 0 AND tax_amount >= 0 AND total_amount >= 0', name='chk_biz_po_amounts')
    )
    op.create_index('idx_biz_po_ws_status', 'business_purchase_orders', ['workspace_id', 'status'])
    op.create_index('idx_biz_po_ws_supplier', 'business_purchase_orders', ['workspace_id', 'supplier_partner_id'])

    # 3. Create business_purchase_order_lines
    op.create_table(
        'business_purchase_order_lines',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('purchase_order_id', sa.String(36), sa.ForeignKey('business_purchase_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('business_products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('ordered_quantity', sa.Numeric(15, 2), nullable=False),
        sa.Column('received_quantity', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        sa.Column('unit_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('ordered_quantity > 0 AND received_quantity >= 0', name='chk_biz_pol_qty'),
        sa.CheckConstraint('unit_price >= 0 AND total_price >= 0', name='chk_biz_pol_prices')
    )
    op.create_index('idx_biz_pol_po_id', 'business_purchase_order_lines', ['purchase_order_id'])
    op.create_index('idx_biz_pol_product_id', 'business_purchase_order_lines', ['product_id'])


def downgrade():
    op.drop_index('idx_biz_pol_product_id', table_name='business_purchase_order_lines')
    op.drop_index('idx_biz_pol_po_id', table_name='business_purchase_order_lines')
    op.drop_table('business_purchase_order_lines')

    op.drop_index('idx_biz_po_ws_supplier', table_name='business_purchase_orders')
    op.drop_index('idx_biz_po_ws_status', table_name='business_purchase_orders')
    op.drop_table('business_purchase_orders')

    op.drop_index('idx_biz_pr_ws_prod', table_name='business_purchase_requests')
    op.drop_index('idx_biz_pr_ws_status', table_name='business_purchase_requests')
    op.drop_table('business_purchase_requests')
