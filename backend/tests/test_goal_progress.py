"""
DeadlineOS — Phase 7 Milestone 5: Goal Progress Tests
=====================================================
Tests deterministic goal progress calculations, milestone ratios,
risk levels, and GET /api/analytics/goal-progress endpoint.
"""

import pytest
from datetime import datetime, timezone
from database.db import db
from models.user import User
from models.goal import Goal, Milestone
from services.analytics.goal_progress import GoalProgressService


def test_goal_progress_calculation_and_risk(app):
    user = User(
        id="test-user-gp-1",
        email="gp1@example.com",
        full_name="Goal Progress User",
        timezone="UTC"
    )
    db.session.add(user)

    # 1. Goal with 2 milestones (1 completed)
    g1 = Goal(
        id="goal-gp-1",
        user_id="test-user-gp-1",
        title="Ship v2.0 Platform",
        category="Engineering",
        target_date="2026-09-30",
        status="Active",
        health_score=90
    )
    db.session.add(g1)
    db.session.flush()

    m1 = Milestone(
        id="ms-gp-1",
        goal_id="goal-gp-1",
        user_id="test-user-gp-1",
        title="Milestone 1: Backend",
        completed=True
    )
    m2 = Milestone(
        id="ms-gp-2",
        goal_id="goal-gp-1",
        user_id="test-user-gp-1",
        title="Milestone 2: Frontend",
        completed=False
    )
    db.session.add_all([m1, m2])
    db.session.commit()

    progress = GoalProgressService.calculate_goal_progress("test-user-gp-1")

    assert progress["active_goals_count"] == 1
    assert progress["overall_completion_rate_pct"] == 50.0
    assert progress["goals"][0]["progress_percentage"] == 50.0
    assert progress["goals"][0]["total_milestones"] == 2
    assert progress["goals"][0]["completed_milestones"] == 1
    assert progress["goals"][0]["risk_level"] == "ON_TRACK"


def test_goal_progress_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_gp@example.com",
        full_name="API GP User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/goal-progress", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "overall_completion_rate_pct" in data["data"]
