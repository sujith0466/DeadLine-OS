import pytest
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from app import create_app
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import Schedule, ScheduleSlot
from models.user_settings import UserSettings


@pytest.fixture
def app_and_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        with app.test_client() as client:
            yield app, client


def test_planner_endpoint_full_lifecycle(app_and_client, monkeypatch):
    """Verify Task -> Planner -> ScheduleSlot -> Serialization -> Visibility lifecycle."""
    app, client = app_and_client

    user_id = str(uuid.uuid4())

    def mock_get_unverified_header(token):
        return {"alg": "HS256"}

    def mock_decode(*args, **kwargs):
        return {"sub": user_id, "email": "planner_test@example.com"}

    monkeypatch.setattr(jwt, "get_unverified_header", mock_get_unverified_header)
    monkeypatch.setattr(jwt, "decode", mock_decode)

    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    with app.app_context():
        # Setup User with explicit timezone
        user = User(
            id=user_id,
            email=f"u_{user_id[:8]}@example.com",
            username=f"u_{user_id[:8]}",
            full_name="Planner Test User",
            timezone="America/New_York",
        )
        settings = UserSettings(user_id=user_id)
        db.session.add_all([user, settings])
        db.session.commit()

        # 1. Create realistic tasks
        task1 = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Prepare system design review",
            estimated_hours=1.5,
            category="work",
            status="pending",
            deadline=datetime.now(timezone.utc) + timedelta(days=2),
        )
        task2 = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Submit internship documentation",
            estimated_hours=0.75,
            category="work",
            status="pending",
            deadline=datetime.now(timezone.utc) + timedelta(days=5),
        )
        db.session.add_all([task1, task2])
        db.session.commit()

        # 2. Run Planner via API endpoint
        response = client.post(
            "/api/agents/plan",
            headers=headers,
            json={
                "tasks": [
                    {
                        "id": task1.id,
                        "title": task1.title,
                        "estimated_hours": 1.5,
                        "deadline": task1.deadline.isoformat(),
                    },
                    {
                        "id": task2.id,
                        "title": task2.title,
                        "estimated_hours": 0.75,
                        "deadline": task2.deadline.isoformat(),
                    },
                ],
                "availability": {
                    "daily_available_hours": 6,
                    "strategy": "Balanced",
                    "preferred_work_hours": {"start": "09:00", "end": "17:00"},
                },
            },
        )

        assert response.status_code in [200, 201]
        data = response.get_json()
        assert data is not None

        # Verify schedule serialization
        sched_data = data.get("data") or data.get("schedule") or data
        slots = sched_data.get("schedule", [])
        assert len(slots) > 0

        first_slot = slots[0]
        assert "start_time" in first_slot
        assert "end_time" in first_slot
        assert "start_time_utc" in first_slot
        assert "end_time_utc" in first_slot
        assert isinstance(first_slot["start_time"], str)

        # 3. Verify downstream Calendar events visibility
        cal_resp = client.get("/api/calendar/events", headers=headers)
        assert cal_resp.status_code == 200
        cal_data = cal_resp.get_json()
        assert len(cal_data.get("data", [])) > 0

        # 4. Verify downstream Today surface visibility
        today_resp = client.get("/api/today", headers=headers)
        assert today_resp.status_code == 200
        today_data = today_resp.get_json()
        assert today_data is not None


def test_planner_empty_tasks(app_and_client, monkeypatch):
    """Verify Planner handles empty tasks gracefully."""
    app, client = app_and_client
    user_id = str(uuid.uuid4())

    def mock_get_unverified_header(token):
        return {"alg": "HS256"}

    def mock_decode(*args, **kwargs):
        return {"sub": user_id, "email": "empty_planner@example.com"}

    monkeypatch.setattr(jwt, "get_unverified_header", mock_get_unverified_header)
    monkeypatch.setattr(jwt, "decode", mock_decode)

    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    with app.app_context():
        user = User(
            id=user_id,
            email=f"u_{user_id[:8]}@example.com",
            username=f"u_{user_id[:8]}",
            full_name="Empty Test User",
            timezone="UTC",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/agents/plan",
            headers=headers,
            json={"tasks": [], "availability": {"daily_available_hours": 8}},
        )
        assert response.status_code in [200, 201]
