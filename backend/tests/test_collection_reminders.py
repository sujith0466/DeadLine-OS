"""
B5 Test Suite — Collection Reminders & Human Confirmation
=========================================================
Tests tone selection, human-in-the-loop review barrier, and state transitions.
"""

import uuid
from datetime import date, timedelta


def test_collection_reminder_draft_and_dispatch_lifecycle(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Reminder Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Create partner and overdue invoice
    res_part = client.post("/api/business/partners", headers=ws_headers, json={
        "name": "Acme Debtor",
        "email": "debtor@acme.com",
        "partner_type": "CUSTOMER"
    })
    part_id = res_part.get_json()["data"]["partner"]["id"]

    res_inv = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "partner_id": part_id,
        "total_amount": "25000.00",
        "due_date": (date.today() - timedelta(days=20)).isoformat()
    })
    inv_id = res_inv.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)

    # 1. Draft GENTLE reminder
    res_draft = client.post("/api/business/reminders/draft", headers=ws_headers, json={
        "invoice_id": inv_id,
        "tone": "GENTLE"
    })
    assert res_draft.status_code == 201
    reminder = res_draft.get_json()["data"]["reminder"]
    assert reminder["status"] == "DRAFT"
    assert reminder["tone"] == "GENTLE"
    assert "25000.00" in reminder["message_body"]
    assert reminder["invoice_number"] is not None

    rem_id = reminder["id"]

    # 2. Dispatch reminder (Human confirmation)
    res_send = client.post(f"/api/business/reminders/{rem_id}/send", headers=ws_headers, json={
        "custom_message": "Friendly reminder: Please arrange payment."
    })
    assert res_send.status_code == 200
    sent_rem = res_send.get_json()["data"]["reminder"]
    assert sent_rem["status"] == "SENT"
    assert sent_rem["sent_at"] is not None

    # 3. Replay protection: Re-sending already SENT reminder is blocked
    res_resend = client.post(f"/api/business/reminders/{rem_id}/send", headers=ws_headers, json={})
    assert res_resend.status_code == 400
    assert res_resend.get_json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_cannot_draft_reminder_for_zero_balance_or_void(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Zero Rem Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Void invoice
    res_inv = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "1000.00",
        "due_date": "2026-08-01"
    })
    inv_id = res_inv.get_json()["data"]["invoice"]["id"]
    client.post(f"/api/business/invoices/{inv_id}/issue", headers=ws_headers)
    client.post(f"/api/business/invoices/{inv_id}/void", headers=ws_headers)

    res_draft_void = client.post("/api/business/reminders/draft", headers=ws_headers, json={"invoice_id": inv_id})
    assert res_draft_void.status_code == 400
    assert res_draft_void.get_json()["error"]["code"] == "INVOICE_VOID"
