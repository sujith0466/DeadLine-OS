"""
DeadlineOS — Phase 4 Milestone 7 Unit Tests
=============================================
Tests CheckInService detection of unstarted slots and confirmation payload generation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.notification import Notification, NotificationType
from services.notifications.checkin_service import CheckInService
from services.notifications.repository import NotificationRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m7"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m7@deadlineos.com",
            full_name="Notification M7 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_checkin_triggered_for_overdue_unstarted_activity(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        # Slot started 15 minutes ago, ends in 45 minutes
        slot = ScheduleSlot(
            id="slot-chk-1",
            user_id=test_user_id,
            task_title="Morning Sprint Review",
            start_time=now - timedelta(minutes=15),
            end_time=now + timedelta(minutes=45),
            status="PLANNED"
        )
        db.session.add(slot)
        db.session.commit()

        checkins = CheckInService.evaluate_unstarted_activities(test_user_id, grace_minutes=10)
        assert len(checkins) == 1
        c = checkins[0]
        assert c.notification_type == NotificationType.CHECKIN
        assert "Morning Sprint Review" in c.title
        assert c.requires_confirmation is True
        assert c.confirmation_action is not None


def test_checkin_ignored_if_already_running(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        slot = ScheduleSlot(
            id="slot-chk-2",
            user_id=test_user_id,
            entity_id="task-running-99",
            task_title="Live Coding Session",
            start_time=now - timedelta(minutes=15),
            end_time=now + timedelta(minutes=45),
            status="PLANNED"
        )
        db.session.add(slot)

        # Set active RuntimeState for this entity
        rt = RuntimeState(
            id="rt-state-chk-2",
            user_id=test_user_id,
            entity_id="task-running-99",
            entity_type="TASK",
            status="RUNNING"
        )
        db.session.add(rt)
        db.session.commit()

        checkins = CheckInService.evaluate_unstarted_activities(test_user_id, grace_minutes=10)
        assert len(checkins) == 0
