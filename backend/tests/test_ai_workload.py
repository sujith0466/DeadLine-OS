"""
DeadlineOS — Phase 6 Milestone 4 Unit Tests
=============================================
Tests Dynamic Workload Balancer with deterministic fallback and schema compliance.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from services.ai.workload_balancer import WorkloadBalancerService
from services.ai.provider import DeterministicFallbackProvider


@pytest.fixture
def test_user_id(app):
    user_id = "user-ai-m4"
    with app.app_context():
        user = User(
            id=user_id,
            email="ai_m4@deadlineos.com",
            full_name="AI M4 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_workload_balancer_detects_overload_fallback(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # Add 4 slots of 2 hours each today (8 hours total)
        for i in range(4):
            slot = ScheduleSlot(
                id=f"slot-m4-{i}",
                user_id=test_user_id,
                entity_type="TASK",
                entity_id=f"task-m4-{i}",
                task_title=f"Heavy Task {i}",
                start_time=now + timedelta(hours=i * 2),
                end_time=now + timedelta(hours=(i * 2) + 2),
                priority=40 if i == 3 else 80,
                status="PLANNED"
            )
            db.session.add(slot)
        db.session.commit()

        # Evaluate workload
        result = WorkloadBalancerService.evaluate_workload(
            user_id=test_user_id,
            provider=DeterministicFallbackProvider()
        )

        assert result is not None
        assert result["is_overloaded"] is True
        assert len(result["overloaded_dates"]) >= 1
        assert len(result["evidence"]) >= 1
        assert len(result["redistribution_plan"]) >= 1
