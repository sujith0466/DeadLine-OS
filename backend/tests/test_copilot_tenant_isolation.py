"""
B4 Test Suite — Copilot Tenant Isolation & RBAC
================================================
Verifies cross-tenant prompt context containment and role-based permissions.
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db


def test_cross_tenant_copilot_context_isolation(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # Tenant A records 5,00,000 cash
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A Secret Corp"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]
    client.post("/api/business/transactions", headers={**headers_a, "X-Workspace-Id": ws_a_id}, json={"transaction_type": "INCOME", "amount": "500000.00"})

    # Tenant B creates workspace with 1,000 cash
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "Tenant B Tiny Corp"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]
    client.post("/api/business/transactions", headers={**headers_b, "X-Workspace-Id": ws_b_id}, json={"transaction_type": "INCOME", "amount": "1000.00"})

    # Tenant B queries Copilot
    res_copilot_b = client.post(
        "/api/business/copilot/query",
        headers={**headers_b, "X-Workspace-Id": ws_b_id},
        json={"prompt": "How much cash do we have?"}
    )
    assert res_copilot_b.status_code == 200
    data_b = res_copilot_b.get_json()["data"]
    # Tenant B must see 1000.00, NEVER 500000.00
    assert data_b["context_summary"]["confirmed_cash"] == "1000.00"


def test_viewer_role_denied_copilot_query(client):
    owner_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())

    db.session.add_all([
        User(id=owner_id, email="owner@copilot.com"),
        User(id=viewer_id, email="viewer@copilot.com")
    ])
    db.session.commit()

    headers_owner = {"Authorization": f"Bearer {owner_id}", "Content-Type": "application/json"}
    headers_viewer = {"Authorization": f"Bearer {viewer_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "Copilot RBAC Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role="VIEWER", status="ACTIVE"))
    db.session.commit()

    # VIEWER denied copilot query (403)
    res_v = client.post(
        "/api/business/copilot/query",
        headers={**headers_viewer, "X-Workspace-Id": ws_id},
        json={"prompt": "Summarize financials"}
    )
    assert res_v.status_code == 403
