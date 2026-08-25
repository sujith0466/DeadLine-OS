"""
DeadlineOS — Phase 4 Milestone 6 Unit Tests
=============================================
Tests ActionRouter and notifications API action endpoints.
"""

import pytest
from datetime import datetime, timezone
from database.db import db
from models.user import User
from models.task import Task
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.repository import NotificationRepository
from services.notifications.action_router import ActionRouter


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m6"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m6@deadlineos.com",
            full_name="Notification M6 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_action_router_start_activity(app, test_user_id):
    with app.app_context():
        task = Task(
            id="task-act-1",
            user_id=test_user_id,
            title="Backend Profiling",
            deadline=datetime.now(timezone.utc),
            status="pending"
        )
        db.session.add(task)
        db.session.commit()

        notif = Notification(
            id="notif-act-1",
            user_id=test_user_id,
            notification_type=NotificationType.REMINDER,
            title="Time for Backend Profiling",
            entity_type="TASK",
            entity_id=task.id,
            status=NotificationStatus.DELIVERED
        )
        NotificationRepository.save(notif)

        # Trigger START_ACTIVITY action
        res = ActionRouter.handle_action(
            user_id=test_user_id,
            notification_id="notif-act-1",
            action_type="START_ACTIVITY"
        )

        assert res["success"] is True
        assert res["result"]["status"] == "STARTED"
        assert res["notification"]["status"] == NotificationStatus.ACKNOWLEDGED


def test_action_router_dismiss(app, test_user_id):
    with app.app_context():
        notif = Notification(
            id="notif-act-2",
            user_id=test_user_id,
            title="Optional Webinar Reminder",
            status=NotificationStatus.DELIVERED
        )
        NotificationRepository.save(notif)

        res = ActionRouter.handle_action(
            user_id=test_user_id,
            notification_id="notif-act-2",
            action_type="DISMISS"
        )

        assert res["success"] is True
        assert res["result"]["status"] == "DISMISSED"
        assert res["notification"]["status"] == NotificationStatus.DISMISSED
