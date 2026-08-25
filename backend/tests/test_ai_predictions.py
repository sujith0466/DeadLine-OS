"""
DeadlineOS — Phase 6 Milestone 2 Unit Tests
=============================================
Tests Delay Detection and Miss Prediction services with deterministic fallbacks.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from services.ai.delay_detection import DelayDetectionService
from services.ai.miss_prediction import MissPredictionService
from services.ai.provider import DeterministicFallbackProvider


@pytest.fixture
def test_user_id(app):
    user_id = "user-ai-m2"
    with app.app_context():
        user = User(
            id=user_id,
            email="ai_m2@deadlineos.com",
            full_name="AI M2 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_delay_detection_deterministic_fallback(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # 1. Create a task and a long paused session
        task = Task(
            id="task-m2-1",
            user_id=test_user_id,
            title="Complex Kernel Build",
            status="in_progress",
            deadline=now + timedelta(hours=3),
            estimated_hours=2.0
        )
        db.session.add(task)

        rt_state = RuntimeState(
            id="rt-m2-1",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id=task.id,
            status="RUNNING"
        )
        db.session.add(rt_state)

        sess = RuntimeSession(
            id="sess-m2-1",
            runtime_state_id=rt_state.id,
            started_at=now - timedelta(hours=1),
            ended_at=now,
            planned_duration_sec=1800,
            paused_duration_sec=1200,  # 20 min paused
            completion_source="Manual"
        )
        db.session.add(sess)
        db.session.commit()

        # Run delay detection using deterministic fallback provider
        result = DelayDetectionService.evaluate_delay_risk(
            user_id=test_user_id,
            provider=DeterministicFallbackProvider()
        )

        assert result is not None
        assert result["delay_probability"] >= 50
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert len(result["evidence"]) >= 1
        assert "recommended_action" in result


def test_miss_prediction_deterministic_fallback(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # Create a task due in 30 minutes that requires 3 hours
        task = Task(
            id="task-m2-tight",
            user_id=test_user_id,
            title="Emergency Patch Deployment",
            status="pending",
            deadline=now + timedelta(minutes=30),
            estimated_hours=3.0,
            actual_hours=0.0
        )
        db.session.add(task)
        db.session.commit()

        # Run miss prediction
        result = MissPredictionService.predict_miss_risk(
            user_id=test_user_id,
            provider=DeterministicFallbackProvider()
        )

        assert result is not None
        assert result["miss_probability"] >= 50
        assert "Emergency Patch Deployment" in result["at_risk_tasks"]
        assert len(result["evidence"]) >= 1
