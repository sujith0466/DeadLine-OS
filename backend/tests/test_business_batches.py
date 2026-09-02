"""
DeadlineOS Business OS — C3.2 Batch, Lot & Expiry Lifecycle Tests
==================================================================
Unit and service tests for batch master creation, movement attributions,
deterministic expiry evaluation, quarantine safety, FEFO advisory allocations,
and 5-tier RBAC / multi-tenant isolation.
"""

import uuid
import pytest
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    BusinessProduct,
    BusinessLocation,
    CommercialPartner,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessStockMovement,
    BusinessBatch,
    BusinessStockMovementBatch,
    AuditEvent
)
from services.business.batch_service import BatchService
from services.business.goods_receipt_service import GoodsReceiptService
from services.business.inventory_service import InventoryService
from utils.errors import APIError


@pytest.fixture
def fx_batch_env(app):
    """Sets up isolated workspaces, users, products, locations, and partners."""
    with app.app_context():
        # Workspace A
        ws_a = Workspace(id=str(uuid.uuid4()), name="Batch Corp A", base_currency="INR")
        # Workspace B
        ws_b = Workspace(id=str(uuid.uuid4()), name="Batch Corp B", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # Users
        u_owner = User(id=str(uuid.uuid4()), email="owner@batch.test", full_name="Batch Owner")
        u_admin = User(id=str(uuid.uuid4()), email="admin@batch.test", full_name="Batch Admin")
        u_member = User(id=str(uuid.uuid4()), email="member@batch.test", full_name="Batch Member")
        u_acct = User(id=str(uuid.uuid4()), email="acct@batch.test", full_name="Batch Accountant")
        u_viewer = User(id=str(uuid.uuid4()), email="viewer@batch.test", full_name="Batch Viewer")
        db.session.add_all([u_owner, u_admin, u_member, u_acct, u_viewer])
        db.session.commit()

        # Memberships
        for u, role in [
            (u_owner, 'OWNER'),
            (u_admin, 'ADMIN'),
            (u_member, 'MEMBER'),
            (u_acct, 'ACCOUNTANT'),
            (u_viewer, 'VIEWER')
        ]:
            db.session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=u.id, role=role, status='ACTIVE'))
        db.session.commit()

        # Product in Workspace A
        prod_a = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku="AMOX-500",
            name="Amoxicillin 500mg",
            unit="BOX",
            cost_price=Decimal("15.00"),
            selling_price=Decimal("25.00")
        )
        # Location in Workspace A
        loc_a = BusinessLocation(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Pharma Vault A",
            location_type="WAREHOUSE"
        )
        # Supplier in Workspace A
        supp_a = CommercialPartner(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            partner_type="SUPPLIER",
            name="Apex Laboratories"
        )

        # Product in Workspace B
        prod_b = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_b.id,
            sku="AMOX-500",
            name="Amoxicillin 500mg Corp B",
            unit="BOX"
        )
        db.session.add_all([prod_a, loc_a, supp_a, prod_b])
        db.session.commit()

        yield {
            'ws_a': ws_a,
            'ws_b': ws_b,
            'owner': u_owner,
            'admin': u_admin,
            'member': u_member,
            'acct': u_acct,
            'viewer': u_viewer,
            'prod_a': prod_a,
            'prod_b': prod_b,
            'loc_a': loc_a,
            'supp_a': supp_a,
        }


def test_batch_creation_and_uniqueness(app, fx_batch_env):
    """Verifies batch creation with metadata and uniqueness enforcement per workspace and product."""
    ws = fx_batch_env['ws_a']
    prod = fx_batch_env['prod_a']
    owner = fx_batch_env['owner']

    exp = date.today() + timedelta(days=180)
    mfg = date.today() - timedelta(days=30)

    batch = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={
            'batch_number': 'LOT-2026-001',
            'product_id': prod.id,
            'manufacture_date': mfg.isoformat(),
            'expiry_date': exp.isoformat(),
            'notes': 'First production run'
        }
    )

    assert batch.id is not None
    assert batch.batch_number == 'LOT-2026-001'
    assert batch.status == 'ACTIVE'
    assert batch.get_derived_status() == 'ACTIVE'

    # Duplicate batch creation must fail
    with pytest.raises(APIError) as exc:
        BatchService.create_batch(
            workspace_id=ws.id,
            actor_user_id=owner.id,
            data={
                'batch_number': 'LOT-2026-001',
                'product_id': prod.id,
            }
        )
    assert exc.value.code == 'DUPLICATE_BATCH'


def test_tenant_isolation_batches(app, fx_batch_env):
    """Verifies strict row-level workspace tenancy on batches."""
    ws_a = fx_batch_env['ws_a']
    ws_b = fx_batch_env['ws_b']
    prod_a = fx_batch_env['prod_a']
    owner = fx_batch_env['owner']

    batch_a = BatchService.create_batch(
        workspace_id=ws_a.id,
        actor_user_id=owner.id,
        data={
            'batch_number': 'LOT-A-999',
            'product_id': prod_a.id
        }
    )

    # Workspace B attempts to read Workspace A batch
    with pytest.raises(APIError) as exc:
        BatchService.get_batch(workspace_id=ws_b.id, batch_id=batch_a.id)
    assert exc.value.code == 'BATCH_NOT_FOUND'

    # Workspace B attempts to quarantine Workspace A batch
    with pytest.raises(APIError) as exc:
        BatchService.quarantine_batch(workspace_id=ws_b.id, batch_id=batch_a.id, actor_user_id=owner.id, reason="Hack")
    assert exc.value.code == 'BATCH_NOT_FOUND'


def test_grn_batch_creation_and_attribution(app, fx_batch_env):
    """Verifies receiving goods through GRN creates batch and links stock movement attribution."""
    ws = fx_batch_env['ws_a']
    prod = fx_batch_env['prod_a']
    loc = fx_batch_env['loc_a']
    supp = fx_batch_env['supp_a']
    owner = fx_batch_env['owner']

    # 1. Create Purchase Order
    po = BusinessPurchaseOrder(
        workspace_id=ws.id,
        po_number="PO-BATCH-01",
        supplier_partner_id=supp.id,
        destination_location_id=loc.id,
        currency="INR",
        status="APPROVED",
        total_amount=Decimal("7500.00"),
        base_currency_total=Decimal("7500.00")
    )
    db.session.add(po)
    db.session.flush()

    pol = BusinessPurchaseOrderLine(
        purchase_order_id=po.id,
        product_id=prod.id,
        ordered_quantity=Decimal("500.00"),
        unit_price=Decimal("15.00"),
        total_price=Decimal("7500.00"),
        status="ORDERED"
    )
    db.session.add(pol)
    db.session.commit()

    # 2. Receive goods with batch metadata
    exp_date = (date.today() + timedelta(days=365)).isoformat()
    grn = GoodsReceiptService.create_goods_receipt(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={
            'purchase_order_id': po.id,
            'lines': [{
                'purchase_order_line_id': pol.id,
                'received_quantity': '500.00',
                'accepted_quantity': '500.00',
                'rejected_quantity': '0.00',
                'batch_number': 'BATCH-GRN-101',
                'expiry_date': exp_date
            }]
        }
    )

    assert grn.status == 'COMPLETED'

    # 3. Verify Batch created and attributed
    batch = BusinessBatch.query.filter_by(workspace_id=ws.id, batch_number='BATCH-GRN-101').first()
    assert batch is not None
    assert batch.product_id == prod.id

    # 4. Invariant: Available batch stock == accepted quantity (500)
    avail_qty = BatchService.get_batch_available_stock(ws.id, batch.id)
    assert avail_qty == Decimal('500.00')


def test_movement_batch_attribution_invariants(app, fx_batch_env):
    """Verifies that SUM(batch attribution quantities) must equal stock movement quantity."""
    ws = fx_batch_env['ws_a']
    prod = fx_batch_env['prod_a']
    loc = fx_batch_env['loc_a']
    owner = fx_batch_env['owner']

    batch = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={'batch_number': 'LOT-INV-01', 'product_id': prod.id}
    )

    # Initial stock movement for 100 units
    mv = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='INITIAL_STOCK',
        direction='IN',
        quantity=Decimal('100.00')
    )
    db.session.add(mv)
    db.session.flush()

    # Mismatched attribution (e.g. 90 instead of 100) must fail
    with pytest.raises(APIError) as exc:
        BatchService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv,
            attributions=[{'batch_id': batch.id, 'quantity': '90.00'}],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'BATCH_QUANTITY_MISMATCH'

    # Correct attribution succeeds
    BatchService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv,
        attributions=[{'batch_id': batch.id, 'quantity': '100.00'}],
        actor_user_id=owner.id
    )
    db.session.commit()

    assert BatchService.get_batch_available_stock(ws.id, batch.id) == Decimal('100.00')


def test_insufficient_batch_stock_rejection(app, fx_batch_env):
    """Verifies that OUT movement exceeding available batch stock is atomically rejected."""
    ws = fx_batch_env['ws_a']
    prod = fx_batch_env['prod_a']
    loc = fx_batch_env['loc_a']
    owner = fx_batch_env['owner']

    batch = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={'batch_number': 'LOT-CAP-01', 'product_id': prod.id}
    )

    # Inflow of 50 units
    mv_in = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='INITIAL_STOCK',
        direction='IN',
        quantity=Decimal('50.00')
    )
    db.session.add(mv_in)
    db.session.flush()
    BatchService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_in,
        attributions=[{'batch_id': batch.id, 'quantity': '50.00'}],
        actor_user_id=owner.id
    )
    db.session.commit()

    # Outflow of 60 units (exceeds 50)
    mv_out = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('60.00')
    )
    db.session.add(mv_out)
    db.session.flush()

    with pytest.raises(APIError) as exc:
        BatchService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv_out,
            attributions=[{'batch_id': batch.id, 'quantity': '60.00'}],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'INSUFFICIENT_BATCH_STOCK'


def test_expiry_lifecycle_and_safety(app, fx_batch_env):
    """Verifies deterministic expiry status and rejection of expired batch dispatches."""
    ws = fx_batch_env['ws_a']
    prod = fx_batch_env['prod_a']
    loc = fx_batch_env['loc_a']
    owner = fx_batch_env['owner']

    # 1. Expired batch (expired yesterday)
    yesterday = date.today() - timedelta(days=1)
    batch_exp = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={
            'batch_number': 'LOT-EXPIRED',
            'product_id': prod.id,
            'expiry_date': yesterday.isoformat()
        }
    )
    assert batch_exp.get_derived_status() == 'EXPIRED'

    # Inflow to expired batch
    mv_in = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='INITIAL_STOCK',
        direction='IN',
        quantity=Decimal('10.00')
    )
    db.session.add(mv_in)
    db.session.flush()
    BatchService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_in,
        attributions=[{'batch_id': batch_exp.id, 'quantity': '10.00'}],
        actor_user_id=owner.id
    )
    db.session.commit()

    # Attempt SALE dispatch from expired batch -> must be rejected
    mv_out = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('5.00')
    )
    db.session.add(mv_out)
    db.session.flush()

    with pytest.raises(APIError) as exc:
        BatchService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv_out,
            attributions=[{'batch_id': batch_exp.id, 'quantity': '5.00'}],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'BATCH_EXPIRED'

    # 2. Expiring soon batch (expires in 15 days)
    soon = date.today() + timedelta(days=15)
    batch_soon = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={
            'batch_number': 'LOT-SOON',
            'product_id': prod.id,
            'expiry_date': soon.isoformat()
        }
    )
    assert batch_soon.get_derived_status(warning_horizon_days=30) == 'EXPIRING_SOON'


def test_quarantine_and_release(app, fx_batch_env):
    """Verifies quarantine isolation, dispatch blockage, and audit logging."""
    ws = fx_batch_env['ws_a']
    prod = fx_batch_env['prod_a']
    loc = fx_batch_env['loc_a']
    owner = fx_batch_env['owner']

    batch = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={'batch_number': 'LOT-QR-01', 'product_id': prod.id}
    )

    # Inflow of 20 units
    mv_in = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='INITIAL_STOCK',
        direction='IN',
        quantity=Decimal('20.00')
    )
    db.session.add(mv_in)
    db.session.flush()
    BatchService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_in,
        attributions=[{'batch_id': batch.id, 'quantity': '20.00'}],
        actor_user_id=owner.id
    )
    db.session.commit()

    # Quarantine batch
    BatchService.quarantine_batch(
        workspace_id=ws.id,
        batch_id=batch.id,
        actor_user_id=owner.id,
        reason="Suspected contamination"
    )

    assert batch.status == 'QUARANTINED'
    assert batch.get_derived_status() == 'QUARANTINED'

    # Attempt dispatch -> rejected
    mv_out = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('5.00')
    )
    db.session.add(mv_out)
    db.session.flush()

    with pytest.raises(APIError) as exc:
        BatchService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv_out,
            attributions=[{'batch_id': batch.id, 'quantity': '5.00'}],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'BATCH_QUARANTINED'

    # Release quarantine
    BatchService.release_quarantine(
        workspace_id=ws.id,
        batch_id=batch.id,
        actor_user_id=owner.id,
        release_notes="Lab tests cleared contamination"
    )
    assert batch.status == 'ACTIVE'

    # Now dispatch succeeds
    BatchService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_out,
        attributions=[{'batch_id': batch.id, 'quantity': '5.00'}],
        actor_user_id=owner.id
    )
    db.session.commit()
    assert BatchService.get_batch_available_stock(ws.id, batch.id) == Decimal('15.00')


def test_fefo_deterministic_ordering_and_override(app, fx_batch_env):
    """Verifies advisory FEFO returns batches ordered by earliest expiry, and records override reasons."""
    ws = fx_batch_env['ws_a']
    prod = fx_batch_env['prod_a']
    loc = fx_batch_env['loc_a']
    owner = fx_batch_env['owner']

    # Batch 1 expires in 60 days
    b1 = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={
            'batch_number': 'LOT-EXP-60',
            'product_id': prod.id,
            'expiry_date': (date.today() + timedelta(days=60)).isoformat()
        }
    )
    # Batch 2 expires in 20 days (Should be first in FEFO)
    b2 = BatchService.create_batch(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={
            'batch_number': 'LOT-EXP-20',
            'product_id': prod.id,
            'expiry_date': (date.today() + timedelta(days=20)).isoformat()
        }
    )

    # Inflows: 30 units to b1, 20 units to b2
    for b, qty in [(b1, '30.00'), (b2, '20.00')]:
        mv = BusinessStockMovement(
            workspace_id=ws.id,
            product_id=prod.id,
            location_id=loc.id,
            movement_type='INITIAL_STOCK',
            direction='IN',
            quantity=Decimal(qty)
        )
        db.session.add(mv)
        db.session.flush()
        BatchService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv,
            attributions=[{'batch_id': b.id, 'quantity': qty}],
            actor_user_id=owner.id
        )
    db.session.commit()

    # Query FEFO for 25 units
    fefo = BatchService.get_fefo_allocation(ws.id, prod.id, requested_quantity=Decimal('25.00'))
    assert fefo['fulfilled'] is True
    assert len(fefo['allocations']) == 2
    # First allocation MUST be b2 (expires in 20 days)
    assert fefo['allocations'][0]['batch_id'] == b2.id
    assert fefo['allocations'][0]['suggested_allocation'] == '20.00'
    # Second allocation is b1 (5 units to complete 25)
    assert fefo['allocations'][1]['batch_id'] == b1.id
    assert fefo['allocations'][1]['suggested_allocation'] == '5.00'

    # Test FEFO Override Audit
    mv_out = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('10.00')
    )
    db.session.add(mv_out)
    db.session.flush()
    # Operator deliberately chooses b1 instead of b2 with override reason
    BatchService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_out,
        attributions=[{'batch_id': b1.id, 'quantity': '10.00'}],
        actor_user_id=owner.id,
        fefo_override_reason="Customer specifically requested LOT-EXP-60"
    )
    db.session.commit()

    audit = AuditEvent.query.filter_by(
        workspace_id=ws.id,
        action='FEFO_OVERRIDE_RECORDED'
    ).first()
    assert audit is not None
    assert audit.after_state['override_reason'] == "Customer specifically requested LOT-EXP-60"


def test_rbac_batch_permissions(app, fx_batch_env):
    """Verifies the 5-tier RBAC matrix for batch operations."""
    from middleware.business_context import ROLE_PERMISSIONS

    # batch:read across all 5 tiers
    assert 'batch:read' in ROLE_PERMISSIONS['OWNER']
    assert 'batch:read' in ROLE_PERMISSIONS['ADMIN']
    assert 'batch:read' in ROLE_PERMISSIONS['MEMBER']
    assert 'batch:read' in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'batch:read' in ROLE_PERMISSIONS['VIEWER']

    # batch:write for OWNER, ADMIN, MEMBER; forbidden for ACCOUNTANT, VIEWER
    assert 'batch:write' in ROLE_PERMISSIONS['OWNER']
    assert 'batch:write' in ROLE_PERMISSIONS['ADMIN']
    assert 'batch:write' in ROLE_PERMISSIONS['MEMBER']
    assert 'batch:write' not in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'batch:write' not in ROLE_PERMISSIONS['VIEWER']

    # batch:quarantine restricted to OWNER, ADMIN
    assert 'batch:quarantine' in ROLE_PERMISSIONS['OWNER']
    assert 'batch:quarantine' in ROLE_PERMISSIONS['ADMIN']
    assert 'batch:quarantine' not in ROLE_PERMISSIONS['MEMBER']
    assert 'batch:quarantine' not in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'batch:quarantine' not in ROLE_PERMISSIONS['VIEWER']
