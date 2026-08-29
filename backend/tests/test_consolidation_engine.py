"""
B7 Test Suite — Cross-Workspace Financial Consolidation Engine
==============================================================
Tests multi-workspace mathematical aggregation and inter-entity transfer elimination.
"""

import uuid
from decimal import Decimal


def test_multi_workspace_consolidation_and_elimination(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    # Workspace 1: Software Services
    res_ws1 = client.post("/api/business/workspaces", headers=headers, json={"name": "Holding Services Corp"})
    ws1_id = res_ws1.get_json()["data"]["workspace"]["id"]
    ws1_headers = {**headers, "X-Workspace-Id": ws1_id}

    # Workspace 2: Cloud Infrastructure
    res_ws2 = client.post("/api/business/workspaces", headers=headers, json={"name": "Holding Infra Corp"})
    ws2_id = res_ws2.get_json()["data"]["workspace"]["id"]
    ws2_headers = {**headers, "X-Workspace-Id": ws2_id}

    # Income transaction in WS1 (100,000)
    client.post("/api/business/transactions", headers=ws1_headers, json={
        "transaction_type": "INCOME",
        "amount": "100000.00",
        "transaction_date": "2026-08-29"
    })

    # Income transaction in WS2 (50,000)
    client.post("/api/business/transactions", headers=ws2_headers, json={
        "transaction_type": "INCOME",
        "amount": "50000.00",
        "transaction_date": "2026-08-29"
    })

    # Inter-entity transfer from WS1 to WS2 (20,000)
    res_trans = client.post("/api/business/transfers", headers=ws1_headers, json={
        "destination_workspace_id": ws2_id,
        "amount": "20000.00",
        "reference_note": "Internal software license"
    })
    assert res_trans.status_code == 201

    # Consolidated report across WS1 + WS2
    res_consol = client.post("/api/business/consolidation/overview", headers=headers, json={
        "workspace_ids": [ws1_id, ws2_id]
    })
    assert res_consol.status_code == 200
    overview = res_consol.get_json()["data"]["overview"]

    assert overview["workspaces_count"] == 2
    assert Decimal(overview["consolidated_revenue"]) == Decimal("150000.00")
    assert Decimal(overview["inter_entity_eliminations"]) == Decimal("20000.00")
