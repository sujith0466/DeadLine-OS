"""
DeadlineOS — Phase 7 Milestone 1: Morning Brief Tests
=====================================================
Tests morning brief generation, priority sorting, overdue detection,
active session inclusion, and API endpoint integration.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from services.analytics.morning_brief import MorningBriefService


def test_morning_brief_deterministic_generation(app):
    user = User(
        id="test-user-mb-1",
        email="mb1@example.com",
        full_name="Morning Brief User",
        timezone="UTC"
    )
    db.session.add(user)

    # Add planned schedule slot for today
    today_start = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
    slot = ScheduleSlot(
        id="slot-mb-1",
        user_id="test-user-mb-1",
        task_title="Review Architecture Document",
        start_time=today_start,
        end_time=today_start + timedelta(hours=1),
        priority=85,
        status="PLANNED"
    )
    db.session.add(slot)

    # Add overdue task
    overdue_task = Task(
        id="task-mb-od",
        user_id="test-user-mb-1",
        title="Overdue Client Report",
        deadline=datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc),
        status="pending",
        estimated_hours=1.5
    )
    db.session.add(overdue_task)

    # Add active interrupted session
    state = RuntimeState(
        id="rs-mb-1",
        user_id="test-user-mb-1",
        entity_type="TASK",
        entity_id="task-mb-od",
        status="INTERRUPTED"
    )
    db.session.add(state)
    db.session.commit()

    brief = MorningBriefService.generate_morning_brief("test-user-mb-1", "2026-08-25")

    assert brief["date"] == "2026-08-25"
    assert brief["planned_activities_count"] == 1
    assert brief["high_priority_count"] == 1
    assert brief["overdue_tasks_count"] == 1
    assert len(brief["active_interrupted_sessions"]) == 1
    assert brief["active_interrupted_sessions"][0]["status"] == "INTERRUPTED"
    assert len(brief["risk_indicators"]) >= 2
    assert "is_ai_generated" in brief and brief["is_ai_generated"] is False


def test_morning_brief_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_mb@example.com",
        full_name="API MB User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/morning-brief?date=2026-08-25", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "planned_activities_count" in data["data"]
    assert data["data"]["date"] == "2026-08-25"
