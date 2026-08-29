"""
B3 Test Suite — Staging to Financial Commit Gateway
===================================================
Tests converting confirmed staging candidates into invoices and transactions.
"""

import uuid


def test_staged_extraction_commit_to_invoice(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Gateway Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Capture text (candidate created in NEEDS_REVIEW)
    res_cap = client.post(
        "/api/business/capture/text",
        headers=ws_headers,
        json={"text": "Invoice to ACME Solutions for 25000 due next week"}
    )
    staged_id = res_cap.get_json()["data"]["staged_extraction"]["id"]

    # 2. Attempt commit before confirmation -> Rejected 400
    res_early = client.post(f"/api/business/staging/{staged_id}/commit", headers=ws_headers)
    assert res_early.status_code == 400
    assert res_early.get_json()["error"]["code"] == "ITEM_NOT_CONFIRMED"

    # 3. Confirm candidate
    client.post(f"/api/business/staging/{staged_id}/confirm", headers=ws_headers)

    # 4. Commit candidate to Invoice
    res_commit = client.post(f"/api/business/staging/{staged_id}/commit", headers=ws_headers, json={"target_domain": "INVOICE"})
    assert res_commit.status_code == 201
    assert res_commit.get_json()["data"]["target"] == "INVOICE"
    inv = res_commit.get_json()["data"]["entity"]
    assert inv["staged_extraction_id"] == staged_id
    assert inv["total_amount"] == "25000.00"
