"""
B8 Test Suite — Business OS Error Hardening & Information Leakage Prevention
============================================================================
Ensures error responses are properly structured and do not expose raw database errors or stack traces.
"""

import uuid


def test_malformed_json_returns_clean_400(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}
    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Error Hardening Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    # Post invalid transaction amount
    res_err = client.post(
        "/api/business/transactions",
        headers={**headers, "X-Workspace-Id": ws_id},
        json={"transaction_type": "INCOME", "amount": "NOT_A_NUMBER", "transaction_date": "2026-08-29"}
    )
    assert res_err.status_code == 400
    err_json = res_err.get_json()
    assert err_json["status"] == "error"
    assert "error" in err_json
    assert "Traceback" not in str(err_json)
    assert "sqlite3" not in str(err_json).lower()
