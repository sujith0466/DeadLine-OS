"""
DeadlineOS Business OS — Business Tasks Test Suite (Phase C1)
=============================================================
Tests task CRUD, member assignments, status lifecycle transitions,
and overdue calculations.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.business import Workspace, WorkspaceMember, BusinessTask, BusinessLocation, BusinessProduct


@pytest.fixture
def workspace_with_members(app):
    with app.app_context():
        # Setup workspace
        ws = Workspace(name="Acme Operations Corp", base_currency="INR")
        db.session.add(ws)
        db.session.commit()

        # Users
        u_owner = User(id=str(uuid.uuid4()), email="owner@acme.com", full_name="Acme Owner")
        u_member1 = User(id=str(uuid.uuid4()), email="alex@acme.com", full_name="Alex Rivera")
        u_member2 = User(id=str(uuid.uuid4()), email="sam@acme.com", full_name="Sam Taylor")
        db.session.add_all([u_owner, u_member1, u_member2])
        db.session.commit()

        # Memberships
        m_owner = WorkspaceMember(workspace_id=ws.id, user_id=u_owner.id, role="OWNER", status="ACTIVE")
        m_member1 = WorkspaceMember(workspace_id=ws.id, user_id=u_member1.id, role="MEMBER", status="ACTIVE")
        m_member2 = WorkspaceMember(workspace_id=ws.id, user_id=u_member2.id, role="MEMBER", status="ACTIVE")
        db.session.add_all([m_owner, m_member1, m_member2])
        db.session.commit()

        # Location & Product
        loc = BusinessLocation(workspace_id=ws.id, name="Warehouse Alpha", location_type="WAREHOUSE")
        prod = BusinessProduct(workspace_id=ws.id, sku="SKU-TEST-001", name="Test Widget", unit="PCS")
        db.session.add_all([loc, prod])
        db.session.commit()

        return {
            'workspace_id': ws.id,
            'owner_user_id': u_owner.id,
            'owner_token': u_owner.id,
            'member1_id': m_member1.id,
            'member1_user_id': u_member1.id,
            'member1_token': u_member1.id,
            'member2_id': m_member2.id,
            'location_id': loc.id,
            'product_id': prod.id,
        }


def test_create_and_query_business_task(client, workspace_with_members):
    ws_id = workspace_with_members['workspace_id']
    token = workspace_with_members['owner_token']
    loc_id = workspace_with_members['location_id']
    prod_id = workspace_with_members['product_id']
    m1_id = workspace_with_members['member1_id']

    # 1. Create Task
    res = client.post(
        '/api/business/tasks',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={
            'title': 'Restock Shelf 4B',
            'description': 'Receive 50 units and stack on shelf 4B',
            'priority': 'HIGH',
            'category': 'INVENTORY',
            'assignee_member_id': m1_id,
            'location_id': loc_id,
            'product_id': prod_id,
            'due_date': (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        }
    )
    assert res.status_code == 201
    task_data = res.get_json()['data']['task']
    task_id = task_data['id']
    assert task_data['title'] == 'Restock Shelf 4B'
    assert task_data['priority'] == 'HIGH'
    assert task_data['status'] == 'TODO'
    assert task_data['is_overdue'] is False
    assert task_data['assignee_member_id'] == m1_id

    # 2. Query Tasks List
    list_res = client.get(
        '/api/business/tasks',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id}
    )
    assert list_res.status_code == 200
    items = list_res.get_json()['data']['tasks']
    assert len(items) == 1
    assert items[0]['id'] == task_id


def test_task_status_lifecycle_and_validation(client, workspace_with_members):
    ws_id = workspace_with_members['workspace_id']
    token = workspace_with_members['owner_token']

    # Create task
    res = client.post(
        '/api/business/tasks',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'title': 'Inspect Fire Extinguishers', 'priority': 'MEDIUM'}
    )
    assert res.status_code == 201
    task_id = res.get_json()['data']['task']['id']

    # 1. Valid Transition: TODO -> IN_PROGRESS
    res_prog = client.post(
        f'/api/business/tasks/{task_id}/status',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'status': 'IN_PROGRESS', 'reason': 'Started inspection'}
    )
    assert res_prog.status_code == 200
    assert res_prog.get_json()['data']['task']['status'] == 'IN_PROGRESS'

    # 2. Valid Transition: IN_PROGRESS -> BLOCKED
    res_blk = client.post(
        f'/api/business/tasks/{task_id}/status',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'status': 'BLOCKED', 'reason': 'Access key missing for building 2'}
    )
    assert res_blk.status_code == 200
    assert res_blk.get_json()['data']['task']['status'] == 'BLOCKED'

    # 3. Invalid Transition: BLOCKED -> DONE directly (must go through IN_PROGRESS)
    res_inv = client.post(
        f'/api/business/tasks/{task_id}/status',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'status': 'DONE'}
    )
    assert res_inv.status_code == 400

    # 4. Valid Transition: BLOCKED -> IN_PROGRESS -> DONE
    client.post(
        f'/api/business/tasks/{task_id}/status',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'status': 'IN_PROGRESS'}
    )
    res_done = client.post(
        f'/api/business/tasks/{task_id}/status',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'status': 'DONE'}
    )
    assert res_done.status_code == 200
    task_done = res_done.get_json()['data']['task']
    assert task_done['status'] == 'DONE'
    assert task_done['completed_at'] is not None


def test_task_reassignment_and_deletion(client, workspace_with_members):
    ws_id = workspace_with_members['workspace_id']
    token = workspace_with_members['owner_token']
    m2_id = workspace_with_members['member2_id']

    # Create task
    res = client.post(
        '/api/business/tasks',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'title': 'Prepare Weekly Dispatch', 'priority': 'LOW'}
    )
    task_id = res.get_json()['data']['task']['id']

    # Reassign to member 2
    res_assign = client.post(
        f'/api/business/tasks/{task_id}/assign',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id},
        json={'assignee_member_id': m2_id}
    )
    assert res_assign.status_code == 200
    assert res_assign.get_json()['data']['task']['assignee_member_id'] == m2_id

    # Delete task
    del_res = client.delete(
        f'/api/business/tasks/{task_id}',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id}
    )
    assert del_res.status_code == 200

    # Confirm 404
    get_res = client.get(
        f'/api/business/tasks/{task_id}',
        headers={'Authorization': f'Bearer {token}', 'X-Workspace-Id': ws_id}
    )
    assert get_res.status_code == 404
