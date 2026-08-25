"""
DeadlineOS — Phase 7 Milestone 0 Tests
======================================
Tests Analytics Foundation timezone window calculations and read-only repository aggregations.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.schedule import ScheduleSlot
from models.recovery import RecoveryRecord, RecoveryActionType
from models.task import Task
from services.analytics.foundation import AnalyticsTimeWindow
from services.analytics.repository import AnalyticsRepository


def test_analytics_time_window_day_boundaries(app):
    user = User(
        id="test-user-p7-tz",
        email="p7tz@example.com",
        full_name="P7 User",
        timezone="Asia/Kolkata"
    )
    db.session.add(user)
    db.session.commit()

    start_utc, end_utc, date_str = AnalyticsTimeWindow.get_day_boundaries_utc("test-user-p7-tz", "2026-08-25")

    assert date_str == "2026-08-25"
    assert start_utc.tzinfo is not None
    assert end_utc.tzinfo is not None
    assert start_utc < end_utc
    # 2026-08-25 00:00:00 IST is 2026-08-24 18:30:00 UTC
    assert start_utc.year == 2026
    assert start_utc.month == 8
    assert start_utc.day == 24
    assert start_utc.hour == 18
    assert start_utc.minute == 30


def test_analytics_repository_read_only_queries(app):
    user = User(
        id="test-user-p7-repo",
        email="p7repo@example.com",
        full_name="P7 Repo User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    # Seed Task
    task = Task(
        id="t-p7-1",
        user_id="test-user-p7-repo",
        title="P7 Foundation Task",
        deadline=datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc),
        status="done",
        estimated_hours=2.0,
        actual_hours=2.0
    )
    db.session.add(task)

    # Seed RuntimeState & Session
    state = RuntimeState(
        id="rs-p7-1",
        user_id="test-user-p7-repo",
        entity_type="TASK",
        entity_id="t-p7-1",
        status="COMPLETED"
    )
    db.session.add(state)
    db.session.flush()

    session = RuntimeSession(
        id="sess-p7-1",
        runtime_state_id="rs-p7-1",
        started_at=datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 8, 25, 10, 30, tzinfo=timezone.utc),
        planned_duration_sec=3600,
        paused_duration_sec=300,
        completion_source="Manual"
    )
    db.session.add(session)

    # Seed Recovery Record
    recovery = RecoveryRecord(
        id="rec-p7-1",
        user_id="test-user-p7-repo",
        action_type=RecoveryActionType.RESCHEDULE,
        entity_type="TASK",
        entity_id="t-p7-1",
        created_at=datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
    )
    db.session.add(recovery)
    db.session.commit()

    start_utc = datetime(2026, 8, 25, 0, 0, tzinfo=timezone.utc)
    end_utc = datetime(2026, 8, 25, 23, 59, tzinfo=timezone.utc)

    # 1. Sessions query
    sessions = AnalyticsRepository.get_sessions("test-user-p7-repo", start_utc, end_utc)
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "sess-p7-1"
    assert sessions[0]["paused_duration_sec"] == 300
    assert sessions[0]["actual_duration_sec"] == 5100  # 90m total (5400s) - 300s paused = 5100s

    # 2. Recovery query
    recoveries = AnalyticsRepository.get_recovery_records("test-user-p7-repo", start_utc, end_utc)
    assert len(recoveries) == 1
    assert recoveries[0]["action_type"] == RecoveryActionType.RESCHEDULE

    # 3. Tasks overview
    tasks_stat = AnalyticsRepository.get_tasks_overview("test-user-p7-repo")
    assert tasks_stat["total_tasks"] == 1
    assert tasks_stat["completed_tasks"] == 1
    assert tasks_stat["completion_rate_pct"] == 100.0
