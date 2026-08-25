"""
DeadlineOS — Phase 7 Milestone 8: Session Analytics Tests
=========================================================
Tests runtime session duration aggregations, pause ratios, distribution math,
and GET /api/analytics/sessions endpoint.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from services.analytics.session_analytics import SessionAnalyticsService


def test_session_analytics_math(app):
    user = User(
        id="test-user-sa-1",
        email="sa1@example.com",
        full_name="Session Analytics User",
        timezone="UTC"
    )
    db.session.add(user)

    t0 = datetime.now(timezone.utc) - timedelta(days=2)

    # 2 sessions: 1 Task, 1 Habit
    state1 = RuntimeState(
        id="rs-sa-1",
        user_id="test-user-sa-1",
        entity_type="TASK",
        entity_id="task-1",
        status="COMPLETED"
    )
    state2 = RuntimeState(
        id="rs-sa-2",
        user_id="test-user-sa-1",
        entity_type="HABIT",
        entity_id="habit-1",
        status="COMPLETED"
    )
    db.session.add_all([state1, state2])
    db.session.flush()

    # Session 1: 60m focus, 0 pause
    s1 = RuntimeSession(
        id="sess-sa-1",
        runtime_state_id="rs-sa-1",
        started_at=t0,
        ended_at=t0 + timedelta(hours=1),
        planned_duration_sec=3600,
        paused_duration_sec=0,
        completion_source="Manual"
    )
    # Session 2: 45m gross, 15m pause (30m focus)
    s2 = RuntimeSession(
        id="sess-sa-2",
        runtime_state_id="rs-sa-2",
        started_at=t0 + timedelta(hours=2),
        ended_at=t0 + timedelta(hours=2, minutes=45),
        planned_duration_sec=1800,
        paused_duration_sec=900,
        completion_source="Manual"
    )
    db.session.add_all([s1, s2])
    db.session.commit()

    analytics = SessionAnalyticsService.get_session_analytics("test-user-sa-1", days=7)

    assert analytics["total_sessions"] == 2
    # 60m + 30m = 90m focus (1.5 hours)
    assert analytics["total_focus_hours"] == 1.5
    assert analytics["total_paused_minutes"] == 15.0
    assert analytics["avg_session_minutes"] == 45.0
    assert analytics["entity_distribution"]["TASK"] == 1
    assert analytics["entity_distribution"]["HABIT"] == 1


def test_session_analytics_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_sa@example.com",
        full_name="API SA User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/sessions?days=14", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "total_sessions" in data["data"]
