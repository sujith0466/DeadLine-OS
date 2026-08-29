"""
B7 Test Suite — Inter-Entity Transfers
======================================
Tests recording and querying inter-entity transfers.
"""

import uuid


def test_inter_entity_transfer_creation(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws1 = client.post("/api/business/workspaces", headers=headers, json={"name": "Source Workspace"})
    ws1_id = res_ws1.get_json()["data"]["workspace"]["id"]
    ws1_headers = {**headers, "X-Workspace-Id": ws1_id}

    res_ws2 = client.post("/api/business/workspaces", headers=headers, json={"name": "Destination Workspace"})
    ws2_id = res_ws2.get_json()["data"]["workspace"]["id"]

    res_trans = client.post("/api/business/transfers", headers=ws1_headers, json={
        "destination_workspace_id": ws2_id,
        "amount": "45000.00",
        "reference_note": "Quarterly management fee"
    })
    assert res_trans.status_code == 201
    transfer = res_trans.get_json()["data"]["transfer"]
    assert transfer["source_workspace_id"] == ws1_id
    assert transfer["destination_workspace_id"] == ws2_id
    assert str(transfer["amount"]) == "45000.00"
    assert transfer["status"] == "SETTLED"
