"""
DeadlineOS — Phase 5 Milestone 2 Unit Tests
=============================================
Tests Activity Pause, Activity Resume, slot status transitions, and notification handling.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from models.notification import Notification, NotificationStatus
from services.scheduling.repository import SchedulingRepository
from services.notifications.repository import NotificationRepository
from services.recovery.service import RecoveryService


@pytest.fixture
def test_user_id(app):
    user_id = "user-rec-m2"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m2@deadlineos.com",
            full_name="Recovery M2 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_pause_and_resume_activity_lifecycle(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        task = Task(
            id="task-pause-1",
            user_id=test_user_id,
            title="Design System Architecture Diagram",
            status="pending",
            deadline=now + timedelta(days=2)
        )
        db.session.add(task)

        slot = ScheduleSlot(
            id="slot-pause-1",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id=task.id,
            task_title="Design System Architecture Diagram",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
            status="PLANNED"
        )
        db.session.add(slot)

        notif = Notification(
            id="notif-pause-1",
            user_id=test_user_id,
            entity_id=task.id,
            title="Pre-alert for Architecture",
            status=NotificationStatus.SCHEDULED
        )
        db.session.add(notif)
        db.session.commit()

        # 1. Pause activity
        pause_res = RecoveryService.pause_activity(
            user_id=test_user_id,
            entity_id=task.id,
            entity_type="TASK",
            reason="Blocked by dependency"
        )
        assert pause_res["success"] is True
        assert pause_res["paused_slots_count"] == 1

        # Verify slot is PAUSED
        saved_slot = SchedulingRepository.get_slot_by_id("slot-pause-1")
        assert saved_slot.status == "PAUSED"

        # Verify notification cancelled
        saved_notif = NotificationRepository.get_by_id("notif-pause-1")
        assert saved_notif.status == NotificationStatus.CANCELLED

        # 2. Resume activity
        resume_res = RecoveryService.resume_activity(
            user_id=test_user_id,
            entity_id=task.id,
            entity_type="TASK"
        )
        assert resume_res["success"] is True
        assert resume_res["resumed_slots_count"] == 1

        # Verify slot restored to PLANNED
        saved_slot_resumed = SchedulingRepository.get_slot_by_id("slot-pause-1")
        assert saved_slot_resumed.status == "PLANNED"
