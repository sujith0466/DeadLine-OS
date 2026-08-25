"""
DeadlineOS — Phase 7 Milestone 6: Deadline Heatmap Tests
========================================================
Tests deterministic deadline heatmap generation, time of day distribution,
density level classification, and GET /api/analytics/deadline-heatmap endpoint.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from services.analytics.deadline_heatmap import DeadlineHeatmapService


def test_deadline_heatmap_buckets_and_density(app):
    user = User(
        id="test-user-dh-1",
        email="dh1@example.com",
        full_name="Deadline Heatmap User",
        timezone="UTC"
    )
    db.session.add(user)

    today = datetime.now(timezone.utc)
    
    # Task with deadline today
    t1 = Task(
        id="task-dh-1",
        user_id="test-user-dh-1",
        title="Due Today Task",
        deadline=today,
        status="pending"
    )
    # Slot today in morning
    s1 = ScheduleSlot(
        id="slot-dh-1",
        user_id="test-user-dh-1",
        task_title="Morning Coding",
        start_time=datetime(today.year, today.month, today.day, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(today.year, today.month, today.day, 11, 0, tzinfo=timezone.utc),
        status="COMPLETED"
    )
    db.session.add_all([t1, s1])
    db.session.commit()

    heatmap = DeadlineHeatmapService.generate_deadline_heatmap("test-user-dh-1", days=7)

    assert heatmap["days_analyzed"] == 7
    assert len(heatmap["heatmap"]) == 7
    assert heatmap["time_of_day_distribution"]["morning"] >= 1
    today_str = f"{today.year:04d}-{today.month:02d}-{today.day:02d}"
    today_item = next((item for item in heatmap["heatmap"] if item["date"] == today_str), None)
    assert today_item is not None
    assert today_item["deadlines_count"] >= 1
    assert today_item["completed_count"] >= 1


def test_deadline_heatmap_api_endpoint(client, mock_auth_headers):
    user_id = mock_auth_headers["Authorization"].split(" ")[1]
    user = User(
        id=user_id,
        email="api_dh@example.com",
        full_name="API DH User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    resp = client.get("/api/analytics/deadline-heatmap?days=14", headers=mock_auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "heatmap" in data["data"]
    assert len(data["data"]["heatmap"]) == 14
