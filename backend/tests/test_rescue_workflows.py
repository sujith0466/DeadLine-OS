"""
B5 Test Suite — Rescue & Overdue Aging Engine
=============================================
Tests deterministic aging buckets, priority scoring, and invoice filtering.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal


def test_overdue_aging_buckets_and_priority_ranking(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Rescue Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    today = date.today()

    # Invoice 1: 15 days overdue (Bucket 1) - 10,000
    res_inv1 = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "10000.00",
        "due_date": (today - timedelta(days=15)).isoformat()
    })
    client.post(f"/api/business/invoices/{res_inv1.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # Invoice 2: 45 days overdue (Bucket 2) - 20,000
    res_inv2 = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "20000.00",
        "due_date": (today - timedelta(days=45)).isoformat()
    })
    client.post(f"/api/business/invoices/{res_inv2.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # Invoice 3: 75 days overdue (Bucket 3) - 30,000
    res_inv3 = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "30000.00",
        "due_date": (today - timedelta(days=75)).isoformat()
    })
    client.post(f"/api/business/invoices/{res_inv3.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # Invoice 4: 100 days overdue (Bucket 4) - 40,000
    res_inv4 = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "40000.00",
        "due_date": (today - timedelta(days=100)).isoformat()
    })
    client.post(f"/api/business/invoices/{res_inv4.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # Invoice 5: Future due date (0 days overdue) - Must be excluded from aging
    res_inv5 = client.post("/api/business/invoices", headers=ws_headers, json={
        "invoice_type": "RECEIVABLE",
        "total_amount": "5000.00",
        "due_date": (today + timedelta(days=10)).isoformat()
    })
    client.post(f"/api/business/invoices/{res_inv5.get_json()['data']['invoice']['id']}/issue", headers=ws_headers)

    # 1. Verify Aging Summary
    res_aging = client.get("/api/business/rescue/aging", headers=ws_headers)
    assert res_aging.status_code == 200
    aging_data = res_aging.get_json()["data"]

    assert aging_data["total_overdue_count"] == 4
    assert Decimal(aging_data["total_overdue_amount"]) == Decimal("100000.00")
    assert aging_data["buckets"]["1_to_30_days"]["count"] == 1
    assert aging_data["buckets"]["31_to_60_days"]["count"] == 1
    assert aging_data["buckets"]["61_to_90_days"]["count"] == 1
    assert aging_data["buckets"]["90_plus_days"]["count"] == 1

    # 2. Verify Priorities
    res_prio = client.get("/api/business/rescue/priorities", headers=ws_headers)
    assert res_prio.status_code == 200
    prios = res_prio.get_json()["data"]["priorities"]
    assert len(prios) == 4

    # Top priority must be invoice 4 (100 days overdue, 40,000 balance -> highest score)
    assert prios[0]["invoice_id"] == res_inv4.get_json()["data"]["invoice"]["id"]
    assert prios[0]["recommended_tone"] == "LEGAL"
