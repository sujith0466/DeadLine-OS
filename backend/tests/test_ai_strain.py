"""
DeadlineOS — Phase 6 Milestone 5 Unit Tests
=============================================
Tests Workload Strain indicator with deterministic fallback and schema compliance.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from models.task import Task
from services.ai.workload_strain import WorkloadStrainService
from services.ai.provider import DeterministicFallbackProvider


@pytest.fixture
def test_user_id(app):
    user_id = "user-ai-m5"
    with app.app_context():
        user = User(
            id=user_id,
            email="ai_m5@deadlineos.com",
            full_name="AI M5 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_workload_strain_evaluation_fallback(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # Add 6 slots and 1 overdue task
        for i in range(6):
            slot = ScheduleSlot(
                id=f"slot-m5-{i}",
                user_id=test_user_id,
                entity_type="TASK",
                entity_id=f"task-m5-{i}",
                task_title=f"Sprint Task {i}",
                start_time=now + timedelta(hours=i),
                end_time=now + timedelta(hours=i + 1),
                priority=75,
                status="PLANNED"
            )
            db.session.add(slot)

        overdue_task = Task(
            id="task-m5-od",
            user_id=test_user_id,
            title="Overdue Client Deliverable",
            status="overdue",
            deadline=now - timedelta(hours=2),
            estimated_hours=1.5
        )
        db.session.add(overdue_task)
        db.session.commit()

        # Evaluate strain
        result = WorkloadStrainService.evaluate_workload_strain(
            user_id=test_user_id,
            provider=DeterministicFallbackProvider()
        )

        assert result is not None
        assert result["strain_score"] >= 50
        assert result["strain_level"] in ("ELEVATED", "HIGH")
        assert len(result["contributing_factors"]) >= 1
        assert len(result["evidence"]) >= 1
        assert "recommended_restoration" in result
