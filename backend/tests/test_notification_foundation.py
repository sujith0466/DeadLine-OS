"""
DeadlineOS — Phase 4 Milestone 0 Unit Tests
=============================================
Tests Notification model lifecycle, NotificationRepository CRUD,
deduplication key idempotency, and status transitions.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.repository import NotificationRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m0"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m0@deadlineos.com",
            full_name="Notification M0 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_notification_creation_and_query(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        notif = Notification(
            id="notif-m0-1",
            user_id=test_user_id,
            notification_type=NotificationType.PRE_ALERT,
            title="Sprint Planning in 15 mins",
            description="Prepare your sprint board.",
            status=NotificationStatus.SCHEDULED,
            scheduled_at=now + timedelta(minutes=15),
            deduplication_key="PRE_ALERT:task-100:20260901",
            entity_type="TASK",
            entity_id="task-100"
        )
        NotificationRepository.save(notif)

        queried = NotificationRepository.get_by_id("notif-m0-1")
        assert queried is not None
        assert queried.title == "Sprint Planning in 15 mins"
        assert queried.status == NotificationStatus.SCHEDULED
        assert queried.notification_type == NotificationType.PRE_ALERT

        # Deduplication query
        dedup = NotificationRepository.get_by_deduplication_key(test_user_id, "PRE_ALERT:task-100:20260901")
        assert dedup is not None
        assert dedup.id == "notif-m0-1"


def test_notification_status_lifecycle(app, test_user_id):
    with app.app_context():
        notif = Notification(
            id="notif-m0-2",
            user_id=test_user_id,
            title="Focus Session Reminder",
            status=NotificationStatus.SCHEDULED,
            entity_id="task-200"
        )
        NotificationRepository.save(notif)

        # Transition to DELIVERED
        updated = NotificationRepository.update_status("notif-m0-2", NotificationStatus.DELIVERED)
        assert updated.status == NotificationStatus.DELIVERED
        assert updated.delivered_at is not None

        # Transition to ACKNOWLEDGED
        ack = NotificationRepository.update_status("notif-m0-2", NotificationStatus.ACKNOWLEDGED)
        assert ack.status == NotificationStatus.ACKNOWLEDGED
        assert ack.acknowledged_at is not None
        assert ack.read is True


def test_cancel_pending_notifications_for_entity(app, test_user_id):
    with app.app_context():
        n1 = Notification(
            id="notif-m0-3",
            user_id=test_user_id,
            title="Reminder 1",
            status=NotificationStatus.SCHEDULED,
            entity_id="task-300"
        )
        n2 = Notification(
            id="notif-m0-4",
            user_id=test_user_id,
            title="Delivered Alert",
            status=NotificationStatus.DELIVERED,
            entity_id="task-300"
        )
        NotificationRepository.save(n1)
        NotificationRepository.save(n2)

        cancelled_count = NotificationRepository.cancel_pending_for_entity(test_user_id, "task-300")
        assert cancelled_count == 1

        n1_fresh = NotificationRepository.get_by_id("notif-m0-3")
        n2_fresh = NotificationRepository.get_by_id("notif-m0-4")
        assert n1_fresh.status == NotificationStatus.CANCELLED
        assert n2_fresh.status == NotificationStatus.DELIVERED
