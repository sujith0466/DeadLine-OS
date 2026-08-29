"""
B2 Test Suite — Staging Forensic Audit Trail
============================================
Verifies emission of audit events across staging creation, edits, and confirmation.
"""

import uuid
from models.business import AuditEvent


def test_staging_audit_trail(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Audit Staging Co"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Capture text (Emits STAGED_EXTRACTION_CREATED)
    res_cap = client.post("/api/business/capture/text", headers=ws_headers, json={"text": "Expense 5000"})
    staged_id = res_cap.get_json()["data"]["staged_extraction"]["id"]

    # 2. Update item (Emits STAGED_EXTRACTION_UPDATED)
    client.patch(f"/api/business/staging/{staged_id}", headers=ws_headers, json={"normalized_data": {"amount": "5500.00"}})

    # 3. Confirm item (Emits STAGED_EXTRACTION_CONFIRMED)
    client.post(f"/api/business/staging/{staged_id}/confirm", headers=ws_headers)

    # 4. Check Audit logs
    res_audit = client.get("/api/business/audit", headers=ws_headers)
    assert res_audit.status_code == 200
    events = res_audit.get_json()["data"]["events"]
    actions = [e["action"] for e in events]

    assert "STAGED_EXTRACTION_CREATED" in actions
    assert "STAGED_EXTRACTION_UPDATED" in actions
    assert "STAGED_EXTRACTION_CONFIRMED" in actions
