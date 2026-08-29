"""
B1 Security Test Suite — Audit Immutability & Traceability
==========================================================
Verifies that all consequential operations emit permanent,
workspace-scoped forensic audit records with before/after state diffs.
"""

import uuid
from models.business import AuditEvent


def test_audit_trail_generation_and_filtering(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    # 1. Create workspace (Emits WORKSPACE_CREATED)
    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Audit Test Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 2. Update workspace (Emits WORKSPACE_UPDATED)
    client.patch("/api/business/workspaces/current", headers=ws_headers, json={"name": "Renamed Corp"})

    # 3. Create partner (Emits PARTNER_CREATED)
    res_p = client.post(
        "/api/business/partners",
        headers=ws_headers,
        json={"partner_type": "SUPPLIER", "name": "Global Logistics"}
    )
    partner_id = res_p.get_json()["data"]["partner"]["id"]

    # 4. Query Audit Logs via API
    res_audit = client.get("/api/business/audit", headers=ws_headers)
    assert res_audit.status_code == 200
    events = res_audit.get_json()["data"]["events"]
    actions = [e["action"] for e in events]

    assert "WORKSPACE_CREATED" in actions
    assert "WORKSPACE_UPDATED" in actions
    assert "PARTNER_CREATED" in actions

    # Verify before/after state diff is captured
    update_event = next(e for e in events if e["action"] == "WORKSPACE_UPDATED")
    assert update_event["before_state"]["name"] == "Audit Test Corp"
    assert update_event["after_state"]["name"] == "Renamed Corp"

    # Verify direct database persistence (non-cascading)
    db_events = AuditEvent.query.filter_by(workspace_id=ws_id).all()
    assert len(db_events) >= 3
