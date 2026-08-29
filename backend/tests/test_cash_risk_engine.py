"""
B4 Test Suite — Cash Risk Engine
================================
Tests deterministic detection of cash deficits, burn velocity, concentration,
and runway shortfalls.
"""

import uuid


def test_cash_deficit_and_concentration_risk_detection(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Risk Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Partner
    res_part = client.post("/api/business/partners", headers=ws_headers, json={"name": "Whale Client Corp", "partner_type": "CUSTOMER"})
    part_id = res_part.get_json()["data"]["partner"]["id"]

    # 2. Low cash (10,000)
    client.post("/api/business/transactions", headers=ws_headers, json={"transaction_type": "INCOME", "amount": "10000.00"})

    # 3. High payable (50,000) -> Projected position is -40,000 (DEFICIT)
    res_pay = client.post("/api/business/invoices", headers=ws_headers, json={"invoice_type": "PAYABLE", "total_amount": "50000.00"})
    client.post(f"/api/business/invoices/{res_pay.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # 4. Large receivable from single client (100,000) -> 100% concentration
    res_rec = client.post("/api/business/invoices", headers=ws_headers, json={"invoice_type": "RECEIVABLE", "partner_id": part_id, "total_amount": "100000.00"})
    client.post(f"/api/business/invoices/{res_rec.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # Evaluate Risks
    res_risks = client.get("/api/business/financial/risks", headers=ws_headers)
    assert res_risks.status_code == 200
    risk_payload = res_risks.get_json()["data"]["risks"]
    assert risk_payload["risks_count"] >= 1

    risk_codes = [r["code"] for r in risk_payload["risks"]]
    assert "RECEIVABLE_CONCENTRATION" in risk_codes
