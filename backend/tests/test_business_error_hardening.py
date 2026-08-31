"""
B8 Test Suite — Business OS Error Hardening & Information Leakage Prevention
============================================================================
Ensures error responses are properly structured and do not expose raw database errors, secrets, or stack traces.
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
    assert "password" not in str(err_json).lower()
    assert "secret" not in str(err_json).lower()


def test_unauthenticated_request_sanitized_401(client):
    """
    Verify unauthenticated access returns clean 401 envelope without internal details.
    """
    res = client.get("/api/business/invoices")
    assert res.status_code == 401
    data = res.get_json()
    assert data["status"] == "error"
    assert "Traceback" not in str(data)


def test_nonexistent_entity_sanitized_404(client, mock_auth_headers):
    """
    Verify 404 response on missing item is clean and structured.
    """
    ws_res = client.post(
        "/api/business/workspaces",
        headers=mock_auth_headers,
        json={"name": "404 Test Workspace", "base_currency": "INR"}
    )
    ws_id = ws_res.get_json()["data"]["workspace"]["id"]
    ws_headers = {**mock_auth_headers, "X-Workspace-Id": ws_id}

    res = client.get(f"/api/business/invoices/{uuid.uuid4()}", headers=ws_headers)
    assert res.status_code == 404
    data = res.get_json()
    assert data["status"] == "error"
    assert "Traceback" not in str(data)
