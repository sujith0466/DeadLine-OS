"""
DeadlineOS — Phase 7 Milestone 10: Analytics AI Tests
=====================================================
Tests analytics AI interpretation, fallback provider execution,
grounding facts validation, and POST /api/analytics/ai/interpret endpoint.
"""

import pytest
from database.db import db
from models.user import User
from services.ai.provider import AIProvider
from services.analytics.ai_interpretation import AnalyticsAIInterpretationService


class MockAnalyticsAIProvider(AIProvider):
    def generate_structured(self, system_prompt, user_prompt, schema, fallback_fn=None):
        return {
            "headline": "Outstanding Productivity Momentum",
            "key_insights": ["High completion consistency across all activities."],
            "strengths": ["Zero unmanaged overdue tasks."],
            "growth_areas": ["Increase focus block duration by 15 minutes."],
            "actionable_takeaway": "Maintain focus blocks early in the day.",
            "confidence_score": 95,
            "_provider": "openrouter",
            "_fallback_used": False
        }

    def generate_text(self, system_prompt, user_prompt):
        return "Analytics summary text."


def test_ai_interpretation_with_mock_provider(app):
    user = User(
        id="test-user-aai-1",
        email="aai1@example.com",
        full_name="Analytics AI User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    provider = MockAnalyticsAIProvider()
    res = AnalyticsAIInterpretationService.interpret_analytics("test-user-aai-1", days=7, provider=provider)

    assert res["headline"] == "Outstanding Productivity Momentum"
    assert len(res["strengths"]) >= 1
    assert "grounding_facts" in res
    assert res["grounding_facts"]["timeframe_days"] == 7
    assert res["_provider"] == "openrouter"


def test_ai_interpretation_fallback_mode(app):
    user = User(
        id="test-user-aai-2",
        email="aai2@example.com",
        full_name="Analytics AI Fallback User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    # Pass None / default provider in test environment without API keys -> triggers deterministic fallback
    res = AnalyticsAIInterpretationService.interpret_analytics("test-user-aai-2", days=7)
    assert res is not None
    assert "headline" in res
    assert len(res["key_insights"]) >= 2
    assert res["_fallback_used"] is True


def test_ai_interpretation_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_aai@example.com",
        full_name="API AAI User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.post("/api/analytics/ai/interpret", json={"days": 7}, headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "headline" in data["data"]
    assert "key_insights" in data["data"]
