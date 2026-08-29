"""
B7 Test Suite — Multi-Entity Tenant Isolation & Authorization
=============================================================
Tests cross-workspace authorization barriers on consolidated views and RBAC.
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db


def test_unauthorized_workspace_consolidation_rejected(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # User A creates Workspace A
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "User A Private Corp"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]

    # User B creates Workspace B
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "User B Private Corp"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]

    # User B attempts to run consolidated report across Workspace B + Workspace A -> Must be 403 Forbidden
    res_unauth = client.post("/api/business/consolidation/overview", headers=headers_b, json={
        "workspace_ids": [ws_b_id, ws_a_id]
    })
    assert res_unauth.status_code == 403


def test_viewer_role_denied_entity_creation(client):
    owner_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())

    db.session.add_all([
        User(id=owner_id, email="owner@entitycorp.com"),
        User(id=viewer_id, email="viewer@entitycorp.com")
    ])
    db.session.commit()

    headers_owner = {"Authorization": f"Bearer {owner_id}", "Content-Type": "application/json"}
    headers_viewer = {"Authorization": f"Bearer {viewer_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "RBAC Entity Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role="VIEWER", status="ACTIVE"))
    db.session.commit()

    # VIEWER denied creating entity (403)
    res_create = client.post(
        "/api/business/entities",
        headers={**headers_viewer, "X-Workspace-Id": ws_id},
        json={"name": "Unauthorized Entity"}
    )
    assert res_create.status_code == 403
