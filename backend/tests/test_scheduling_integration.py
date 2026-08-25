"""
DeadlineOS — Phase 3 Milestone 7 Integration Tests
===================================================
Tests Calendar and Today API integration with Smart Scheduling.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from services.scheduling.repository import SchedulingRepository
from services.calendar_service import CalendarService
from services.today_service import TodayService


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m7"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_m7@deadlineos.com",
            full_name="Schedule M7 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_calendar_service_includes_smart_slots(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # 1. Create a task deadline
        task = Task(
            id="task-cal-1",
            user_id=test_user_id,
            title="Submit Report",
            deadline=now + timedelta(hours=4)
        )
        db.session.add(task)

        # 2. Create a smart schedule slot
        slot = ScheduleSlot(
            id="slot-cal-1",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id=task.id,
            task_title="Write Report Section A",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            focus_block=True
        )
        SchedulingRepository.save_slot(slot)

        # Fetch events via CalendarService
        events = CalendarService.get_events(user_id=test_user_id)
        
        assert len(events) >= 2
        titles = [e["title"] for e in events]
        assert "Deadline: Submit Report" in titles
        assert "Write Report Section A" in titles


def test_today_service_merges_schedule_slots(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        task = Task(
            id="task-today-1",
            user_id=test_user_id,
            title="Urgent Bugfix",
            deadline=now + timedelta(hours=5),
            status="pending"
        )
        db.session.add(task)

        slot = ScheduleSlot(
            id="slot-today-1",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id=task.id,
            task_title="Urgent Bugfix",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2)
        )
        SchedulingRepository.save_slot(slot)

        today_data = TodayService.get_today_activities(test_user_id)
        upcoming = today_data["upcoming"]
        
        target_activity = next((a for a in upcoming if a["id"] == task.id), None)
        assert target_activity is not None
        assert target_activity["schedule_slot"] is not None
        assert target_activity["schedule_slot"]["id"] == "slot-today-1"
