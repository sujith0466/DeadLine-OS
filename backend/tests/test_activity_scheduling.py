"""
DeadlineOS — Phase 3 Milestone 1 Unit Tests
=============================================
Tests multi-domain activity scheduling (Task, Goal, Habit) and schedule API.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.goal import Goal, Habit
from services.scheduling.activity_scheduler import ActivityScheduler
from services.scheduling.repository import SchedulingRepository


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m1"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_m1@deadlineos.com",
            full_name="Schedule M1 User",
            timezone="America/New_York"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_schedule_task_activity(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        task = Task(
            id="task-m1-test",
            user_id=test_user_id,
            title="Algorithm Practice",
            deadline=now + timedelta(days=2),
            estimated_hours=2.0
        )
        db.session.add(task)
        db.session.commit()

        # Schedule the task
        slot = ActivityScheduler.schedule_activity(
            user_id=test_user_id,
            entity_type="TASK",
            entity_id=task.id,
            start_time=now,
            focus_block=True
        )

        assert slot.task_title == "Algorithm Practice"
        assert slot.entity_type == "TASK"
        assert slot.entity_id == task.id
        assert slot.focus_block is True
        assert (slot.end_time - slot.start_time).total_seconds() == 7200  # 2 hours


def test_schedule_habit_activity(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        habit = Habit(
            id="habit-m1-test",
            user_id=test_user_id,
            name="Morning Meditation",
            momentum_score=75
        )
        db.session.add(habit)
        db.session.commit()

        slot = ActivityScheduler.schedule_activity(
            user_id=test_user_id,
            entity_type="HABIT",
            entity_id=habit.id,
            start_time=now
        )

        assert slot.task_title == "Morning Meditation"
        assert slot.entity_type == "HABIT"
        assert slot.priority == 75
        assert (slot.end_time - slot.start_time).total_seconds() == 1800  # 30 mins default


def test_schedule_goal_activity(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        goal = Goal(
            id="goal-m1-test",
            user_id=test_user_id,
            title="Launch Startup MVP",
            priority="High"
        )
        db.session.add(goal)
        db.session.commit()

        slot = ActivityScheduler.schedule_activity(
            user_id=test_user_id,
            entity_type="GOAL",
            entity_id=goal.id,
            start_time=now
        )

        assert slot.task_title == "Launch Startup MVP"
        assert slot.entity_type == "GOAL"
        assert slot.priority == 85  # High priority map
