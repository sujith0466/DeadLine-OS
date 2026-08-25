"""
DeadlineOS — Phase 4 Milestone 8 Unit Tests
=============================================
Tests EscalationService tier calculation, escalation generation, and max tier bounding.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from models.notification import Notification, NotificationType
from services.notifications.escalation_service import EscalationService
from services.notifications.repository import NotificationRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m8"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m8@deadlineos.com",
            full_name="Notification M8 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_escalation_lifecycle_and_bounding(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        slot = ScheduleSlot(
            id="slot-esc-1",
            user_id=test_user_id,
            entity_id="task-esc-100",
            task_title="Production Incident Postmortem",
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=1),
            status="PLANNED"
        )
        db.session.add(slot)
        db.session.commit()

        # 1st evaluation -> Tier 1
        e1 = EscalationService.evaluate_escalations(test_user_id)
        assert len(e1) == 1
        assert "[Tier 1 Alert]" in e1[0].title
        assert e1[0].notification_type == NotificationType.ESCALATION

        # 2nd evaluation -> Tier 2
        e2 = EscalationService.evaluate_escalations(test_user_id)
        assert len(e2) == 1
        assert "[Tier 2 Alert]" in e2[0].title

        # 3rd evaluation -> Tier 3 (Max)
        e3 = EscalationService.evaluate_escalations(test_user_id)
        assert len(e3) == 1
        assert "[Tier 3 Alert]" in e3[0].title
        assert e3[0].severity == "critical"

        # 4th evaluation -> Capped, no further escalations generated
        e4 = EscalationService.evaluate_escalations(test_user_id)
        assert len(e4) == 0
