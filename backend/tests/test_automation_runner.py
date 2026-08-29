"""
B6 Test Suite — Automation Runner & Idempotency
===============================================
Tests deterministic invoice generation, cycle idempotency, and batch execution.
"""

import uuid
from datetime import date
from models.business import Invoice


def test_automation_runner_invoice_generation_and_idempotency(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Runner Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Partner
    res_part = client.post("/api/business/partners", headers=ws_headers, json={
        "name": "Retainer Client",
        "partner_type": "CUSTOMER"
    })
    part_id = res_part.get_json()["data"]["partner"]["id"]

    # 1. Create active recurring obligation due today
    today_str = date.today().isoformat()
    res_obl = client.post("/api/business/recurring", headers=ws_headers, json={
        "title": "Software Retainer",
        "partner_id": part_id,
        "obligation_type": "RECEIVABLE",
        "frequency": "MONTHLY",
        "amount": "120000.00",
        "start_date": today_str
    })
    obl_id = res_obl.get_json()["data"]["obligation"]["id"]

    # 2. Trigger single execution
    res_trig = client.post(f"/api/business/recurring/{obl_id}/trigger", headers=ws_headers)
    assert res_trig.status_code == 200
    data = res_trig.get_json()["data"]
    assert data["status"] == "SUCCESS"
    assert data["generated_entity_type"] == "INVOICE"
    inv_id = data["generated_entity_id"]

    # Verify generated invoice in B3 ledger
    inv = Invoice.query.get(inv_id)
    assert inv is not None
    assert inv.workspace_id == ws_id
    assert str(inv.total_amount) == "120000.00"

    # 3. Trigger again on same date -> Must be SKIPPED due to idempotency
    res_trig_repeat = client.post(f"/api/business/recurring/{obl_id}/trigger", headers=ws_headers, json={"target_date": today_str})
    assert res_trig_repeat.status_code == 200
    repeat_data = res_trig_repeat.get_json()["data"]
    assert repeat_data["status"] == "SKIPPED"

    # 4. Verify batch execution
    res_batch = client.post("/api/business/automation/run", headers=ws_headers, json={"as_of_date": today_str})
    assert res_batch.status_code == 200

    # 5. Verify logs
    res_logs = client.get("/api/business/automation/logs", headers=ws_headers)
    assert res_logs.status_code == 200
    assert res_logs.get_json()["data"]["count"] >= 1
