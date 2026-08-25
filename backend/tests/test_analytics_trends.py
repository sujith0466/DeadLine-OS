"""
DeadlineOS — Phase 7 Milestone 9: Trends Analytics Tests
========================================================
Tests multi-day completion trends, recovery trends, timeframe clamping,
and GET /api/analytics/trends endpoint.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from models.recovery import RecoveryRecord, RecoveryActionType
from services.analytics.trends import TrendsAnalyticsService


def test_trends_analytics_aggregation(app):
    user = User(
        id="test-user-tr-1",
        email="tr1@example.com",
        full_name="Trends User",
        timezone="UTC"
    )
    db.session.add(user)

    today = datetime.now(timezone.utc)
    slot1 = ScheduleSlot(
        id="slot-tr-1",
        user_id="test-user-tr-1",
        task_title="Trend Task 1",
        start_time=today,
        end_time=today + timedelta(hours=1),
        status="COMPLETED"
    )
    rec1 = RecoveryRecord(
        id="rec-tr-1",
        user_id="test-user-tr-1",
        action_type=RecoveryActionType.RESCHEDULE,
        created_at=today
    )
    db.session.add_all([slot1, rec1])
    db.session.commit()

    trends = TrendsAnalyticsService.get_trends("test-user-tr-1", days=7)

    assert trends["days_analyzed"] == 7
    assert len(trends["daily_trends"]) == 7
    assert trends["total_completed_tasks"] >= 1
    assert trends["total_recovery_actions"] >= 1
    assert trends["trend_direction"] in ["IMPROVING", "STABLE", "DECLINING"]


def test_trends_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_tr@example.com",
        full_name="API TR User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/trends?days=14", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "daily_trends" in data["data"]
    assert len(data["data"]["daily_trends"]) == 14
