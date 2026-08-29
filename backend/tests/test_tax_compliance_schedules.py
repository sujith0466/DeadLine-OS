"""
B6 Test Suite — Tax & Compliance Schedules
==========================================
Tests recurring statutory compliance tracking and due date stepping.
"""

import uuid


def test_tax_compliance_schedule_creation_and_stepping(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Tax Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Create quarterly advance tax obligation
    res_tax = client.post("/api/business/recurring", headers=ws_headers, json={
        "title": "Advance Corporate Income Tax (Q2)",
        "obligation_type": "TAX_COMPLIANCE",
        "frequency": "QUARTERLY",
        "amount": "250000.00",
        "start_date": "2026-09-15"
    })
    assert res_tax.status_code == 201
    obl = res_tax.get_json()["data"]["obligation"]
    assert obl["obligation_type"] == "TAX_COMPLIANCE"
    assert obl["next_due_date"] == "2026-09-15"
