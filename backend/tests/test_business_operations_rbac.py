"""
DeadlineOS Business OS — Operations RBAC Test Suite (Phase C1)
==============================================================
Tests 5-tier role enforcement on Tasks, Products, Locations, and Inventory.
"""

import uuid
import pytest
from database.db import db
from models.user import User
from models.business import Workspace, WorkspaceMember, BusinessLocation, BusinessProduct


@pytest.fixture
def rbac_roles_env(app):
    with app.app_context():
        ws = Workspace(name="Vanguard Operations", base_currency="INR")
        db.session.add(ws)
        db.session.commit()

        # Users for 5 roles
        u_owner = User(id=str(uuid.uuid4()), email="owner@vanguard.com", full_name="Owner")
        u_admin = User(id=str(uuid.uuid4()), email="admin@vanguard.com", full_name="Admin")
        u_member = User(id=str(uuid.uuid4()), email="member@vanguard.com", full_name="Member")
        u_acct = User(id=str(uuid.uuid4()), email="acct@vanguard.com", full_name="Accountant")
        u_viewer = User(id=str(uuid.uuid4()), email="viewer@vanguard.com", full_name="Viewer")
        db.session.add_all([u_owner, u_admin, u_member, u_acct, u_viewer])
        db.session.commit()

        m_owner = WorkspaceMember(workspace_id=ws.id, user_id=u_owner.id, role="OWNER", status="ACTIVE")
        m_admin = WorkspaceMember(workspace_id=ws.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE")
        m_member = WorkspaceMember(workspace_id=ws.id, user_id=u_member.id, role="MEMBER", status="ACTIVE")
        m_acct = WorkspaceMember(workspace_id=ws.id, user_id=u_acct.id, role="ACCOUNTANT", status="ACTIVE")
        m_viewer = WorkspaceMember(workspace_id=ws.id, user_id=u_viewer.id, role="VIEWER", status="ACTIVE")
        db.session.add_all([m_owner, m_admin, m_member, m_acct, m_viewer])
        db.session.commit()

        loc = BusinessLocation(workspace_id=ws.id, name="Hub 1")
        prod = BusinessProduct(workspace_id=ws.id, sku="VGD-01", name="Standard Part")
        db.session.add_all([loc, prod])
        db.session.commit()

        return {
            'workspace_id': ws.id,
            'owner_token': u_owner.id,
            'admin_token': u_admin.id,
            'member_token': u_member.id,
            'acct_token': u_acct.id,
            'viewer_token': u_viewer.id,
            'loc_id': loc.id,
            'prod_id': prod.id
        }


def test_member_operational_permissions(client, rbac_roles_env):
    ws_id = rbac_roles_env['workspace_id']
    m_token = rbac_roles_env['member_token']
    loc_id = rbac_roles_env['loc_id']
    prod_id = rbac_roles_env['prod_id']

    # MEMBER CAN create task
    res_task = client.post(
        '/api/business/tasks',
        headers={'Authorization': f'Bearer {m_token}', 'X-Workspace-Id': ws_id},
        json={'title': 'Member Created Task'}
    )
    assert res_task.status_code == 201

    # MEMBER CAN record movement
    res_mov = client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {m_token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_id,
            'movement_type': 'INITIAL_STOCK',
            'quantity': '20.00'
        }
    )
    assert res_mov.status_code == 201

    # MEMBER CANNOT delete product (restricted to OWNER/ADMIN)
    res_del = client.delete(
        f'/api/business/products/{prod_id}',
        headers={'Authorization': f'Bearer {m_token}', 'X-Workspace-Id': ws_id}
    )
    assert res_del.status_code == 403


def test_accountant_read_only_restriction(client, rbac_roles_env):
    ws_id = rbac_roles_env['workspace_id']
    acct_token = rbac_roles_env['acct_token']
    loc_id = rbac_roles_env['loc_id']
    prod_id = rbac_roles_env['prod_id']

    # ACCOUNTANT CAN read inventory
    res_inv = client.get(
        '/api/business/inventory',
        headers={'Authorization': f'Bearer {acct_token}', 'X-Workspace-Id': ws_id}
    )
    assert res_inv.status_code == 200

    # ACCOUNTANT CANNOT record stock movement
    res_mov = client.post(
        '/api/business/inventory/movements',
        headers={'Authorization': f'Bearer {acct_token}', 'X-Workspace-Id': ws_id},
        json={
            'product_id': prod_id,
            'location_id': loc_id,
            'movement_type': 'INITIAL_STOCK',
            'quantity': '5.00'
        }
    )
    assert res_mov.status_code == 403


def test_viewer_read_only_restriction(client, rbac_roles_env):
    ws_id = rbac_roles_env['workspace_id']
    v_token = rbac_roles_env['viewer_token']

    # VIEWER CAN read tasks
    res_tasks = client.get(
        '/api/business/tasks',
        headers={'Authorization': f'Bearer {v_token}', 'X-Workspace-Id': ws_id}
    )
    assert res_tasks.status_code == 200

    # VIEWER CANNOT create task
    res_post = client.post(
        '/api/business/tasks',
        headers={'Authorization': f'Bearer {v_token}', 'X-Workspace-Id': ws_id},
        json={'title': 'Unauthorized Task'}
    )
    assert res_post.status_code == 403
