"""
B1 Functional Test Suite — Commercial Partner Registry
======================================================
Tests partner creation, validation, duplicate prevention, search, and archival.
"""

import uuid


def test_partner_lifecycle_and_duplicate_prevention(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    # Create workspace
    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Trade Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Create Partner
    res_create = client.post(
        "/api/business/partners",
        headers=ws_headers,
        json={
            "partner_type": "CUSTOMER",
            "name": "Reliance Retail",
            "legal_name": "Reliance Retail Ventures Ltd",
            "tax_identifier": "GST27AABCR1234K1ZM",
            "credit_period_days": 45
        }
    )
    assert res_create.status_code == 201
    partner_id = res_create.get_json()["data"]["partner"]["id"]
    assert res_create.get_json()["data"]["partner"]["credit_period_days"] == 45

    # 2. Duplicate Name Rejection
    res_dupe = client.post(
        "/api/business/partners",
        headers=ws_headers,
        json={"partner_type": "CUSTOMER", "name": "Reliance Retail"}
    )
    assert res_dupe.status_code == 409
    assert "already exists" in res_dupe.get_json()["error"]["message"]

    # 3. Search Partner
    res_search = client.get("/api/business/partners?search=Reliance", headers=ws_headers)
    assert res_search.status_code == 200
    assert len(res_search.get_json()["data"]["partners"]) == 1

    # 4. Update Partner
    res_update = client.patch(
        f"/api/business/partners/{partner_id}",
        headers=ws_headers,
        json={"phone": "+91 9876543210", "credit_period_days": 60}
    )
    assert res_update.status_code == 200
    assert res_update.get_json()["data"]["partner"]["credit_period_days"] == 60

    # 5. Archive Partner
    res_archive = client.post(
        f"/api/business/partners/{partner_id}/archive",
        headers=ws_headers,
        json={"reason": "Contract expired"}
    )
    assert res_archive.status_code == 200
    assert res_archive.get_json()["data"]["partner"]["status"] == "ARCHIVED"
