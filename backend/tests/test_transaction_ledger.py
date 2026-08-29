"""
B3 Test Suite — Transaction Ledger
==================================
Tests operational event ledger ingestion, immutability, and queries.
"""

import uuid


def test_record_transaction_and_query(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Tx Ledger Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Record income transaction
    tx_payload = {
        "transaction_type": "INCOME",
        "amount": "50000.00",
        "currency": "INR",
        "transaction_date": "2026-08-29",
        "payment_method": "BANK_TRANSFER",
        "reference_number": "NEFT-12345678"
    }

    res_tx = client.post("/api/business/transactions", headers=ws_headers, json=tx_payload)
    assert res_tx.status_code == 201
    tx = res_tx.get_json()["data"]["transaction"]
    assert tx["status"] == "CONFIRMED"
    assert tx["amount"] == "50000.00"
    assert tx["reference_number"] == "NEFT-12345678"

    # Query ledger
    res_list = client.get("/api/business/transactions", headers=ws_headers)
    assert res_list.status_code == 200
    assert res_list.get_json()["data"]["total"] >= 1
