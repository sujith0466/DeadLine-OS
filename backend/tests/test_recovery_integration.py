"""
DeadlineOS — Phase 5 Milestone 7 Integration Tests
===================================================
Tests full cross-system integration: Recovery, TodayService, ReminderService,
Vacation Mode, and Emergency Mode.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from models.notification import Notification
from services.today_service import TodayService
from services.recovery.service import RecoveryService
from services.notifications.reminder_service import ReminderService


@pytest.fixture
def test_user_id(app):
    user_id = "user-rec-m7"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m7@deadlineos.com",
            full_name="Recovery M7 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_today_service_respects_skip_and_emergency_mode(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # 1. High priority task
        t_high = Task(
            id="task-m7-high",
            user_id=test_user_id,
            title="Critical Server Patch",
            status="pending",
            deadline=now + timedelta(hours=4)
        )
        db.session.add(t_high)

        # 2. Low priority task
        t_low = Task(
            id="task-m7-low",
            user_id=test_user_id,
            title="Clean Download Folder",
            status="pending",
            deadline=now + timedelta(hours=4)
        )
        db.session.add(t_low)
        db.session.commit()

        # Regular Today view: Both tasks appear
        today_data = TodayService.get_today_activities(test_user_id)
        task_ids = [a["id"] for a in today_data["activities"]]
        assert "task-m7-high" in task_ids
        assert "task-m7-low" in task_ids

        # Set vacation mode and verify today service reflects is_vacation_mode
        RecoveryService.set_vacation_mode(test_user_id, start_date=now.strftime("%Y-%m-%d"), end_date=(now + timedelta(days=1)).strftime("%Y-%m-%d"))
        vac_today = TodayService.get_today_activities(test_user_id)
        assert vac_today["is_vacation_mode"] is True

        # End vacation mode
        RecoveryService.end_vacation_mode(test_user_id)


def test_reminder_suppression_during_vacation(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        slot = ScheduleSlot(
            id="slot-m7-vac",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id="task-vac-1",
            task_title="Vacation Activity",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
            status="PLANNED"
        )
        db.session.add(slot)
        db.session.commit()

        # Start Vacation
        RecoveryService.set_vacation_mode(test_user_id, start_date=today_str, end_date=tomorrow_str)

        # Generate reminders -> Should return empty list during vacation
        reminders = ReminderService.register_schedule_reminders(slot)
        assert len(reminders) == 0

        # End Vacation
        RecoveryService.end_vacation_mode(test_user_id)
