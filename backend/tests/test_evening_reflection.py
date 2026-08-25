"""
DeadlineOS — Phase 7 Milestone 2: Evening Reflection Tests
==========================================================
Tests evening reflection metrics, focus time aggregation, adherence math,
and GET /api/analytics/evening-reflection endpoint.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.recovery import RecoveryRecord, RecoveryActionType
from services.analytics.evening_reflection import EveningReflectionService


def test_evening_reflection_deterministic_metrics(app):
    user = User(
        id="test-user-er-1",
        email="er1@example.com",
        full_name="Evening Reflection User",
        timezone="UTC"
    )
    db.session.add(user)

    today_start = datetime(2026, 8, 25, 14, 0, tzinfo=timezone.utc)

    # 1. Completed slot
    slot1 = ScheduleSlot(
        id="slot-er-1",
        user_id="test-user-er-1",
        task_title="System Integration Testing",
        start_time=today_start,
        end_time=today_start + timedelta(hours=2),
        priority=90,
        status="COMPLETED"
    )
    # 2. Planned slot
    slot2 = ScheduleSlot(
        id="slot-er-2",
        user_id="test-user-er-1",
        task_title="Documentation Update",
        start_time=today_start + timedelta(hours=3),
        end_time=today_start + timedelta(hours=4),
        priority=60,
        status="PLANNED"
    )
    db.session.add_all([slot1, slot2])
    db.session.flush()

    # Runtime state & session
    state = RuntimeState(
        id="rs-er-1",
        user_id="test-user-er-1",
        entity_type="TASK",
        entity_id="slot-er-1",
        status="COMPLETED"
    )
    db.session.add(state)
    db.session.flush()

    session = RuntimeSession(
        id="sess-er-1",
        runtime_state_id="rs-er-1",
        started_at=today_start,
        ended_at=today_start + timedelta(minutes=100),
        planned_duration_sec=7200,
        paused_duration_sec=600,
        completion_source="Manual"
    )
    db.session.add(session)

    # Recovery record
    rec = RecoveryRecord(
        id="rec-er-1",
        user_id="test-user-er-1",
        action_type=RecoveryActionType.SKIP,
        entity_type="TASK",
        created_at=today_start + timedelta(hours=1)
    )
    db.session.add(rec)
    db.session.commit()

    reflection = EveningReflectionService.generate_evening_reflection("test-user-er-1", "2026-08-25")

    assert reflection["date"] == "2026-08-25"
    assert reflection["total_planned_activities"] == 2
    assert reflection["completed_activities_count"] == 1
    assert reflection["completion_rate_pct"] == 50.0
    assert reflection["skipped_activities_count"] == 1
    # 100m total - 10m pause = 90m focus
    assert reflection["total_focus_duration_minutes"] == 90.0
    assert reflection["total_paused_duration_minutes"] == 10.0
    assert reflection["schedule_adherence_pct"] > 0
    assert len(reflection["narrative_highlights"]) >= 3


def test_evening_reflection_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_er@example.com",
        full_name="API ER User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/evening-reflection?date=2026-08-25", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "schedule_adherence_pct" in data["data"]
