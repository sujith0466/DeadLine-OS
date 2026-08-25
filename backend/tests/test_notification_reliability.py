"""
DeadlineOS — Phase 4 Milestone 10 Unit Tests
==============================================
Tests DeliveryService delivery success, idempotency, retry backoff, and max retries failure.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.delivery_service import DeliveryService
from services.notifications.repository import NotificationRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m10"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m10@deadlineos.com",
            full_name="Notification M10 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_delivery_success_and_idempotency(app, test_user_id):
    with app.app_context():
        notif = Notification(
            id="notif-rel-1",
            user_id=test_user_id,
            title="Scheduled Standup",
            status=NotificationStatus.SCHEDULED,
            scheduled_at=datetime.now(timezone.utc)
        )
        NotificationRepository.save(notif)

        # 1. Deliver successfully
        res = DeliveryService.deliver_notification("notif-rel-1")
        assert res["success"] is True
        assert res["status"] == NotificationStatus.DELIVERED

        # 2. Re-delivering is idempotent no-op
        res2 = DeliveryService.deliver_notification("notif-rel-1")
        assert res2["success"] is True
        assert res2["status"] == NotificationStatus.DELIVERED


def test_delivery_retry_and_deadletter_failure(app, test_user_id):
    with app.app_context():
        notif = Notification(
            id="notif-rel-2",
            user_id=test_user_id,
            title="External Webhook Alert",
            status=NotificationStatus.SCHEDULED,
            retry_count=0
        )
        NotificationRepository.save(notif)

        def failing_sender(n):
            raise ConnectionError("Network unreachable")

        # Attempt 1 -> Retry 1
        r1 = DeliveryService.deliver_notification("notif-rel-2", sender_callable=failing_sender)
        assert r1["success"] is False
        assert r1["retry_count"] == 1
        assert r1["status"] == NotificationStatus.SCHEDULED

        # Attempt 2 -> Retry 2
        r2 = DeliveryService.deliver_notification("notif-rel-2", sender_callable=failing_sender)
        assert r2["retry_count"] == 2

        # Attempt 3 -> Retry 3 -> Marked FAILED
        r3 = DeliveryService.deliver_notification("notif-rel-2", sender_callable=failing_sender)
        assert r3["success"] is False
        assert r3["status"] == NotificationStatus.FAILED

        fresh = NotificationRepository.get_by_id("notif-rel-2")
        assert fresh.status == NotificationStatus.FAILED
