"""
DeadlineOS — Phase 3 Milestone 5 Unit Tests
=============================================
Tests deterministic priority-based slot assignment and explainable rankings.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from services.scheduling.priority_scheduler import PriorityScheduler


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m5"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_m5@deadlineos.com",
            full_name="Schedule M5 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_effective_priority_calculation():
    now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    
    # Urgent deadline (<6 hours away)
    urgent_p = PriorityScheduler.calculate_effective_priority(
        priority_score=60,
        deadline=now + timedelta(hours=3),
        reference_time=now
    )
    assert urgent_p == 140.0  # 60 + 80

    # Non-urgent task (4 days away)
    normal_p = PriorityScheduler.calculate_effective_priority(
        priority_score=60,
        deadline=now + timedelta(days=4),
        reference_time=now
    )
    assert normal_p == 60.0


def test_priority_scheduling_order(app, test_user_id):
    with app.app_context():
        w_start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        w_end = datetime(2026, 9, 1, 13, 0, tzinfo=timezone.utc)

        activities = [
            {
                "entity_type": "TASK",
                "entity_id": "task-low",
                "title": "Low Priority Task",
                "priority": 30,
                "duration_minutes": 60,
                "deadline": (w_start + timedelta(days=5)).isoformat()
            },
            {
                "entity_type": "TASK",
                "entity_id": "task-high",
                "title": "High Priority Task",
                "priority": 90,
                "duration_minutes": 60,
                "deadline": (w_start + timedelta(hours=4)).isoformat()
            }
        ]

        result = PriorityScheduler.plan_priority_schedule(
            user_id=test_user_id,
            activities=activities,
            window_start=w_start,
            window_end=w_end,
            buffer_minutes=15,
            persist=False
        )

        assert result["scheduled_count"] == 2
        scheduled = result["scheduled"]

        # High priority task must be placed first at 09:00
        assert scheduled[0]["entity_id"] == "task-high"
        assert scheduled[0]["start_time"] == w_start.isoformat()

        # Low priority task must be placed after High priority task + 15 min buffer (10:15)
        assert scheduled[1]["entity_id"] == "task-low"
        expected_start = (w_start + timedelta(minutes=75)).isoformat()
        assert scheduled[1]["start_time"] == expected_start
