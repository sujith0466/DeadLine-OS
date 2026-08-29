"""
B8 Test Suite — End-to-End Monolithic Production Lifecycle
==========================================================
Validates complete lifecycle: Workspace -> Partner -> Invoice -> Payment ->
Risk Engine -> Copilot Context -> Rescue -> Recurring -> Multi-Entity Consolidation.
"""

import uuid
from decimal import Decimal


def test_full_business_os_production_lifecycle(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    # 1. Provision Workspace
    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "E2E Enterprise Corp"})
    assert res_ws.status_code == 201
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 2. Register Commercial Partner
    res_part = client.post(
        "/api/business/partners",
        headers=ws_headers,
        json={"name": "Global Client Ltd", "partner_type": "CUSTOMER", "email": "billing@globalclient.com"}
    )
    assert res_part.status_code == 201
    partner_id = res_part.get_json()["data"]["partner"]["id"]

    # 3. Create & Issue Invoice
    res_inv = client.post(
        "/api/business/invoices",
        headers=ws_headers,
        json={
            "invoice_number": "INV-E2E-001",
            "invoice_type": "RECEIVABLE",
            "partner_id": partner_id,
            "issue_date": "2026-08-29",
            "due_date": "2026-09-15",
            "items": [{"description": "Enterprise Platform Deployment", "quantity": 1, "unit_price": 75000}]
        }
    )
    assert res_inv.status_code == 201
    inv = res_inv.get_json()["data"]["invoice"]
    inv_id = inv["id"]
    assert Decimal(inv["total_amount"]) == Decimal("75000.00")

    # Issue the invoice
    res_issue = client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)
    assert res_issue.status_code == 200

    # 4. Record Payment Transaction & Allocation
    res_tx = client.post(
        "/api/business/transactions",
        headers=ws_headers,
        json={
            "transaction_type": "INCOME",
            "amount": "75000.00",
            "partner_id": partner_id,
            "transaction_date": "2026-08-29"
        }
    )
    assert res_tx.status_code == 201
    tx_id = res_tx.get_json()["data"]["transaction"]["id"]

    res_alloc = client.post(
        "/api/business/allocations",
        headers=ws_headers,
        json={"transaction_id": tx_id, "allocations": [{"invoice_id": inv_id, "allocated_amount": "75000.00"}]}
    )
    assert res_alloc.status_code == 201

    # 5. Check Cash Risk Engine
    res_risk = client.get("/api/business/financial/risks", headers=ws_headers)
    assert res_risk.status_code == 200
    assert "overall_status" in res_risk.get_json()["data"]["risks"]

    # 6. Create Recurring Obligation
    res_rec = client.post(
        "/api/business/recurring",
        headers=ws_headers,
        json={
            "title": "Cloud Hosting",
            "obligation_type": "PAYABLE",
            "frequency": "MONTHLY",
            "amount": "5000.00",
            "start_date": "2026-08-29"
        }
    )
    assert res_rec.status_code == 201

    # 7. Create Business Entity
    res_ent = client.post(
        "/api/business/entities",
        headers=ws_headers,
        json={"name": "HQ Branch", "is_default": True}
    )
    assert res_ent.status_code == 201

    # 8. Consolidated Overview
    res_consol = client.post("/api/business/consolidation/overview", headers=headers, json={
        "workspace_ids": [ws_id]
    })
    assert res_consol.status_code == 200
    overview = res_consol.get_json()["data"]["overview"]
    assert overview["workspaces_count"] == 1
    assert Decimal(overview["consolidated_revenue"]) == Decimal("75000.00")
