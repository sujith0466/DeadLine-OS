"""
DeadlineOS — Phase 4 Milestone 2 Unit Tests
=============================================
Tests ReminderService multi-offset reminders, deadline warnings, and cancellation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.reminder_service import ReminderService
from services.notifications.repository import NotificationRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m2"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m2@deadlineos.com",
            full_name="Notification M2 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_schedule_reminders_creation(app, test_user_id):
    with app.app_context():
        start_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        slot = ScheduleSlot(
            id="slot-rem-1",
            user_id=test_user_id,
            task_title="System Architecture Sync",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            status="PLANNED"
        )
        db.session.add(slot)
        db.session.commit()

        notifs = ReminderService.register_schedule_reminders(slot)
        # Default: 1 pre-alert (15m) + 1 reminder (5m) = 2 notifications
        assert len(notifs) == 2
        
        pre = next(n for n in notifs if n.notification_type == NotificationType.PRE_ALERT)
        pre_time = pre.scheduled_at.replace(tzinfo=timezone.utc) if pre.scheduled_at.tzinfo is None else pre.scheduled_at
        assert pre_time == start_time - timedelta(minutes=15)

        rem = next(n for n in notifs if n.notification_type == NotificationType.REMINDER)
        rem_time = rem.scheduled_at.replace(tzinfo=timezone.utc) if rem.scheduled_at.tzinfo is None else rem.scheduled_at
        assert rem_time == start_time - timedelta(minutes=5)


def test_task_deadline_reminders(app, test_user_id):
    with app.app_context():
        dl = datetime(2026, 9, 2, 17, 0, tzinfo=timezone.utc)
        task = Task(
            id="task-dl-test",
            user_id=test_user_id,
            title="Q3 Security Audit",
            deadline=dl,
            status="pending"
        )
        db.session.add(task)
        db.session.commit()

        notifs = ReminderService.register_deadline_reminders(task)
        # Default: 24h (1440m) and 2h (120m) = 2 alerts
        assert len(notifs) == 2
        
        # When task is done, pending reminders get cancelled
        ReminderService.on_activity_completed_or_cancelled(test_user_id, task.id)
        for n in notifs:
            fresh = NotificationRepository.get_by_id(n.id)
            assert fresh.status == NotificationStatus.CANCELLED
