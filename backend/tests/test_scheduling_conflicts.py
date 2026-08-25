"""
DeadlineOS — Phase 3 Milestone 4 Unit Tests
=============================================
Tests deterministic conflict detection for time overlaps, invalid durations,
and window bounds.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from services.scheduling.conflict_service import ConflictDetectionService


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m4"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_m4@deadlineos.com",
            full_name="Schedule M4 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_conflict_detection_no_overlap(app, test_user_id):
    with app.app_context():
        t1 = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        slot1 = ScheduleSlot(
            id="slot-c-1",
            user_id=test_user_id,
            task_title="Focus Block 1",
            start_time=t1,
            end_time=t1 + timedelta(hours=1),
            status="PLANNED"
        )
        SchedulingRepository.save_slot(slot1)

        # Proposed slot is completely after slot1 (10:00 - 11:00)
        report = ConflictDetectionService.check_conflicts(
            user_id=test_user_id,
            start_time=t1 + timedelta(hours=1),
            end_time=t1 + timedelta(hours=2),
            allow_past=True
        )

        assert report["has_conflict"] is False
        assert report["conflict_count"] == 0


def test_conflict_detection_time_overlap(app, test_user_id):
    with app.app_context():
        t1 = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        slot1 = ScheduleSlot(
            id="slot-c-2",
            user_id=test_user_id,
            task_title="Client Meeting",
            start_time=t1,
            end_time=t1 + timedelta(hours=2),
            status="PLANNED"
        )
        SchedulingRepository.save_slot(slot1)

        # Proposed slot overlaps: 10:00 - 11:00
        report = ConflictDetectionService.check_conflicts(
            user_id=test_user_id,
            start_time=t1 + timedelta(hours=1),
            end_time=t1 + timedelta(hours=2),
            allow_past=True
        )

        assert report["has_conflict"] is True
        assert report["conflict_count"] == 1
        assert report["conflicts"][0]["reason"] == "TIME_OVERLAP"
        assert report["conflicts"][0]["slot_id"] == "slot-c-2"


def test_conflict_detection_invalid_duration(app, test_user_id):
    with app.app_context():
        t1 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        
        # End time before start time
        report = ConflictDetectionService.check_conflicts(
            user_id=test_user_id,
            start_time=t1,
            end_time=t1 - timedelta(hours=1),
            allow_past=True
        )

        assert report["has_conflict"] is True
        assert any(c["reason"] == "INVALID_DURATION" for c in report["conflicts"])
