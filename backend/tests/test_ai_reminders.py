"""
DeadlineOS — Phase 6 Milestone 3 Unit Tests
=============================================
Tests Adaptive Reminder Intelligence with deterministic fallbacks and schema compliance.
"""

import pytest
from database.db import db
from models.user import User
from services.ai.reminder_intelligence import AdaptiveReminderService
from services.ai.provider import DeterministicFallbackProvider


@pytest.fixture
def test_user_id(app):
    user_id = "user-ai-m3"
    with app.app_context():
        user = User(
            id=user_id,
            email="ai_m3@deadlineos.com",
            full_name="AI M3 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_adaptive_reminder_recommendations_fallback(app, test_user_id):
    with app.app_context():
        # 1. High priority test
        res_high = AdaptiveReminderService.recommend_reminder_timing(
            user_id=test_user_id,
            slot_duration_minutes=90,
            priority_score=90,
            provider=DeterministicFallbackProvider()
        )
        assert res_high is not None
        assert 30 in res_high["recommended_pre_alerts"]
        assert len(res_high["recommended_reminders"]) >= 2
        assert len(res_high["evidence"]) >= 1

        # 2. Short sprint test
        res_short = AdaptiveReminderService.recommend_reminder_timing(
            user_id=test_user_id,
            slot_duration_minutes=25,
            priority_score=40,
            provider=DeterministicFallbackProvider()
        )
        assert res_short is not None
        assert res_short["recommended_pre_alerts"] == [10]
        assert res_short["recommended_reminders"] == [3]
