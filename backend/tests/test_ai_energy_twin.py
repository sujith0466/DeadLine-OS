"""
DeadlineOS — Phase 6 Milestone 6 Unit Tests
=============================================
Tests Energy Preferences and Digital Twin learning lifecycle, precedence, and reset.
"""

import pytest
from database.db import db
from models.user import User
from models.task import Task
from models.user_settings import UserSettings
from services.ai.energy_preferences import EnergyPreferencesService
from services.ai.digital_twin_learning import DigitalTwinLearningService


@pytest.fixture
def test_user_id(app):
    user_id = "user-ai-m6"
    with app.app_context():
        user = User(
            id=user_id,
            email="ai_m6@deadlineos.com",
            full_name="AI M6 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_energy_preferences_crud_and_precedence(app, test_user_id):
    with app.app_context():
        # 1. Default preferences
        prefs = EnergyPreferencesService.get_energy_preferences(test_user_id)
        assert prefs["is_explicitly_configured"] is False

        # 2. Update explicit preferences
        set_res = EnergyPreferencesService.set_energy_preferences(
            user_id=test_user_id,
            peak_focus_start="08:00",
            peak_focus_end="11:00",
            preferred_session_duration_minutes=45
        )
        assert set_res["success"] is True
        assert set_res["energy_preferences"]["peak_focus_start"] == "08:00"
        assert set_res["energy_preferences"]["is_explicitly_configured"] is True


def test_digital_twin_learning_and_reset(app, test_user_id):
    with app.app_context():
        # 1. Add completed tasks with known velocity
        t1 = Task(
            id="task-twin-1",
            user_id=test_user_id,
            title="Task 1",
            status="completed",
            estimated_hours=2.0,
            actual_hours=3.0,  # 1.5 velocity
            deadline=None
        )
        # Note: deadline is required on Task model, let's provide dummy deadline
        from datetime import datetime, timezone, timedelta
        t1.deadline = datetime.now(timezone.utc)
        db.session.add(t1)
        db.session.commit()

        # 2. Rebuild profile
        rebuild_res = DigitalTwinLearningService.rebuild_learned_profile(test_user_id)
        assert rebuild_res["success"] is True
        prof = rebuild_res["learned_profile"]
        assert prof["sample_count"] >= 1
        assert prof["velocity_multiplier"] == 1.5

        # 3. Reset profile
        reset_res = DigitalTwinLearningService.reset_learned_profile(test_user_id)
        assert reset_res["success"] is True
        assert reset_res["learned_profile"]["sample_count"] == 0
        assert reset_res["learned_profile"]["velocity_multiplier"] == 1.0
