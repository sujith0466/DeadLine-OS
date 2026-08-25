"""
DeadlineOS — Phase 7 Milestone 4: Habit Health Tests
====================================================
Tests deterministic habit health calculations, streaks, momentum velocity,
and GET /api/analytics/habit-health endpoint.
"""

import pytest
from datetime import datetime, timezone
from database.db import db
from models.user import User
from models.goal import Habit, HabitLog
from services.analytics.habit_health import HabitHealthService


def test_habit_health_calculation_and_streaks(app):
    user = User(
        id="test-user-hh-1",
        email="hh1@example.com",
        full_name="Habit Health User",
        timezone="UTC"
    )
    db.session.add(user)

    h1 = Habit(
        id="habit-hh-1",
        user_id="test-user-hh-1",
        name="Morning Workout",
        frequency="Daily",
        current_streak=7,
        longest_streak=14,
        completion_rate=90,
        momentum_score=85,
        last_checkin_date="2026-08-25"
    )
    h2 = Habit(
        id="habit-hh-2",
        user_id="test-user-hh-1",
        name="Deep Work Block",
        frequency="Daily",
        current_streak=3,
        longest_streak=5,
        completion_rate=75,
        momentum_score=60,
        last_checkin_date="2026-08-24"
    )
    db.session.add_all([h1, h2])
    db.session.commit()

    health_data = HabitHealthService.calculate_habit_health("test-user-hh-1")

    assert health_data["active_habits_count"] == 2
    assert health_data["overall_health_score"] >= 70
    assert len(health_data["habits"]) == 2
    assert health_data["habits"][0]["current_streak"] == 7
    assert health_data["habits"][0]["trend"] == "STRONG_POSITIVE"


def test_habit_health_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_hh@example.com",
        full_name="API HH User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/habit-health", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "overall_health_score" in data["data"]
