"""
B3 Test Suite — Cash Truth & Deterministic Runway
=================================================
Tests 4-tier Cash Reality hierarchy and 5-tier deterministic Runway Days precedence.
"""

import uuid


def test_cash_position_and_runway_calculation(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Runway Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Record 1,00,000 confirmed cash
    client.post("/api/business/transactions", headers=ws_headers, json={"transaction_type": "INCOME", "amount": "100000.00"})

    # 2. Record 20,000 expense
    client.post("/api/business/transactions", headers=ws_headers, json={"transaction_type": "EXPENSE", "amount": "20000.00"})

    # 3. Create issued receivable of 50,000
    res_rec = client.post("/api/business/invoices", headers=ws_headers, json={"invoice_type": "RECEIVABLE", "total_amount": "50000.00"})
    client.post(f"/api/business/invoices/{res_rec.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # 4. Create issued payable of 10,000
    res_pay = client.post("/api/business/invoices", headers=ws_headers, json={"invoice_type": "PAYABLE", "total_amount": "10000.00"})
    client.post(f"/api/business/invoices/{res_pay.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # Check Cash Position
    res_pos = client.get("/api/business/financial/cash-position", headers=ws_headers)
    assert res_pos.status_code == 200
    pos = res_pos.get_json()["data"]["cash_position"]
    assert pos["confirmed_cash"] == "80000.00"        # 100k - 20k
    assert pos["committed_inflows"] == "50000.00"
    assert pos["committed_outflows"] == "10000.00"
    assert pos["projected_position"] == "120000.00"   # 80k + 50k - 10k

    # Check Runway Days: ADBR_30 = (20000 expenses + 10000 payables) / 60 = 500/day
    # Runway Days = floor(80000 / 500) = 160 days
    res_runway = client.get("/api/business/financial/runway", headers=ws_headers)
    assert res_runway.status_code == 200
    rw = res_runway.get_json()["data"]["runway"]
    assert rw["state"] == "CALCULATED"
    assert rw["runway_days"] == 160
    assert rw["confirmed_cash"] == "80000.00"
