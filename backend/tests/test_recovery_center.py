"""
DeadlineOS — Phase 5 Milestone 3 Unit Tests
=============================================
Tests Recovery Center aggregation and action execution routing.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from services.recovery.service import RecoveryService


@pytest.fixture
def test_user_id(app):
    user_id = "user-rec-m3"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m3@deadlineos.com",
            full_name="Recovery M3 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_recovery_center_aggregation_and_actions(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # 1. Create overdue task
        overdue_task = Task(
            id="task-rc-overdue",
            user_id=test_user_id,
            title="Overdue Tax Report",
            status="pending",
            deadline=now - timedelta(hours=3)
        )
        db.session.add(overdue_task)

        # 2. Create missed slot
        missed_slot = ScheduleSlot(
            id="slot-rc-missed",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id=overdue_task.id,
            task_title="Overdue Tax Report",
            start_time=now - timedelta(hours=5),
            end_time=now - timedelta(hours=4),
            status="PLANNED"
        )
        db.session.add(missed_slot)
        db.session.commit()

        # Retrieve recoverable items
        items = RecoveryService.get_recoverable_items(test_user_id)
        assert len(items["missed"]) >= 1
        assert len(items["overdue"]) >= 1
        assert items["total_threats"] >= 2

        # Execute recovery complete action
        res = RecoveryService.execute_recovery_action(
            user_id=test_user_id,
            action="COMPLETE",
            entity_id=overdue_task.id,
            entity_type="TASK"
        )
        assert res["success"] is True

        # Verify task completed
        saved_task = db.session.get(Task, overdue_task.id)
        assert saved_task.status == "completed"
