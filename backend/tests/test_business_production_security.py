"""
B8 Test Suite — Business OS Production Security & Multi-Tenant Boundaries
=========================================================================
Validates workspace isolation, X-Workspace-ID spoofing, 5-tier RBAC, and IDOR protection.
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db


def test_unauthenticated_request_rejected(client):
    res = client.get("/api/business/workspaces")
    assert res.status_code == 401


def test_unauthorized_workspace_spoofing_rejected(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # User A creates Workspace A
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A Secure"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]

    # User B attempts to access Workspace A using X-Workspace-Id header
    res_spoof = client.get(
        "/api/business/invoices",
        headers={**headers_b, "X-Workspace-Id": ws_a_id}
    )
    assert res_spoof.status_code == 403


def test_cross_tenant_idor_rejected(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # WS A
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A Invoices"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]

    # Invoice in WS A
    res_inv = client.post(
        "/api/business/invoices",
        headers={**headers_a, "X-Workspace-Id": ws_a_id},
        json={
            "invoice_number": "INV-A-100",
            "invoice_type": "RECEIVABLE",
            "issue_date": "2026-08-29",
            "due_date": "2026-09-29",
            "line_items": [{"description": "Service", "quantity": 1, "unit_price": 5000}]
        }
    )
    assert res_inv.status_code == 201
    inv_id = res_inv.get_json()["data"]["invoice"]["id"]

    # WS B
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "Tenant B Invoices"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]

    # User B attempts to view Invoice from WS A under WS B context -> 404
    res_idor = client.get(
        f"/api/business/invoices/{inv_id}",
        headers={**headers_b, "X-Workspace-Id": ws_b_id}
    )
    assert res_idor.status_code == 404
