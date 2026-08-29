"""
B3 Test Suite — Financial Multi-Tenancy & RBAC
==============================================
Verifies cross-tenant invoice/transaction IDOR defense and 5-tier RBAC rules.
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db


def test_cross_tenant_invoice_and_transaction_isolation(client):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    headers_a = {"Authorization": f"Bearer {user_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {user_b}", "Content-Type": "application/json"}

    # Tenant A creates invoice and transaction
    res_ws_a = client.post("/api/business/workspaces", headers=headers_a, json={"name": "Tenant A Financial"})
    ws_a_id = res_ws_a.get_json()["data"]["workspace"]["id"]
    ws_a_headers = {**headers_a, "X-Workspace-Id": ws_a_id}

    res_inv_a = client.post("/api/business/invoices", headers=ws_a_headers, json={"total_amount": "50000.00"})
    inv_a_id = res_inv_a.get_json()["data"]["invoice"]["id"]

    res_tx_a = client.post("/api/business/transactions", headers=ws_a_headers, json={"transaction_type": "INCOME", "amount": "50000.00"})
    tx_a_id = res_tx_a.get_json()["data"]["transaction"]["id"]

    # Tenant B creates workspace
    res_ws_b = client.post("/api/business/workspaces", headers=headers_b, json={"name": "Tenant B Financial"})
    ws_b_id = res_ws_b.get_json()["data"]["workspace"]["id"]
    ws_b_headers = {**headers_b, "X-Workspace-Id": ws_b_id}

    # Tenant B attempts IDOR on Tenant A's invoice
    res_idor_inv = client.get(f"/api/business/invoices/{inv_a_id}", headers=ws_b_headers)
    assert res_idor_inv.status_code == 404

    # Tenant B attempts IDOR on Tenant A's transaction
    res_idor_tx = client.get(f"/api/business/transactions/{tx_a_id}", headers=ws_b_headers)
    assert res_idor_tx.status_code == 404

    # Tenant B attempts to allocate payment to Tenant A's invoice
    res_cross_alloc = client.post("/api/business/allocations", headers=ws_b_headers, json={
        "transaction_id": tx_a_id,
        "allocations": [{"invoice_id": inv_a_id, "allocated_amount": "50000.00"}]
    })
    assert res_cross_alloc.status_code == 404


def test_viewer_denied_invoice_creation_and_member_denied_reversal(client):
    owner_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())
    member_id = str(uuid.uuid4())

    db.session.add_all([
        User(id=owner_id, email="owner@rbac.com"),
        User(id=viewer_id, email="viewer@rbac.com"),
        User(id=member_id, email="member@rbac.com")
    ])
    db.session.commit()

    headers_owner = {"Authorization": f"Bearer {owner_id}", "Content-Type": "application/json"}
    headers_viewer = {"Authorization": f"Bearer {viewer_id}", "Content-Type": "application/json"}
    headers_member = {"Authorization": f"Bearer {member_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "RBAC Roles Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    db.session.add_all([
        WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role="VIEWER", status="ACTIVE"),
        WorkspaceMember(workspace_id=ws_id, user_id=member_id, role="MEMBER", status="ACTIVE")
    ])
    db.session.commit()

    # 1. VIEWER cannot create invoice (403)
    res_v_create = client.post("/api/business/invoices", headers={**headers_viewer, "X-Workspace-Id": ws_id}, json={"total_amount": "1000.00"})
    assert res_v_create.status_code == 403

    # 2. Owner creates transaction
    res_tx = client.post("/api/business/transactions", headers={**headers_owner, "X-Workspace-Id": ws_id}, json={"transaction_type": "INCOME", "amount": "5000.00"})
    tx_id = res_tx.get_json()["data"]["transaction"]["id"]

    # 3. MEMBER cannot reverse transaction (403 - requires transaction:reverse which only OWNER/ADMIN have)
    res_m_rev = client.post(f"/api/business/transactions/{tx_id}/reverse", headers={**headers_member, "X-Workspace-Id": ws_id}, json={"reason": "Member trying to reverse"})
    assert res_m_rev.status_code == 403
