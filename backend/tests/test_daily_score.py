"""
DeadlineOS — Phase 7 Milestone 3: Daily Score Tests
===================================================
Tests deterministic daily score calculations, component weighting,
explainability, boundary bounds, and GET /api/analytics/daily-score endpoint.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from services.analytics.daily_score import DailyScoreService


def test_daily_score_calculation_bounds_and_components(app):
    user = User(
        id="test-user-ds-1",
        email="ds1@example.com",
        full_name="Daily Score User",
        timezone="UTC"
    )
    db.session.add(user)

    today_start = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)

    # 2 completed slots
    slot1 = ScheduleSlot(
        id="slot-ds-1",
        user_id="test-user-ds-1",
        task_title="Task A",
        start_time=today_start,
        end_time=today_start + timedelta(hours=2),
        priority=80,
        status="COMPLETED"
    )
    slot2 = ScheduleSlot(
        id="slot-ds-2",
        user_id="test-user-ds-1",
        task_title="Task B",
        start_time=today_start + timedelta(hours=2),
        end_time=today_start + timedelta(hours=4),
        priority=70,
        status="COMPLETED"
    )
    db.session.add_all([slot1, slot2])
    db.session.flush()

    # Runtime sessions (4 hours focus)
    state = RuntimeState(
        id="rs-ds-1",
        user_id="test-user-ds-1",
        entity_type="TASK",
        entity_id="slot-ds-1",
        status="COMPLETED"
    )
    db.session.add(state)
    db.session.flush()

    session = RuntimeSession(
        id="sess-ds-1",
        runtime_state_id="rs-ds-1",
        started_at=today_start,
        ended_at=today_start + timedelta(hours=4),
        planned_duration_sec=14400,
        paused_duration_sec=0,
        completion_source="Manual"
    )
    db.session.add(session)
    db.session.commit()

    score_data = DailyScoreService.calculate_daily_score("test-user-ds-1", "2026-08-25")

    assert score_data["score"] >= 90
    assert score_data["grade"] == "EXCELLENT"
    assert score_data["components"]["completion_rate"]["score"] == 100.0
    assert score_data["components"]["focus_depth"]["score"] == 100.0
    assert len(score_data["explanation"]) == 5


def test_daily_score_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_ds@example.com",
        full_name="API DS User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/daily-score?date=2026-08-25", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "score" in data["data"]
    assert "components" in data["data"]
