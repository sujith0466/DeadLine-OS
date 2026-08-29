"""
B4 Test Suite — Business Copilot & Grounded Context
===================================================
Tests zero-bypass context assembly, grounded financial Q&A, and action proposals.
"""

import uuid


def test_copilot_query_with_grounded_financial_context(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Copilot Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Set up financial state: 100,000 cash, 50,000 receivable
    client.post("/api/business/transactions", headers=ws_headers, json={"transaction_type": "INCOME", "amount": "100000.00"})
    res_inv = client.post("/api/business/invoices", headers=ws_headers, json={"invoice_type": "RECEIVABLE", "total_amount": "50000.00"})
    client.post(f"/api/business/invoices/{res_inv.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # 2. Query Copilot
    res_query = client.post(
        "/api/business/copilot/query",
        headers=ws_headers,
        json={"prompt": "What is our current cash reality and who owes us money?"}
    )
    assert res_query.status_code == 200
    data = res_query.get_json()["data"]
    assert "query" in data
    assert "response" in data
    assert "context_summary" in data
    assert data["context_summary"]["confirmed_cash"] == "100000.00"


def test_copilot_empty_prompt_rejected(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Copilot Reject Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    res_bad = client.post("/api/business/copilot/query", headers=ws_headers, json={"prompt": "   "})
    assert res_bad.status_code == 400
    assert res_bad.get_json()["error"]["code"] == "EMPTY_PROMPT"
