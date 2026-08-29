"""
B6 Test Suite — Recurring Obligations & Recurrence Math
=======================================================
Tests CRUD, calendar recurrence math, month-end clamping, and lifecycle state transitions.
"""

import uuid
from datetime import date
from services.business.recurring_obligation_service import RecurringObligationService


def test_recurring_obligation_crud_and_lifecycle(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Recurring Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Create monthly receivable obligation
    res_create = client.post("/api/business/recurring", headers=ws_headers, json={
        "title": "Monthly Retainer Contract",
        "obligation_type": "RECEIVABLE",
        "frequency": "MONTHLY",
        "amount": "75000.00",
        "start_date": "2026-09-01",
        "notes": "Client retainer"
    })
    assert res_create.status_code == 201
    obl = res_create.get_json()["data"]["obligation"]
    obl_id = obl["id"]
    assert obl["status"] == "ACTIVE"
    assert obl["next_due_date"] == "2026-09-01"

    # 2. Pause obligation
    res_pause = client.post(f"/api/business/recurring/{obl_id}/pause", headers=ws_headers)
    assert res_pause.status_code == 200
    assert res_pause.get_json()["data"]["obligation"]["status"] == "PAUSED"

    # 3. Resume obligation
    res_resume = client.post(f"/api/business/recurring/{obl_id}/resume", headers=ws_headers)
    assert res_resume.status_code == 200
    assert res_resume.get_json()["data"]["obligation"]["status"] == "ACTIVE"

    # 4. Cancel obligation
    res_cancel = client.post(f"/api/business/recurring/{obl_id}/cancel", headers=ws_headers)
    assert res_cancel.status_code == 200
    assert res_cancel.get_json()["data"]["obligation"]["status"] == "CANCELLED"


def test_month_end_clamping_and_frequencies():
    # Jan 31 -> Feb 28 (non-leap) or Feb 29
    d_jan31 = date(2026, 1, 31)
    next_feb = RecurringObligationService.calculate_next_due_date(d_jan31, 'MONTHLY')
    assert next_feb == date(2026, 2, 28)

    # Weekly: +7 days
    d_sep01 = date(2026, 9, 1)
    next_week = RecurringObligationService.calculate_next_due_date(d_sep01, 'WEEKLY')
    assert next_week == date(2026, 9, 8)

    # Quarterly: +3 months
    next_q = RecurringObligationService.calculate_next_due_date(d_sep01, 'QUARTERLY')
    assert next_q == date(2026, 12, 1)

    # Annually: +1 year
    next_yr = RecurringObligationService.calculate_next_due_date(d_sep01, 'ANNUALLY')
    assert next_yr == date(2027, 9, 1)
