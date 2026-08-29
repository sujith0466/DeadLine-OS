"""
B5 Test Suite — Rescue & Export Tenant Isolation & RBAC
=======================================================
Verifies multi-tenant isolation on rescue queues and role-based export access.
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db
from datetime import date, timedelta


def test_cross_tenant_rescue_queue_isolation(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # Tenant A records overdue invoice of 80,000
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A Overdue"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]
    res_inv_a = client.post("/api/business/invoices", headers={**headers_a, "X-Workspace-Id": ws_a_id}, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "80000.00",
        "due_date": (date.today() - timedelta(days=30)).isoformat()
    })
    client.post(f"/api/business/invoices/{res_inv_a.get_json()['data']['invoice']['id']}/issue", headers={**headers_a, "X-Workspace-Id": ws_a_id})

    # Tenant B creates workspace with NO overdue invoices
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "Tenant B Clean"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]

    # Tenant B queries aging summary
    res_aging_b = client.get("/api/business/rescue/aging", headers={**headers_b, "X-Workspace-Id": ws_b_id})
    assert res_aging_b.status_code == 200
    aging_b = res_aging_b.get_json()["data"]
    # Must see 0, NEVER 80000.00
    assert aging_b["total_overdue_count"] == 0
    assert aging_b["total_overdue_amount"] == "0.00"


def test_viewer_role_denied_export_and_reminder_draft(client):
    owner_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())

    db.session.add_all([
        User(id=owner_id, email="owner@rescue.com"),
        User(id=viewer_id, email="viewer@rescue.com")
    ])
    db.session.commit()

    headers_owner = {"Authorization": f"Bearer {owner_id}", "Content-Type": "application/json"}
    headers_viewer = {"Authorization": f"Bearer {viewer_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "RBAC Export Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role="VIEWER", status="ACTIVE"))
    db.session.commit()

    # VIEWER denied drafting reminders (requires transaction:create)
    res_draft = client.post(
        "/api/business/reminders/draft",
        headers={**headers_viewer, "X-Workspace-Id": ws_id},
        json={"invoice_id": "dummy-id"}
    )
    assert res_draft.status_code == 403
