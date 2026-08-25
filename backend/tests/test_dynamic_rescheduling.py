"""
DeadlineOS — Phase 3 Milestone 6 Unit Tests
=============================================
Tests safe rescheduling, conflict prevention, before/after auditing,
and cascade shifts without touching runtime history.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from services.scheduling.rescheduling_engine import ReschedulingEngine


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m6"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_m6@deadlineos.com",
            full_name="Schedule M6 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_reschedule_slot_clean_move(app, test_user_id):
    with app.app_context():
        t1 = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        slot = ScheduleSlot(
            id="slot-resched-1",
            user_id=test_user_id,
            task_title="Morning Sprint",
            start_time=t1,
            end_time=t1 + timedelta(hours=1),
            status="PLANNED"
        )
        SchedulingRepository.save_slot(slot)

        # Reschedule to 14:00
        new_start = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)
        res = ReschedulingEngine.reschedule_slot(
            user_id=test_user_id,
            slot_id="slot-resched-1",
            new_start_time=new_start
        )

        assert res["success"] is True
        assert res["before"]["start_time_utc"] == t1.isoformat()
        assert res["after"]["start_time_utc"] == new_start.isoformat()
        assert res["after"]["status"] == "RESCHEDULED"


def test_reschedule_slot_conflict_rejection(app, test_user_id):
    with app.app_context():
        t1 = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 1, 11, 0, tzinfo=timezone.utc)

        slot1 = ScheduleSlot(
            id="slot-r-1",
            user_id=test_user_id,
            task_title="Task 1",
            start_time=t1,
            end_time=t1 + timedelta(hours=1),
            status="PLANNED"
        )
        slot2 = ScheduleSlot(
            id="slot-r-2",
            user_id=test_user_id,
            task_title="Task 2 (Blocking)",
            start_time=t2,
            end_time=t2 + timedelta(hours=1),
            status="PLANNED"
        )
        SchedulingRepository.save_slot(slot1)
        SchedulingRepository.save_slot(slot2)

        # Attempt to move Task 1 to collide with Task 2 without force_cascade
        res = ReschedulingEngine.reschedule_slot(
            user_id=test_user_id,
            slot_id="slot-r-1",
            new_start_time=t2,
            force_cascade=False
        )

        assert res["success"] is False
        assert res["error"] == "CONFLICT_DETECTED"
        assert res["conflict_report"]["has_conflict"] is True


def test_reschedule_slot_with_cascade(app, test_user_id):
    with app.app_context():
        t1 = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 1, 11, 0, tzinfo=timezone.utc)

        slot1 = ScheduleSlot(
            id="slot-c-1",
            user_id=test_user_id,
            task_title="Task 1",
            start_time=t1,
            end_time=t1 + timedelta(hours=1),
            status="PLANNED"
        )
        slot2 = ScheduleSlot(
            id="slot-c-2",
            user_id=test_user_id,
            task_title="Task 2 (Will Shift)",
            start_time=t2,
            end_time=t2 + timedelta(hours=1),
            status="PLANNED"
        )
        SchedulingRepository.save_slot(slot1)
        SchedulingRepository.save_slot(slot2)

        # Move Task 1 to 11:00 with force_cascade=True
        res = ReschedulingEngine.reschedule_slot(
            user_id=test_user_id,
            slot_id="slot-c-1",
            new_start_time=t2,
            force_cascade=True
        )

        assert res["success"] is True
        assert len(res["cascaded_shifts"]) == 1
        assert res["cascaded_shifts"][0]["slot_id"] == "slot-c-2"

        # Verify slot2 was shifted after slot1
        shifted_slot2 = SchedulingRepository.get_slot_by_id("slot-c-2")
        shifted_start = shifted_slot2.start_time.replace(tzinfo=timezone.utc) if shifted_slot2.start_time.tzinfo is None else shifted_slot2.start_time
        assert shifted_start >= (t2 + timedelta(hours=1))
