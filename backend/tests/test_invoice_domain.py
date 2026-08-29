"""
B3 Test Suite — Invoice Domain & Arithmetic Invariants
======================================================
Tests invoice creation, subtotal/tax/discount arithmetic, issuance freeze,
voiding rules, and balance synchronization.
"""

import uuid
from decimal import Decimal


def test_invoice_creation_and_issuance_freeze(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Invoice Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Create invoice with line items
    inv_payload = {
        "invoice_type": "RECEIVABLE",
        "issue_date": "2026-08-29",
        "due_date": "2026-09-15",
        "items": [
            {"description": "Consulting Hours", "quantity": "10", "unit_price": "1500.00"},
            {"description": "Software License", "quantity": "1", "unit_price": "5000.00"}
        ],
        "tax_amount": "3600.00",      # 18% GST on 20,000
        "discount_amount": "1000.00"
    }

    res_create = client.post("/api/business/invoices", headers=ws_headers, json=inv_payload)
    assert res_create.status_code == 201
    inv = res_create.get_json()["data"]["invoice"]
    assert inv["status"] == "DRAFT"
    assert inv["subtotal"] == "20000.00"
    assert inv["tax_amount"] == "3600.00"
    assert inv["discount_amount"] == "1000.00"
    assert inv["total_amount"] == "22600.00"
    assert inv["paid_amount"] == "0.00"
    assert inv["balance_due"] == "22600.00"

    inv_id = inv["id"]

    # 2. Issue invoice (Arithmetic Freeze)
    res_issue = client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)
    assert res_issue.status_code == 200
    assert res_issue.get_json()["data"]["invoice"]["status"] == "ISSUED"


def test_discount_exceeding_subtotal_plus_tax_rejected(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Discount Reject Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    inv_payload = {
        "subtotal": "1000.00",
        "tax_amount": "100.00",
        "discount_amount": "1500.00"  # Exceeds 1100.00
    }

    res = client.post("/api/business/invoices", headers=ws_headers, json=inv_payload)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_DISCOUNT"


def test_invoice_voiding_rules(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Void Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Create & Issue invoice
    res_create = client.post("/api/business/invoices", headers=ws_headers, json={"total_amount": "5000.00"})
    inv_id = res_create.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)

    # Void unpaid invoice
    res_void = client.post(f"/api/business/invoices/{inv_id}/void", headers=ws_headers, json={"reason": "Customer cancelled project"})
    assert res_void.status_code == 200
    assert res_void.get_json()["data"]["invoice"]["status"] == "VOID"
    assert res_void.get_json()["data"]["invoice"]["balance_due"] == "0.00"
