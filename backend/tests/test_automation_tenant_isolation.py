"""
B6 Test Suite — Automation Multi-Tenant Isolation & RBAC
========================================================
Verifies cross-tenant isolation on recurring schedules and RBAC permissions.
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db


def test_cross_tenant_recurring_isolation(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # Tenant A creates recurring obligation
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A Secrets"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]
    res_obl_a = client.post("/api/business/recurring", headers={**headers_a, "X-Workspace-Id": ws_a_id}, json={
        "title": "Secret Retainer A",
        "obligation_type": "RECEIVABLE",
        "frequency": "MONTHLY",
        "amount": "990000.00",
        "start_date": "2026-09-01"
    })
    obl_a_id = res_obl_a.get_json()["data"]["obligation"]["id"]

    # Tenant B creates workspace with NO obligations
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "Tenant B Clean"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]

    # Tenant B lists obligations -> Must see 0
    res_list_b = client.get("/api/business/recurring", headers={**headers_b, "X-Workspace-Id": ws_b_id})
    assert res_list_b.status_code == 200
    assert res_list_b.get_json()["data"]["count"] == 0

    # Tenant B tries to trigger Tenant A's obligation -> 404
    res_trig_b = client.post(f"/api/business/recurring/{obl_a_id}/trigger", headers={**headers_b, "X-Workspace-Id": ws_b_id})
    assert res_trig_b.status_code == 404


def test_viewer_role_denied_recurring_creation(client):
    owner_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())

    db.session.add_all([
        User(id=owner_id, email="owner@autom.com"),
        User(id=viewer_id, email="viewer@autom.com")
    ])
    db.session.commit()

    headers_owner = {"Authorization": f"Bearer {owner_id}", "Content-Type": "application/json"}
    headers_viewer = {"Authorization": f"Bearer {viewer_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "RBAC Autom Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role="VIEWER", status="ACTIVE"))
    db.session.commit()

    # VIEWER denied creating recurring obligation (403)
    res_create = client.post(
        "/api/business/recurring",
        headers={**headers_viewer, "X-Workspace-Id": ws_id},
        json={"title": "Denied Retainer", "obligation_type": "RECEIVABLE", "amount": "100.00"}
    )
    assert res_create.status_code == 403
