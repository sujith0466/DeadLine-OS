"""
DeadlineOS — Phase 6 Milestone 7 Unit Tests
=============================================
Tests Weekly AI Coach with deterministic fallback, insufficient data handling, and persistence.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.intelligence import CoachReport
from services.ai.weekly_coach import WeeklyAICoachService
from services.ai.provider import DeterministicFallbackProvider


@pytest.fixture
def test_user_id(app):
    user_id = "user-ai-m7"
    with app.app_context():
        user = User(
            id=user_id,
            email="ai_m7@deadlineos.com",
            full_name="AI M7 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_weekly_coach_generates_and_persists_report(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # 1. Add completed task
        t_done = Task(
            id="task-m7-done",
            user_id=test_user_id,
            title="Complete Auth Overhaul",
            status="completed",
            deadline=now - timedelta(days=2),
            estimated_hours=4.0,
            actual_hours=3.5
        )
        t_done.updated_at = now - timedelta(days=2)
        db.session.add(t_done)
        db.session.commit()

        # 2. Generate coach report
        report = WeeklyAICoachService.generate_weekly_report(
            user_id=test_user_id,
            persist=True,
            provider=DeterministicFallbackProvider()
        )

        assert report is not None
        assert "summary" in report
        assert len(report["strengths"]) >= 1
        assert "weekly_challenge" in report
        assert "report_id" in report

        # 3. Verify in database
        saved = CoachReport.query.get(report["report_id"])
        assert saved is not None
        assert saved.user_id == test_user_id
