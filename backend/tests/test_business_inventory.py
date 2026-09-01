"""
DeadlineOS Business OS — Inventory & Stock Ledger Test Suite (Phase C1)
======================================================================
Tests product catalog, location registry, append-only stock movement ledger,
negative stock rejection, atomic transfers, and low-stock health thresholds.
"""

import uuid
import pytest
from decimal import Decimal
from database.db import db
from models.user import User
from models.business import Workspace, WorkspaceMember, BusinessLocation, BusinessProduct, BusinessStockMovement
from services.business.inventory_service import InventoryService


@pytest.fixture
def inventory_test_env(app):
    with app.app_context():
        ws = Workspace(name="Titan Manufacturing", base_currency="INR")
        db.session.add(ws)
        db.session.commit()

        u_admin = User(id=str(uuid.uuid4()), email="admin@titan.com", full_name="Titan Admin")
        db.session.add(u_admin)
        db.session.commit()

        m_admin = WorkspaceMember(workspace_id=ws.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE")
        db.session.add(m_admin)
        db.session.commit()

        # Two Locations
        loc_a = BusinessLocation(workspace_id=ws.id, name="Factory Floor", location_type="WAREHOUSE")
        loc_b = BusinessLocation(workspace_id=ws.id, name="Downtown Outlet", location_type="STORE")
        db.session.add_all([loc_a, loc_b])
        db.session.commit()

        # Product with Reorder Level = 20.00, Safety Stock = 10.00
        prod = BusinessProduct(
            workspace_id=ws.id,
            sku="TITAN-BOLT-01",
            name="Titan Steel Bolt",
            unit="PCS",
            reorder_level=Decimal("20.00"),
            safety_stock=Decimal("10.00"),
            cost_price=Decimal("15.50"),
            selling_price=Decimal("25.00")
        )
        db.session.add(prod)
        db.session.commit()

        return {
            'workspace_id': ws.id,
            'admin_token': u_admin.id,
            'admin_user_id': u_admin.id,
            'loc_a_id': loc_a.id,
            'loc_b_id': loc_b.id,
            'product_id': prod.id,
            'sku': prod.sku
        }


def test_initial_stock_and_exact_decimal_aggregation(client, inventory_test_env):
    ws_id = inventory_test_env['workspace_id']
    token = inventory_test_env['admin_token']
    loc_a_id = inventory_test_env['loc_a_id']
    prod_id = inventory_test_env['product_id']

    # 1. Check stock before movements (should be 0.00)
    stock_0 = InventoryService.get_available_stock(ws_id, prod_id, loc_a_id)
    assert stock_0 == Decimal('0.00')

    # 2. Record INITIAL_STOCK (+50.00)
    res_in = client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_a_id,
            'movement_type': 'INITIAL_STOCK',
            'quantity': '50.00',
            'unit_cost': '15.50',
            'reason': 'Opening stock balance'
        }
    )
    assert res_in.status_code == 201
    mov_data = res_in.get_json()['data']['movement']
    assert mov_data['direction'] == 'IN'
    assert mov_data['quantity'] == '50.00'

    # 3. Check derived stock
    stock_1 = InventoryService.get_available_stock(ws_id, prod_id, loc_a_id)
    assert stock_1 == Decimal('50.00')


def test_strict_negative_stock_rejection(client, inventory_test_env):
    ws_id = inventory_test_env['workspace_id']
    token = inventory_test_env['admin_token']
    loc_a_id = inventory_test_env['loc_a_id']
    prod_id = inventory_test_env['product_id']

    # Initial stock: 15.00
    client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_a_id,
            'movement_type': 'INITIAL_STOCK',
            'quantity': '15.00'
        }
    )

    # Attempt to dispatch SALE of 20.00 (Exceeds 15.00)
    res_out = client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_a_id,
            'movement_type': 'SALE',
            'quantity': '20.00',
            'reason': 'Customer order'
        }
    )
    assert res_out.status_code == 400
    err_json = res_out.get_json()
    assert err_json['error']['code'] == 'INSUFFICIENT_STOCK'

    # Verify no movement record was inserted
    movements = BusinessStockMovement.query.filter_by(workspace_id=ws_id, movement_type='SALE').all()
    assert len(movements) == 0

    # Stock remains 15.00
    assert InventoryService.get_available_stock(ws_id, prod_id, loc_a_id) == Decimal('15.00')


def test_atomic_two_sided_transfer(client, inventory_test_env):
    ws_id = inventory_test_env['workspace_id']
    token = inventory_test_env['admin_token']
    loc_a_id = inventory_test_env['loc_a_id']
    loc_b_id = inventory_test_env['loc_b_id']
    prod_id = inventory_test_env['product_id']

    # Supply Factory Floor with 100 units
    client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_a_id,
            'movement_type': 'PURCHASE_RECEIVED',
            'quantity': '100.00'
        }
    )

    # Execute transfer of 40 units from Factory Floor to Downtown Outlet
    trf_res = client.post(
        '/api/business/inventory/transfers',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'source_location_id': loc_a_id,
            'destination_location_id': loc_b_id,
            'quantity': '40.00',
            'reason': 'Stock replenishment for retail branch'
        }
    )
    assert trf_res.status_code == 201
    trf_data = trf_res.get_json()['data']['transfer']
    batch_id = trf_data['transfer_batch_id']
    assert batch_id is not None

    # Verify Ledger Balances
    stock_a = InventoryService.get_available_stock(ws_id, prod_id, loc_a_id)
    stock_b = InventoryService.get_available_stock(ws_id, prod_id, loc_b_id)
    assert stock_a == Decimal('60.00')
    assert stock_b == Decimal('40.00')

    # Verify paired records share transfer_batch_id
    paired = BusinessStockMovement.query.filter_by(transfer_batch_id=batch_id).all()
    assert len(paired) == 2
    types = {p.movement_type for p in paired}
    assert types == {'TRANSFER_OUT', 'TRANSFER_IN'}


def test_low_stock_and_critical_safety_thresholds(client, inventory_test_env):
    ws_id = inventory_test_env['workspace_id']
    token = inventory_test_env['admin_token']
    loc_a_id = inventory_test_env['loc_a_id']
    prod_id = inventory_test_env['product_id']

    # Initial state: 0 quantity -> OUT_OF_STOCK
    res_0 = client.get(
        '/api/business/inventory',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id}
    )
    item_0 = res_0.get_json()['data']['items'][0]
    assert item_0['status'] == 'OUT_OF_STOCK'

    # Add 15 units (Reorder = 20, Safety = 10) -> LOW STOCK (above safety, below reorder)
    client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_a_id,
            'movement_type': 'INITIAL_STOCK',
            'quantity': '15.00'
        }
    )
    res_1 = client.get(
        '/api/business/inventory',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id}
    )
    item_1 = res_1.get_json()['data']['items'][0]
    assert item_1['status'] == 'LOW'
    assert item_1['is_critical_safety'] is False

    # Dispatch 8 units (Leaves 7 units -> At or below Safety of 10) -> CRITICAL SAFETY
    client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_a_id,
            'movement_type': 'SALE',
            'quantity': '8.00'
        }
    )
    res_2 = client.get(
        '/api/business/inventory',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id}
    )
    item_2 = res_2.get_json()['data']['items'][0]
    assert item_2['status'] == 'LOW'
    assert item_2['is_critical_safety'] is True

    # Receive 50 units (Total = 57 -> Above Reorder of 20) -> HEALTHY
    client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_a_id,
            'movement_type': 'PURCHASE_RECEIVED',
            'quantity': '50.00'
        }
    )
    res_3 = client.get(
        '/api/business/inventory',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id}
    )
    item_3 = res_3.get_json()['data']['items'][0]
    assert item_3['status'] == 'HEALTHY'
    assert item_3['is_critical_safety'] is False
