"""
DeadlineOS — Phase 3 Milestone 0 Unit Tests
=============================================
Tests SchedulingRepository, RecurrenceRule, and enhanced ScheduleSlot models.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import Schedule, ScheduleSlot
from models.recurrence_rule import RecurrenceRule
from services.scheduling.repository import SchedulingRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m0"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_test@deadlineos.com",
            full_name="Schedule Test User",
            timezone="America/New_York"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_schedule_slot_creation_and_query(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        slot = ScheduleSlot(
            id="slot-m0-1",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id="task-123",
            task_title="Complete Phase 3 M0",
            start_time=now,
            end_time=now + timedelta(hours=2),
            window_start=now - timedelta(hours=1),
            window_end=now + timedelta(hours=4),
            priority=85,
            status="PLANNED",
            focus_block=True
        )
        SchedulingRepository.save_slot(slot)

        queried = SchedulingRepository.get_slot_by_id("slot-m0-1")
        assert queried is not None
        assert queried.task_title == "Complete Phase 3 M0"
        assert queried.priority == 85
        assert queried.focus_block is True
        assert queried.status == "PLANNED"

        # Test time-range query
        slots = SchedulingRepository.get_slots_by_user(
            user_id=test_user_id,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=3)
        )
        assert len(slots) == 1
        assert slots[0].id == "slot-m0-1"

        # Test serialization
        data = queried.to_dict()
        assert data["entity_type"] == "TASK"
        assert data["entity_id"] == "task-123"
        assert data["priority"] == 85
        assert "start_time_utc" in data


def test_recurrence_rule_creation(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        rule = RecurrenceRule(
            id="rule-m0-1",
            user_id=test_user_id,
            frequency="WEEKLY",
            interval=1,
            by_weekdays="MO,WE,FR",
            start_date=now,
            end_date=now + timedelta(days=30),
            occurrence_count=12
        )
        SchedulingRepository.save_recurrence_rule(rule)

        queried = SchedulingRepository.get_recurrence_rule("rule-m0-1")
        assert queried is not None
        assert queried.frequency == "WEEKLY"
        assert queried.interval == 1
        assert "MO" in queried.by_weekdays

        d = queried.to_dict()
        assert d["by_weekdays"] == ["MO", "WE", "FR"]
        assert d["occurrence_count"] == 12
