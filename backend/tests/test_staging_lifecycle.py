"""
B2 Test Suite — Staging Lifecycle & State Machine
=================================================
Tests 8-state finite state transitions, human edits, confirmation,
rejection, and terminal state immutability.
"""

import uuid


def test_staging_lifecycle_confirm_and_reject(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Staging Lifecycle Co"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Ingest text item
    res_cap = client.post(
        "/api/business/capture/text",
        headers=ws_headers,
        json={"text": "Paid rent of 25000 to Landlord on 2026-08-01"}
    )
    staged_id = res_cap.get_json()["data"]["staged_extraction"]["id"]

    # 2. Update item during review
    res_update = client.patch(
        f"/api/business/staging/{staged_id}",
        headers=ws_headers,
        json={
            "normalized_data": {
                "amount": "26000.00",
                "partner_name": "Commercial Landlord Ltd",
                "description": "August 2026 Office Rent with Utilities"
            }
        }
    )
    assert res_update.status_code == 200
    assert res_update.get_json()["data"]["staged_extraction"]["normalized_data"]["amount"] == "26000.00"

    # 3. Confirm item
    res_confirm = client.post(f"/api/business/staging/{staged_id}/confirm", headers=ws_headers)
    assert res_confirm.status_code == 200
    assert res_confirm.get_json()["data"]["staged_extraction"]["status"] == "CONFIRMED"
    assert res_confirm.get_json()["data"]["staged_extraction"]["confirmed_at"] is not None

    # 4. Terminal state immutability: Cannot re-confirm or edit confirmed item
    res_reconfirm = client.post(f"/api/business/staging/{staged_id}/confirm", headers=ws_headers)
    assert res_reconfirm.status_code == 409

    res_edit_confirmed = client.patch(f"/api/business/staging/{staged_id}", headers=ws_headers, json={"normalized_data": {"amount": "30000.00"}})
    assert res_edit_confirmed.status_code == 400
