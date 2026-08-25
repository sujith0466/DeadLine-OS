"""
DeadlineOS — Phase 7 Milestone 7: Timeline Analytics Tests
==========================================================
Tests chronological event normalization, sorting, recovery inclusion,
and GET /api/analytics/timeline endpoint.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.recovery import RecoveryRecord, RecoveryActionType
from services.analytics.timeline import TimelineAnalyticsService


def test_timeline_normalization_and_ordering(app):
    user = User(
        id="test-user-tl-1",
        email="tl1@example.com",
        full_name="Timeline User",
        timezone="UTC"
    )
    db.session.add(user)

    t0 = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)

    # 1. Session start & end
    state = RuntimeState(
        id="rs-tl-1",
        user_id="test-user-tl-1",
        entity_type="TASK",
        entity_id="task-123",
        status="COMPLETED"
    )
    db.session.add(state)
    db.session.flush()

    session = RuntimeSession(
        id="sess-tl-1",
        runtime_state_id="rs-tl-1",
        started_at=t0,
        ended_at=t0 + timedelta(hours=1),
        planned_duration_sec=3600,
        paused_duration_sec=0,
        completion_source="Manual"
    )
    db.session.add(session)

    # 2. Recovery record at t0 + 2h
    rec = RecoveryRecord(
        id="rec-tl-1",
        user_id="test-user-tl-1",
        action_type=RecoveryActionType.DEFER,
        entity_type="TASK",
        created_at=t0 + timedelta(hours=2)
    )
    db.session.add(rec)
    db.session.commit()

    timeline = TimelineAnalyticsService.get_timeline("test-user-tl-1", start_date="2026-08-25", end_date="2026-08-25")

    assert timeline["total_events_count"] == 3  # Start, End, Recovery
    # Chronological check: latest event first (Recovery at t0+2h)
    assert timeline["events"][0]["event_type"] == "RECOVERY_DEFER"
    assert timeline["events"][1]["event_type"] == "SESSION_COMPLETED"
    assert timeline["events"][2]["event_type"] == "SESSION_STARTED"


def test_timeline_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_tl@example.com",
        full_name="API TL User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/timeline?limit=20", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "events" in data["data"]
