"""
DeadlineOS Business OS — Operations Tenant Isolation & IDOR Test Suite (Phase C1)
================================================================================
Verifies that tasks, products, locations, and inventory movements cannot be accessed
or mutated across workspace boundaries.
"""

import uuid
import pytest
from database.db import db
from models.user import User
from models.business import Workspace, WorkspaceMember, BusinessLocation, BusinessProduct, BusinessTask


@pytest.fixture
def multi_workspace_env(app):
    with app.app_context():
        # Workspace A (Tenant A)
        ws_a = Workspace(name="Tenant Alpha", base_currency="INR")
        # Workspace B (Tenant B)
        ws_b = Workspace(name="Tenant Beta", base_currency="USD")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        u_a = User(id=str(uuid.uuid4()), email="user_a@alpha.com", full_name="User Alpha")
        u_b = User(id=str(uuid.uuid4()), email="user_b@beta.com", full_name="User Beta")
        db.session.add_all([u_a, u_b])
        db.session.commit()

        m_a = WorkspaceMember(workspace_id=ws_a.id, user_id=u_a.id, role="OWNER", status="ACTIVE")
        m_b = WorkspaceMember(workspace_id=ws_b.id, user_id=u_b.id, role="OWNER", status="ACTIVE")
        db.session.add_all([m_a, m_b])
        db.session.commit()

        # Tenant A resources
        loc_a = BusinessLocation(workspace_id=ws_a.id, name="Alpha Warehouse")
        prod_a = BusinessProduct(workspace_id=ws_a.id, sku="ALPHA-001", name="Alpha Widget")
        task_a = BusinessTask(workspace_id=ws_a.id, title="Alpha Secret Task", created_by_user_id=u_a.id)

        # Tenant B resources
        loc_b = BusinessLocation(workspace_id=ws_b.id, name="Beta Warehouse")
        prod_b = BusinessProduct(workspace_id=ws_b.id, sku="BETA-001", name="Beta Widget")
        task_b = BusinessTask(workspace_id=ws_b.id, title="Beta Secret Task", created_by_user_id=u_b.id)

        db.session.add_all([loc_a, prod_a, task_a, loc_b, prod_b, task_b])
        db.session.commit()

        return {
            'ws_a_id': ws_a.id,
            'token_a': u_a.id,
            'loc_a_id': loc_a.id,
            'prod_a_id': prod_a.id,
            'task_a_id': task_a.id,
            'ws_b_id': ws_b.id,
            'token_b': u_b.id,
            'loc_b_id': loc_b.id,
            'prod_b_id': prod_b.id,
            'task_b_id': task_b.id,
        }


def test_cross_tenant_task_access_blocked(client, multi_workspace_env):
    ws_a_id = multi_workspace_env['ws_a_id']
    token_b = multi_workspace_env['token_b']
    task_a_id = multi_workspace_env['task_a_id']

    # User B attempts to access Workspace A's task using Workspace A header -> 403 (Not a member of WS A)
    res_hdr = client.get(
        f'/api/business/tasks/{task_a_id}',
        headers={'Authorization': f'Bearer {token_b}', 'X-Workspace-Id': ws_a_id}
    )
    assert res_hdr.status_code == 403

    # User B attempts to query Task A using their own Workspace B header -> 404 (Task does not belong to WS B)
    ws_b_id = multi_workspace_env['ws_b_id']
    res_idor = client.get(
        f'/api/business/tasks/{task_a_id}',
        headers={'Authorization': f'Bearer {token_b}', 'X-Workspace-Id': ws_b_id}
    )
    assert res_idor.status_code == 404


def test_cross_tenant_inventory_movement_blocked(client, multi_workspace_env):
    ws_a_id = multi_workspace_env['ws_a_id']
    token_a = multi_workspace_env['token_a']
    prod_a_id = multi_workspace_env['prod_a_id']
    loc_b_id = multi_workspace_env['loc_b_id']  # Location belongs to Workspace B

    # User A tries to record movement for Product A into Location B (Cross-tenant Foreign Key Injection)
    res = client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {token_a}', 'X-Workspace-Id': ws_a_id},
        json={
            'product_id': prod_a_id,
            'location_id': loc_b_id,
            'movement_type': 'INITIAL_STOCK',
            'quantity': '10.00'
        }
    )
    assert res.status_code == 404
    assert res.get_json()['error']['code'] == 'NOT_FOUND'


def test_cross_tenant_transfer_blocked(client, multi_workspace_env):
    ws_a_id = multi_workspace_env['ws_a_id']
    token_a = multi_workspace_env['token_a']
    prod_a_id = multi_workspace_env['prod_a_id']
    loc_a_id = multi_workspace_env['loc_a_id']
    loc_b_id = multi_workspace_env['loc_b_id']

    # User A tries to transfer stock from Location A to Location B (different workspace)
    res = client.post(
        '/api/business/inventory/transfers',
        headers={'Authorization': f'Bearer {token_a}', 'X-Workspace-Id': ws_a_id},
        json={
            'product_id': prod_a_id,
            'source_location_id': loc_a_id,
            'destination_location_id': loc_b_id,
            'quantity': '5.00'
        }
    )
    assert res.status_code == 404
