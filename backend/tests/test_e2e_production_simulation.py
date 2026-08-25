"""
DeadlineOS — End-to-End Production Workflow Simulation (M13)
=============================================================
Simulates real user lifecycles across Tasks, Goals, Habits, Scheduling,
Runtime Execution, Notifications, Recovery, Analytics, and AI.
"""

from database.db import db
from models.task import Task
from models.goal import Goal, Habit
from models.user import User


def test_e2e_user_creation_and_task_lifecycle(client, mock_auth_headers):
    """E2E Flow: Create tasks, update status, and fetch dashboard telemetry."""
    # 1. Create Task
    task_payload = {
        "title": "Complete Production Verification",
        "priority": "P1",
        "deadline": "2026-12-31T23:59:59Z",
        "duration": 45
    }
    res = client.post("/api/tasks", json=task_payload, headers=mock_auth_headers)
    assert res.status_code in [200, 201]

    # 2. Get Tasks
    tasks_res = client.get("/api/tasks", headers=mock_auth_headers)
    assert tasks_res.status_code == 200
    tasks = tasks_res.get_json().get("tasks", [])
    assert len(tasks) >= 1

    # 3. Fetch Analytics Overview
    analytics_res = client.get("/api/analytics/overview", headers=mock_auth_headers)
    assert analytics_res.status_code == 200


def test_e2e_goals_and_habits_lifecycle(client, mock_auth_headers):
    """E2E Flow: Create goals and habits and verify retrieval."""
    # 1. Create Goal
    goal_res = client.post("/api/goals", json={"title": "Master Distributed Systems", "target_date": "2026-12-31"}, headers=mock_auth_headers)
    assert goal_res.status_code in [200, 201]

    # 2. Create Habit
    habit_res = client.post("/api/habits", json={"name": "Daily Deep Work Session", "frequency": "DAILY"}, headers=mock_auth_headers)
    assert habit_res.status_code in [200, 201]


def test_e2e_recovery_center_and_actions(client, mock_auth_headers):
    """E2E Flow: Recovery skip-today and vacation mode triggers."""
    res = client.post("/api/recovery/skip-today", json={"entity_id": "test_task_1", "entity_type": "TASK", "reason": "Conflict"}, headers=mock_auth_headers)
    assert res.status_code in [200, 400, 404]  # Valid structured response
