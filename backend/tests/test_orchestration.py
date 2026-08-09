import pytest
from app import create_app
from database.db import db
from models.user import User
from models.telemetry import OrchestratorEvent
import uuid


from tests.conftest import TestConfig

@pytest.fixture
def client():
    app = create_app(config_override=TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            user_id = str(uuid.uuid4())
            u = User(
                id=user_id,
                email="test_orch@example.com",
                username="testorch",
                full_name="Test Orch",
            )
            db.session.add(u)
            db.session.commit()
            # Fake login via header
            client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {user_id}"
            # Because auth might need valid JWT, we might mock `require_auth` or just inject g.user_id
            yield client
            db.session.rollback()
            db.session.close()
            db.session.remove()
            db.engine.dispose()
            db.drop_all()


def test_orchestration_execute_route(client, mocker):
    # Mock require_auth to bypass JWT decode
    mocker.patch("api.orchestration.require_auth", lambda f: f)
    # Mock Gemini Service inside the route

    # We will test if the /api/orchestration/execute returns 500 NameError or success
    # By mocking OrchestratorService
    mock_orch = mocker.patch("api.orchestration.OrchestratorService")
    mock_orch.return_value.evaluate_system_state.return_value = {"status": "mocked"}

    # Inject g.user_id manually since we mocked auth
    @client.application.before_request
    def set_g():
        from flask import g, current_app
        g.user_id = "test-user-id"
        current_app.extensions = getattr(current_app, "extensions", {})
        current_app.extensions["gemini_service"] = mocker.Mock()

    response = client.post("/api/orchestration/execute")
    assert response.status_code == 200
    assert response.json["status"] == "mocked"
