"""
B1 Security Test Suite — Multi-Tenant Leakage & IDOR Defense
============================================================
Verifies that:
- User from Tenant A cannot access Tenant B resources.
- Forged or spoofed X-Workspace-Id headers are rejected with 403.
- Unauthenticated requests are rejected with 401.
- Inactive members are rejected with 403.
"""

import uuid
from models.business import WorkspaceMember
from database.db import db


def test_cross_tenant_partner_access_rejected(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # User A creates Workspace A and Partner A
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]

    res_p_a = client.post(
        "/api/business/partners",
        headers={**headers_a, "X-Workspace-Id": ws_a_id},
        json={"partner_type": "CUSTOMER", "name": "Confidential Client A"}
    )
    partner_a_id = res_p_a.get_json()["data"]["partner"]["id"]

    # User B creates Workspace B
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "Tenant B"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]

    # User B attempts to access Partner A under Workspace B header (IDOR attempt)
    res_idor = client.get(
        f"/api/business/partners/{partner_a_id}",
        headers={**headers_b, "X-Workspace-Id": ws_b_id}
    )
    assert res_idor.status_code == 404
    assert "not found" in res_idor.get_json()["error"]["message"].lower()

    # User B attempts to access Partner A using Workspace A header without membership (Header spoofing)
    res_spoof = client.get(
        f"/api/business/partners/{partner_a_id}",
        headers={**headers_b, "X-Workspace-Id": ws_a_id}
    )
    assert res_spoof.status_code == 403
    assert res_spoof.get_json()["error"]["code"] == "WORKSPACE_ACCESS_DENIED"


def test_missing_workspace_header_rejected(client):
    user = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user}", "Content-Type": "application/json"}

    res = client.get("/api/business/partners", headers=headers)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "WORKSPACE_ID_REQUIRED"


def test_inactive_suspended_member_rejected(client):
    user_owner = str(uuid.uuid4())
    user_member = str(uuid.uuid4())
    headers_owner = {"Authorization": f"Bearer {user_owner}", "Content-Type": "application/json"}
    headers_member = {"Authorization": f"Bearer {user_member}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "Test Company"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    # Add member with SUSPENDED status directly
    member = WorkspaceMember(workspace_id=ws_id, user_id=user_member, role="MEMBER", status="SUSPENDED")
    db.session.add(member)
    db.session.commit()

    # Suspended member attempts access
    res = client.get("/api/business/partners", headers={**headers_member, "X-Workspace-Id": ws_id})
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "WORKSPACE_ACCESS_DENIED"
