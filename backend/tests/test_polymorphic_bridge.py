"""
B4 Test Suite — Polymorphic Personal OS Bridge Adapter
=======================================================
Tests read-only cross-domain schedule feed projection and guarantees zero
contamination of Personal OS tables.
"""

import uuid
from models.schedule import ScheduleSlot
from models.task import Task


def test_bridge_virtual_schedule_feed_and_zero_personal_contamination(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    # Count Personal OS records before
    slots_before = ScheduleSlot.query.count()
    tasks_before = Task.query.count()

    # Create workspace and invoice
    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Bridge Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    res_inv = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "75000.00",
        "due_date": "2026-09-10"
    })
    inv_id = res_inv.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)

    # Query Polymorphic Bridge Feed
    res_feed = client.get("/api/business/bridge/feed?window_days=30", headers=headers)
    assert res_feed.status_code == 200
    feed = res_feed.get_json()["data"]
    assert feed["count"] >= 1

    virt_item = next((item for item in feed["virtual_obligations"] if item["entity_id"] == inv_id), None)
    assert virt_item is not None
    assert virt_item["source_domain"] == "BUSINESS_OS"
    assert virt_item["amount"] == "75000.00"

    # GUARANTEE: Zero Personal OS tables were modified or written to
    assert ScheduleSlot.query.count() == slots_before
    assert Task.query.count() == tasks_before
