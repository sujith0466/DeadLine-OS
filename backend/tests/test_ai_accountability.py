"""
DeadlineOS — Phase 6 Milestone 8 Unit Tests
=============================================
Tests AI Accountability Partner and Phase 6 REST API endpoints.
"""

import pytest
from database.db import db
from models.user import User
from models.task import Task
from services.ai.accountability_partner import AccountabilityPartnerService
from services.ai.provider import DeterministicFallbackProvider


@pytest.fixture
def test_user_id(app):
    user_id = "user-ai-m8"
    with app.app_context():
        user = User(
            id=user_id,
            email="ai_m8@deadlineos.com",
            full_name="AI M8 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_accountability_partner_chat(app, test_user_id):
    with app.app_context():
        # Add a task
        from datetime import datetime, timezone, timedelta
        task = Task(
            id="task-m8-focus",
            user_id=test_user_id,
            title="Implement Kernel Scheduler",
            status="pending",
            deadline=datetime.now(timezone.utc) + timedelta(hours=4),
            estimated_hours=2.0
        )
        db.session.add(task)
        db.session.commit()

        # Chat with partner
        res = AccountabilityPartnerService.chat(
            user_id=test_user_id,
            user_message="What should I work on next?",
            provider=DeterministicFallbackProvider()
        )

        assert res is not None
        assert "Implement Kernel Scheduler" in res["reply"]
        assert len(res["suggested_actions"]) >= 1
        assert len(res["grounding_context"]) >= 1


def test_ai_api_endpoints(client, test_user_id):
    auth_headers = {"Authorization": f"Bearer {test_user_id}"}
    
    # Test GET energy preferences
    res = client.get(
        "/api/ai/energy-preferences",
        headers=auth_headers
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "peak_focus_start" in json_data["data"]

    # Test POST delay risk
    res = client.post(
        "/api/ai/delay-risk",
        headers=auth_headers,
        json={}
    )
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # Test POST coach weekly
    res = client.post(
        "/api/ai/coach/weekly",
        headers=auth_headers,
        json={"persist": False}
    )
    assert res.status_code == 200
    assert res.get_json()["success"] is True
