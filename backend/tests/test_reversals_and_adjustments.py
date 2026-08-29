"""
B3 Test Suite — Append-Only Reversals & Corrections
===================================================
Tests formal reversal protocol with counter-adjustment generation,
allocation reversal, and dynamic invoice balance restoration.
"""

import uuid


def test_transaction_reversal_restores_invoice_balance(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Reversal Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Create and issue invoice for 10,000
    res_inv = client.post("/api/business/invoices", headers=ws_headers, json={"total_amount": "10000.00"})
    inv_id = res_inv.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)

    # 2. Record payment of 10,000 and allocate
    res_tx = client.post("/api/business/transactions", headers=ws_headers, json={"transaction_type": "INCOME", "amount": "10000.00"})
    tx_id = res_tx.get_json()["data"]["transaction"]["id"]
    client.post("/api/business/allocations", headers=ws_headers, json={
        "transaction_id": tx_id,
        "allocations": [{"invoice_id": inv_id, "allocated_amount": "10000.00"}]
    })

    # Verify invoice is PAID
    inv_before = client.get(f"/api/business/invoices/{inv_id}", headers=ws_headers).get_json()["data"]["invoice"]
    assert inv_before["status"] == "PAID"
    assert inv_before["balance_due"] == "0.00"

    # 3. Reverse payment transaction (e.g. Bounced cheque / Chargeback)
    res_rev = client.post(
        f"/api/business/transactions/{tx_id}/reverse",
        headers=ws_headers,
        json={"reason": "Customer cheque bounced with insufficient funds"}
    )
    assert res_rev.status_code == 200
    assert res_rev.get_json()["data"]["transaction"]["status"] == "REVERSED"

    # 4. Verify Invoice is restored to ISSUED and balance_due == 10000.00
    inv_after = client.get(f"/api/business/invoices/{inv_id}", headers=ws_headers).get_json()["data"]["invoice"]
    assert inv_after["status"] == "ISSUED"
    assert inv_after["paid_amount"] == "0.00"
    assert inv_after["balance_due"] == "10000.00"

    # 5. Immutability: Cannot reverse an already reversed transaction
    res_rerev = client.post(
        f"/api/business/transactions/{tx_id}/reverse",
        headers=ws_headers,
        json={"reason": "Attempting duplicate reversal"}
    )
    assert res_rerev.status_code == 400
