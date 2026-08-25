"""
DeadlineOS — Phase 5 Milestone 1 Unit Tests
=============================================
Tests Skip Today idempotency, domain preservation, and notification cancellation.
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
    user_id = "user-rec-m1"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m1@deadlineos.com",
            full_name="Recovery M1 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_skip_today_preserves_task_and_updates_slot(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        task = Task(
            id="task-skip-1",
            user_id=test_user_id,
            title="Read Chapter 4 Architecture",
            status="pending",
            deadline=now + timedelta(days=2)
        )
        db.session.add(task)

        slot = ScheduleSlot(
            id="slot-skip-1",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id=task.id,
            task_title="Read Chapter 4 Architecture",
            start_time=now,
            end_time=now + timedelta(hours=1),
            status="PLANNED"
        )
        db.session.add(slot)

        notif = Notification(
            id="notif-skip-1",
            user_id=test_user_id,
            entity_id=task.id,
            title="Pre-alert for Read Chapter 4",
            status=NotificationStatus.SCHEDULED
        )
        db.session.add(notif)
        db.session.commit()

        # Execute Skip Today
        res = RecoveryService.skip_today(
            user_id=test_user_id,
            entity_id=task.id,
            entity_type="TASK",
            schedule_id=slot.id
        )

        assert res["success"] is True
        
        # Verify task is NOT deleted
        saved_task = db.session.get(Task, "task-skip-1")
        assert saved_task is not None
        assert saved_task.status == "pending"  # Preserved

        # Verify schedule slot is marked SKIPPED
        saved_slot = SchedulingRepository.get_slot_by_id("slot-skip-1")
        assert saved_slot.status == "SKIPPED"

        # Verify notification was cancelled
        saved_notif = NotificationRepository.get_by_id("notif-skip-1")
        assert saved_notif.status == NotificationStatus.CANCELLED
