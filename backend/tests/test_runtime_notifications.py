"""
DeadlineOS — Phase 4 Milestone 3 Unit Tests
=============================================
Tests RuntimeNotificationListener response to Runtime Event Bus signals.
"""

import pytest
from datetime import datetime, timezone
from database.db import db
from models.user import User
from models.notification import Notification, NotificationType
from services.notifications.repository import NotificationRepository
import services.notifications.runtime_listener  # ensure signals are connected
from services.runtime.event_bus import activity_started, activity_completed, activity_interrupted


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m3"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m3@deadlineos.com",
            full_name="Notification M3 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_runtime_started_signal_emits_notification(app, test_user_id):
    with app.app_context():
        activity_started.send(
            None,
            payload={
                "user_id": test_user_id,
                "entity_id": "task-rt-101",
                "entity_type": "TASK",
                "title": "Database Optimization"
            }
        )

        notifs = NotificationRepository.get_user_notifications(test_user_id)
        assert len(notifs) >= 1
        started_notif = next((n for n in notifs if n.entity_id == "task-rt-101"), None)
        assert started_notif is not None
        assert "Session Started: Database Optimization" in started_notif.title
        assert started_notif.notification_type == NotificationType.RUNNING_SESSION


def test_runtime_interrupted_signal_emits_checkin(app, test_user_id):
    with app.app_context():
        activity_interrupted.send(
            None,
            payload={
                "user_id": test_user_id,
                "entity_id": "task-rt-102",
                "entity_type": "TASK",
                "title": "API Refactoring"
            }
        )

        notifs = NotificationRepository.get_user_notifications(test_user_id)
        int_notif = next((n for n in notifs if n.entity_id == "task-rt-102"), None)
        assert int_notif is not None
        assert int_notif.notification_type == NotificationType.CHECKIN
        assert int_notif.requires_confirmation is True
