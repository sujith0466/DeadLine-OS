"""
B3 Test Suite — Payment Allocation & Settlement
===============================================
Tests multi-invoice allocation, partial settlement, and conservation math.
"""

import uuid


def test_multi_invoice_payment_allocation(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Alloc Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Create two invoices
    res_inv1 = client.post("/api/business/invoices", headers=ws_headers, json={"total_amount": "10000.00"})
    inv1_id = res_inv1.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv1_id}/issue", headers=ws_headers)

    res_inv2 = client.post("/api/business/invoices", headers=ws_headers, json={"total_amount": "15000.00"})
    inv2_id = res_inv2.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv2_id}/issue", headers=ws_headers)

    # 2. Record lump-sum customer payment of 20,000
    res_tx = client.post("/api/business/transactions", headers=ws_headers, json={"transaction_type": "INCOME", "amount": "20000.00"})
    tx_id = res_tx.get_json()["data"]["transaction"]["id"]

    # 3. Allocate 10,000 to Inv1 (fully pays it) and 10,000 to Inv2 (partially pays it)
    alloc_payload = {
        "transaction_id": tx_id,
        "allocations": [
            {"invoice_id": inv1_id, "allocated_amount": "10000.00"},
            {"invoice_id": inv2_id, "allocated_amount": "10000.00"}
        ]
    }

    res_alloc = client.post("/api/business/allocations", headers=ws_headers, json=alloc_payload)
    assert res_alloc.status_code == 201
    assert len(res_alloc.get_json()["data"]["allocations"]) == 2

    # 4. Check Invoice 1 status -> PAID (balance_due == 0.00)
    res_get_inv1 = client.get(f"/api/business/invoices/{inv1_id}", headers=ws_headers)
    inv1 = res_get_inv1.get_json()["data"]["invoice"]
    assert inv1["status"] == "PAID"
    assert inv1["paid_amount"] == "10000.00"
    assert inv1["balance_due"] == "0.00"

    # 5. Check Invoice 2 status -> PARTIALLY_PAID (balance_due == 5000.00)
    res_get_inv2 = client.get(f"/api/business/invoices/{inv2_id}", headers=ws_headers)
    inv2 = res_get_inv2.get_json()["data"]["invoice"]
    assert inv2["status"] == "PARTIALLY_PAID"
    assert inv2["paid_amount"] == "10000.00"
    assert inv2["balance_due"] == "5000.00"


def test_allocation_exceeding_transaction_balance_rejected(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Alloc Overflow Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    res_inv = client.post("/api/business/invoices", headers=ws_headers, json={"total_amount": "10000.00"})
    inv_id = res_inv.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)

    res_tx = client.post("/api/business/transactions", headers=ws_headers, json={"transaction_type": "INCOME", "amount": "5000.00"})
    tx_id = res_tx.get_json()["data"]["transaction"]["id"]

    # Attempt to allocate 8000 from a 5000 tx
    res_alloc = client.post("/api/business/allocations", headers=ws_headers, json={
        "transaction_id": tx_id,
        "allocations": [{"invoice_id": inv_id, "allocated_amount": "8000.00"}]
    })
    assert res_alloc.status_code == 400
    assert res_alloc.get_json()["error"]["code"] == "INSUFFICIENT_TRANSACTION_BALANCE"
