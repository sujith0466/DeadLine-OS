"""
B2 Test Suite — Multi-Tenant Isolation & RBAC
==============================================
Verifies cross-tenant staging isolation and 5-tier RBAC boundaries.
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db


def test_cross_tenant_staging_isolation(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # Tenant A creates workspace and staged item
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A Corp"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]
    res_cap_a = client.post("/api/business/capture/text", headers={**headers_a, "X-Workspace-Id": ws_a_id}, json={"text": "Confidential expense 50k"})
    staged_a_id = res_cap_a.get_json()["data"]["staged_extraction"]["id"]

    # Tenant B creates workspace
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "Tenant B Corp"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]

    # Tenant B attempts IDOR to read Tenant A's staged item
    res_idor = client.get(f"/api/business/staging/{staged_a_id}", headers={**headers_b, "X-Workspace-Id": ws_b_id})
    assert res_idor.status_code == 404

    # Tenant B attempts header spoofing on Tenant A's workspace
    res_spoof = client.get(f"/api/business/staging/{staged_a_id}", headers={**headers_b, "X-Workspace-Id": ws_a_id})
    assert res_spoof.status_code == 403


def test_viewer_cannot_confirm_staged_item(client):
    owner_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())
    db.session.add(User(id=owner_id, email="owner@biz.com"))
    db.session.add(User(id=viewer_id, email="viewer@biz.com"))
    db.session.commit()

    headers_owner = {"Authorization": f"Bearer {owner_id}", "Content-Type": "application/json"}
    headers_viewer = {"Authorization": f"Bearer {viewer_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "RBAC Staging Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    # Add viewer
    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role="VIEWER", status="ACTIVE"))
    db.session.commit()

    # Owner creates staged item
    res_cap = client.post("/api/business/capture/text", headers={**headers_owner, "X-Workspace-Id": ws_id}, json={"text": "Expense 10000"})
    staged_id = res_cap.get_json()["data"]["staged_extraction"]["id"]

    # Viewer can read
    res_read = client.get(f"/api/business/staging/{staged_id}", headers={**headers_viewer, "X-Workspace-Id": ws_id})
    assert res_read.status_code == 200

    # Viewer denied confirmation
    res_confirm = client.post(f"/api/business/staging/{staged_id}/confirm", headers={**headers_viewer, "X-Workspace-Id": ws_id})
    assert res_confirm.status_code == 403
    assert res_confirm.get_json()["error"]["code"] == "PERMISSION_DENIED"
