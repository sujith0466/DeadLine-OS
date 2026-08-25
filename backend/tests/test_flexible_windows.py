"""
DeadlineOS — Phase 3 Milestone 3 Unit Tests
=============================================
Tests deterministic slot placement within flexible scheduling windows.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from services.scheduling.flexible_window_engine import FlexibleWindowEngine


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m3"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_m3@deadlineos.com",
            full_name="Schedule M3 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_flexible_window_empty_schedule(app, test_user_id):
    with app.app_context():
        w_start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        w_end = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

        slot = FlexibleWindowEngine.find_best_slot(
            user_id=test_user_id,
            window_start=w_start,
            window_end=w_end,
            duration_minutes=60
        )

        assert slot is not None
        start, end = slot
        assert start == w_start
        assert end == w_start + timedelta(hours=1)


def test_flexible_window_with_existing_commitment(app, test_user_id):
    with app.app_context():
        w_start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        w_end = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

        # Existing commitment: 09:00 - 10:00
        existing = ScheduleSlot(
            id="slot-existing-1",
            user_id=test_user_id,
            task_title="Team Standup",
            start_time=w_start,
            end_time=w_start + timedelta(hours=1),
            status="PLANNED"
        )
        SchedulingRepository.save_slot(existing)

        # New activity: 60 minutes
        slot = FlexibleWindowEngine.find_best_slot(
            user_id=test_user_id,
            window_start=w_start,
            window_end=w_end,
            duration_minutes=60
        )

        assert slot is not None
        start, end = slot
        # Should be placed immediately after the standup at 10:00 - 11:00
        assert start == w_start + timedelta(hours=1)
        assert end == w_start + timedelta(hours=2)


def test_flexible_window_insufficient_space(app, test_user_id):
    with app.app_context():
        w_start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        w_end = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

        # Existing commitment occupies entire window
        existing = ScheduleSlot(
            id="slot-existing-2",
            user_id=test_user_id,
            task_title="Deep Work Block",
            start_time=w_start,
            end_time=w_end,
            status="PLANNED"
        )
        SchedulingRepository.save_slot(existing)

        # Try placing 60 min task
        slot = FlexibleWindowEngine.find_best_slot(
            user_id=test_user_id,
            window_start=w_start,
            window_end=w_end,
            duration_minutes=60
        )

        assert slot is None
