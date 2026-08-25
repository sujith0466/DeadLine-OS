"""
DeadlineOS — Phase 4 Milestone 5 Unit Tests
=============================================
Tests GroupingService clustering, group_id linkage, and severity inheritance.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.repository import NotificationRepository
from services.notifications.grouping_service import GroupingService


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m5"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m5@deadlineos.com",
            full_name="Notification M5 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_notification_grouping_clusters(app, test_user_id):
    with app.app_context():
        t0 = datetime.now(timezone.utc) + timedelta(minutes=30)

        # 3 notifications scheduled closely within 10 minutes
        n1 = Notification(
            id="notif-g-1",
            user_id=test_user_id,
            title="Task A Reminder",
            severity="info",
            scheduled_at=t0,
            status=NotificationStatus.SCHEDULED
        )
        n2 = Notification(
            id="notif-g-2",
            user_id=test_user_id,
            title="Task B Reminder",
            severity="high",
            scheduled_at=t0 + timedelta(minutes=5),
            status=NotificationStatus.SCHEDULED
        )
        n3 = Notification(
            id="notif-g-3",
            user_id=test_user_id,
            title="Habit C Reminder",
            severity="medium",
            scheduled_at=t0 + timedelta(minutes=10),
            status=NotificationStatus.SCHEDULED
        )
        NotificationRepository.save(n1)
        NotificationRepository.save(n2)
        NotificationRepository.save(n3)

        groups = GroupingService.group_pending_notifications(test_user_id, window_minutes=15)
        assert len(groups) == 1
        group = groups[0]

        assert "3 activities scheduled soon" in group.title
        assert group.severity == "high"  # Inherits highest severity from Task B
        assert group.group_id is not None

        # Verify child notifications received group_id
        child_n1 = NotificationRepository.get_by_id("notif-g-1")
        assert child_n1.group_id == group.group_id
