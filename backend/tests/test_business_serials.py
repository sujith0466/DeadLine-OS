"""
DeadlineOS Business OS — C3.3 Serial Numbers & Unit Provenance Tests
====================================================================
Unit and integration tests for unit-level serial tracking, lifecycle state machine,
stock movement attributions, single-location invariant, double-dispatch prevention,
batch-serial consistency, 5-tier RBAC, and multi-tenant isolation.
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
    BusinessSerialNumber,
    BusinessStockMovementSerial,
    AuditEvent
)
from services.business.serial_service import SerialService
from services.business.batch_service import BatchService
from services.business.goods_receipt_service import GoodsReceiptService
from services.business.inventory_service import InventoryService
from utils.errors import APIError


@pytest.fixture
def fx_serial_env(app):
    """Sets up isolated workspaces, users, products, locations, and partners."""
    with app.app_context():
        # Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name="Serial Corp A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="Serial Corp B", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # Users
        u_owner = User(id=str(uuid.uuid4()), email="owner@serial.test", full_name="Serial Owner")
        u_admin = User(id=str(uuid.uuid4()), email="admin@serial.test", full_name="Serial Admin")
        u_member = User(id=str(uuid.uuid4()), email="member@serial.test", full_name="Serial Member")
        u_acct = User(id=str(uuid.uuid4()), email="acct@serial.test", full_name="Serial Accountant")
        u_viewer = User(id=str(uuid.uuid4()), email="viewer@serial.test", full_name="Serial Viewer")
        db.session.add_all([u_owner, u_admin, u_member, u_acct, u_viewer])
        db.session.commit()

        for u, role in [
            (u_owner, 'OWNER'),
            (u_admin, 'ADMIN'),
            (u_member, 'MEMBER'),
            (u_acct, 'ACCOUNTANT'),
            (u_viewer, 'VIEWER')
        ]:
            db.session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=u.id, role=role, status='ACTIVE'))
        db.session.commit()

        # Serialized Product in Workspace A
        prod_a = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku="DEV-ECG-01",
            name="Clinical ECG Monitor",
            unit="UNIT",
            cost_price=Decimal("12000.00"),
            selling_price=Decimal("22000.00"),
            is_serialized=True
        )
        # Location in Workspace A
        loc_a = BusinessLocation(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="High-Value Tech Vault",
            location_type="WAREHOUSE"
        )
        # Second Location in Workspace A
        loc_a2 = BusinessLocation(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Staging Bay 2",
            location_type="WAREHOUSE"
        )
        # Supplier in Workspace A
        supp_a = CommercialPartner(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            partner_type="SUPPLIER",
            name="Apex Medical Instruments"
        )

        # Product in Workspace B
        prod_b = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_b.id,
            sku="DEV-ECG-01",
            name="Clinical ECG Monitor Corp B",
            unit="UNIT",
            is_serialized=True
        )
        db.session.add_all([prod_a, loc_a, loc_a2, supp_a, prod_b])
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
            'loc_a2': loc_a2,
            'supp_a': supp_a,
        }


def test_serial_creation_and_uniqueness(app, fx_serial_env):
    """Verifies registering serial numbers and workspace-product uniqueness."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc = fx_serial_env['loc_a']
    owner = fx_serial_env['owner']

    serials = SerialService.register_or_receive_serials(
        workspace_id=ws.id,
        product_id=prod.id,
        serial_numbers=['SN-2026-001', 'SN-2026-002'],
        actor_user_id=owner.id,
        location_id=loc.id
    )

    assert len(serials) == 2
    assert serials[0].serial_number == 'SN-2026-001'
    assert serials[0].status == 'IN_STOCK'
    assert serials[0].current_location_id == loc.id

    # Duplicate registration attempt must fail
    with pytest.raises(APIError) as exc:
        SerialService.register_or_receive_serials(
            workspace_id=ws.id,
            product_id=prod.id,
            serial_numbers=['SN-2026-001'],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'DUPLICATE_SERIAL'


def test_tenant_isolation_serials(app, fx_serial_env):
    """Verifies that Workspace B cannot access or manipulate Workspace A serials."""
    ws_a = fx_serial_env['ws_a']
    ws_b = fx_serial_env['ws_b']
    prod_a = fx_serial_env['prod_a']
    owner = fx_serial_env['owner']

    serials = SerialService.register_or_receive_serials(
        workspace_id=ws_a.id,
        product_id=prod_a.id,
        serial_numbers=['SN-ISOLATION-01'],
        actor_user_id=owner.id
    )
    s_a = serials[0]

    # Workspace B attempts lookup
    with pytest.raises(APIError) as exc:
        SerialService.get_serial(ws_b.id, s_a.id)
    assert exc.value.code == 'SERIAL_NOT_FOUND'

    # Workspace B attempts transition
    with pytest.raises(APIError) as exc:
        SerialService.transition_lifecycle(ws_b.id, s_a.id, 'SHIPPED', owner.id)
    assert exc.value.code == 'SERIAL_NOT_FOUND'


def test_grn_serial_receiving_and_attribution(app, fx_serial_env):
    """Verifies receiving serialized products on GRN lines registers serials and links stock movement."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc = fx_serial_env['loc_a']
    supp = fx_serial_env['supp_a']
    owner = fx_serial_env['owner']

    po = BusinessPurchaseOrder(
        workspace_id=ws.id,
        po_number="PO-SERIAL-01",
        supplier_partner_id=supp.id,
        destination_location_id=loc.id,
        currency="INR",
        status="APPROVED",
        total_amount=Decimal("36000.00"),
        base_currency_total=Decimal("36000.00")
    )
    db.session.add(po)
    db.session.flush()

    pol = BusinessPurchaseOrderLine(
        purchase_order_id=po.id,
        product_id=prod.id,
        ordered_quantity=Decimal("3.00"),
        unit_price=Decimal("12000.00"),
        total_price=Decimal("36000.00"),
        status="ORDERED"
    )
    db.session.add(pol)
    db.session.commit()

    # Receive 3 serialized units with serial numbers
    grn = GoodsReceiptService.create_goods_receipt(
        workspace_id=ws.id,
        actor_user_id=owner.id,
        data={
            'purchase_order_id': po.id,
            'lines': [{
                'purchase_order_line_id': pol.id,
                'received_quantity': '3.00',
                'accepted_quantity': '3.00',
                'rejected_quantity': '0.00',
                'serial_numbers': ['ECG-1001', 'ECG-1002', 'ECG-1003']
            }]
        }
    )
    db.session.commit()

    assert grn.status == 'COMPLETED'

    # Verify serials exist in IN_STOCK
    s1 = SerialService.get_serial_by_number(ws.id, prod.id, 'ECG-1001')
    assert s1 is not None
    assert s1.status == 'IN_STOCK'
    assert s1.current_location_id == loc.id
    assert s1.goods_receipt_id == grn.id

    # Verify attribution link exists
    attr = BusinessStockMovementSerial.query.filter_by(workspace_id=ws.id, serial_id=s1.id).first()
    assert attr is not None
    assert attr.stock_movement.movement_type == 'PURCHASE_RECEIVED'


def test_quantity_serial_count_mismatch(app, fx_serial_env):
    """Verifies that movement quantity must exactly equal serials count."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc = fx_serial_env['loc_a']
    owner = fx_serial_env['owner']

    mv = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='INITIAL_STOCK',
        direction='IN',
        quantity=Decimal('2.00')
    )
    db.session.add(mv)
    db.session.flush()

    # Provide only 1 serial for quantity 2.00
    with pytest.raises(APIError) as exc:
        SerialService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv,
            product=prod,
            serials=['SN-ONLY-ONE'],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'SERIAL_COUNT_MISMATCH'


def test_serial_dispatch_and_status_transition(app, fx_serial_env):
    """Verifies outbound SALE stock movement dispatches serial, transitions status to SHIPPED, and clears location."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc = fx_serial_env['loc_a']
    owner = fx_serial_env['owner']

    # 1. Inward movement with serial
    mv_in = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='INITIAL_STOCK',
        direction='IN',
        quantity=Decimal('1.00')
    )
    db.session.add(mv_in)
    db.session.flush()
    SerialService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_in,
        product=prod,
        serials=['SN-DISPATCH-01'],
        actor_user_id=owner.id
    )
    db.session.commit()

    serial = SerialService.get_serial_by_number(ws.id, prod.id, 'SN-DISPATCH-01')
    assert serial.status == 'IN_STOCK'
    assert serial.current_location_id == loc.id

    # 2. Outward SALE movement dispatching the serial
    mv_out = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('1.00')
    )
    db.session.add(mv_out)
    db.session.flush()
    SerialService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_out,
        product=prod,
        serials=['SN-DISPATCH-01'],
        actor_user_id=owner.id
    )
    db.session.commit()

    # 3. Assert serial is now SHIPPED and location is cleared
    assert serial.status == 'SHIPPED'
    assert serial.shipped_at is not None
    assert serial.current_location_id is None

    # Verify provenance history
    provenance = SerialService.get_serial_provenance(ws.id, serial.id)
    assert len(provenance['provenance_history']) == 2
    assert provenance['provenance_history'][0]['movement_type'] == 'INITIAL_STOCK'
    assert provenance['provenance_history'][1]['movement_type'] == 'SALE'


def test_double_dispatch_prevention(app, fx_serial_env):
    """Verifies that an already dispatched serial cannot be dispatched a second time."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc = fx_serial_env['loc_a']
    owner = fx_serial_env['owner']

    # Inward movement
    mv_in = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='INITIAL_STOCK',
        direction='IN',
        quantity=Decimal('1.00')
    )
    db.session.add(mv_in)
    db.session.flush()
    SerialService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_in,
        product=prod,
        serials=['SN-DOUBLE-SPEND'],
        actor_user_id=owner.id
    )
    db.session.commit()

    # First dispatch succeeds
    mv_out_1 = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('1.00')
    )
    db.session.add(mv_out_1)
    db.session.flush()
    SerialService.validate_and_attribute_movement(
        workspace_id=ws.id,
        movement=mv_out_1,
        product=prod,
        serials=['SN-DOUBLE-SPEND'],
        actor_user_id=owner.id
    )
    db.session.commit()

    # Second dispatch must be rejected
    mv_out_2 = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('1.00')
    )
    db.session.add(mv_out_2)
    db.session.flush()

    with pytest.raises(APIError) as exc:
        SerialService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv_out_2,
            product=prod,
            serials=['SN-DOUBLE-SPEND'],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'SERIAL_NOT_AVAILABLE'


def test_batch_serial_consistency(app, fx_serial_env):
    """Verifies that a serial associated with Batch A cannot be dispatched under a Batch B movement."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc = fx_serial_env['loc_a']
    owner = fx_serial_env['owner']

    # Create Batch A and Batch B
    batch_a = BatchService.create_batch(ws.id, owner.id, {'batch_number': 'BATCH-A-01', 'product_id': prod.id})
    batch_b = BatchService.create_batch(ws.id, owner.id, {'batch_number': 'BATCH-B-01', 'product_id': prod.id})

    # Register serial under Batch A
    serials = SerialService.register_or_receive_serials(
        workspace_id=ws.id,
        product_id=prod.id,
        serial_numbers=['SN-BATCH-A-01'],
        actor_user_id=owner.id,
        location_id=loc.id,
        batch_id=batch_a.id
    )
    s_a = serials[0]

    # Create movement attributed to Batch B
    mv = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('1.00')
    )
    db.session.add(mv)
    db.session.flush()
    sm_b = BusinessStockMovementBatch(workspace_id=ws.id, stock_movement_id=mv.id, batch_id=batch_b.id, quantity=Decimal('1.00'))
    db.session.add(sm_b)
    db.session.flush()

    # Attempt to dispatch Batch A serial under Batch B movement -> must fail
    with pytest.raises(APIError) as exc:
        SerialService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv,
            product=prod,
            serials=[s_a.serial_number],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'BATCH_SERIAL_MISMATCH'


def test_location_invariant(app, fx_serial_env):
    """Verifies that a serial cannot be dispatched from a location other than its current physical location."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc1 = fx_serial_env['loc_a']
    loc2 = fx_serial_env['loc_a2']
    owner = fx_serial_env['owner']

    serials = SerialService.register_or_receive_serials(
        workspace_id=ws.id,
        product_id=prod.id,
        serial_numbers=['SN-LOC-01'],
        actor_user_id=owner.id,
        location_id=loc1.id
    )
    s = serials[0]

    # Attempt dispatch from loc2 (item is in loc1)
    mv_out = BusinessStockMovement(
        workspace_id=ws.id,
        product_id=prod.id,
        location_id=loc2.id,
        movement_type='SALE',
        direction='OUT',
        quantity=Decimal('1.00')
    )
    db.session.add(mv_out)
    db.session.flush()

    with pytest.raises(APIError) as exc:
        SerialService.validate_and_attribute_movement(
            workspace_id=ws.id,
            movement=mv_out,
            product=prod,
            serials=[s.serial_number],
            actor_user_id=owner.id
        )
    assert exc.value.code == 'SERIAL_LOCATION_MISMATCH'


def test_lifecycle_transitions_and_audit(app, fx_serial_env):
    """Verifies state machine transitions and audit logging."""
    ws = fx_serial_env['ws_a']
    prod = fx_serial_env['prod_a']
    loc = fx_serial_env['loc_a']
    owner = fx_serial_env['owner']

    serials = SerialService.register_or_receive_serials(
        workspace_id=ws.id,
        product_id=prod.id,
        serial_numbers=['SN-LIFECYCLE-01'],
        actor_user_id=owner.id,
        location_id=loc.id
    )
    s = serials[0]

    # Valid transition: IN_STOCK -> ALLOCATED
    SerialService.transition_lifecycle(ws.id, s.id, 'ALLOCATED', owner.id, reason="Reserved for SO-101")
    assert s.status == 'ALLOCATED'
    assert s.allocated_at is not None

    # Valid transition: ALLOCATED -> SHIPPED
    SerialService.transition_lifecycle(ws.id, s.id, 'SHIPPED', owner.id, reason="Shipped to customer")
    assert s.status == 'SHIPPED'
    assert s.current_location_id is None

    # Valid transition: SHIPPED -> CONSUMED
    SerialService.transition_lifecycle(ws.id, s.id, 'CONSUMED', owner.id, reason="Installed at hospital")
    assert s.status == 'CONSUMED'

    # Invalid transition: CONSUMED -> IN_STOCK (CONSUMED is terminal)
    with pytest.raises(APIError) as exc:
        SerialService.transition_lifecycle(ws.id, s.id, 'IN_STOCK', owner.id)
    assert exc.value.code == 'INVALID_LIFECYCLE_TRANSITION'

    # Verify audit events created
    audits = AuditEvent.query.filter_by(workspace_id=ws.id, entity_id=s.id).all()
    actions = [a.action for a in audits]
    assert 'SERIAL_REGISTERED' in actions
    assert 'SERIAL_STATUS_CHANGED' in actions


def test_rbac_serial_permissions(app, fx_serial_env):
    """Verifies 5-tier RBAC permissions for serial tracking."""
    from middleware.business_context import ROLE_PERMISSIONS

    # serial:read across all 5 tiers
    assert 'serial:read' in ROLE_PERMISSIONS['OWNER']
    assert 'serial:read' in ROLE_PERMISSIONS['ADMIN']
    assert 'serial:read' in ROLE_PERMISSIONS['MEMBER']
    assert 'serial:read' in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'serial:read' in ROLE_PERMISSIONS['VIEWER']

    # serial:write for OWNER, ADMIN, MEMBER; forbidden for ACCOUNTANT, VIEWER
    assert 'serial:write' in ROLE_PERMISSIONS['OWNER']
    assert 'serial:write' in ROLE_PERMISSIONS['ADMIN']
    assert 'serial:write' in ROLE_PERMISSIONS['MEMBER']
    assert 'serial:write' not in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'serial:write' not in ROLE_PERMISSIONS['VIEWER']

    # serial:quarantine restricted to OWNER, ADMIN
    assert 'serial:quarantine' in ROLE_PERMISSIONS['OWNER']
    assert 'serial:quarantine' in ROLE_PERMISSIONS['ADMIN']
    assert 'serial:quarantine' not in ROLE_PERMISSIONS['MEMBER']
    assert 'serial:quarantine' not in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'serial:quarantine' not in ROLE_PERMISSIONS['VIEWER']
