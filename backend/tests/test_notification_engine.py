"""
DeadlineOS — Phase 4 Milestone 1 Unit Tests
=============================================
Tests NotificationEngine decision logic, idempotency, and schedule synchronization.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.notification_engine import NotificationEngine
from services.notifications.repository import NotificationRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m1"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m1@deadlineos.com",
            full_name="Notification M1 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_notification_engine_idempotent_creation(app, test_user_id):
    with app.app_context():
        scheduled_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

        # 1st creation
        n1 = NotificationEngine.schedule_notification(
            user_id=test_user_id,
            notification_type=NotificationType.PRE_ALERT,
            title="Design Review",
            description="In 15 minutes",
            scheduled_at=scheduled_time,
            entity_id="task-500"
        )
        assert n1 is not None

        # 2nd creation with exact same params — should return existing without duplicate
        n2 = NotificationEngine.schedule_notification(
            user_id=test_user_id,
            notification_type=NotificationType.PRE_ALERT,
            title="Design Review",
            description="In 15 minutes",
            scheduled_at=scheduled_time,
            entity_id="task-500"
        )
        assert n2.id == n1.id


def test_sync_schedule_slot_notifications(app, test_user_id):
    with app.app_context():
        slot_start = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)
        slot = ScheduleSlot(
            id="slot-sync-1",
            user_id=test_user_id,
            task_title="Deep Work Code Review",
            start_time=slot_start,
            end_time=slot_start + timedelta(hours=2),
            status="PLANNED"
        )
        db.session.add(slot)
        db.session.commit()

        notifs = NotificationEngine.sync_schedule_slot_notifications(
            slot=slot,
            pre_alert_minutes=15,
            reminder_minutes=5
        )

        assert len(notifs) == 2
        types = [n.notification_type for n in notifs]
        assert NotificationType.PRE_ALERT in types
        assert NotificationType.REMINDER in types

        # Reschedule slot to different time and re-sync
        slot.start_time = slot_start + timedelta(hours=2)
        slot.end_time = slot_start + timedelta(hours=4)
        db.session.commit()

        updated_notifs = NotificationEngine.sync_schedule_slot_notifications(
            slot=slot,
            pre_alert_minutes=15,
            reminder_minutes=5
        )
        assert len(updated_notifs) == 2
        
        # Verify old notifications were marked CANCELLED
        old_pre = NotificationRepository.get_by_id(notifs[0].id)
        assert old_pre.status == NotificationStatus.CANCELLED
