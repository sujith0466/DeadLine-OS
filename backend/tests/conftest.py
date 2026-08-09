import pytest
from app import create_app
from database.db import db
import uuid


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = "ERROR"
    LOG_FORMAT = "%(message)s"
    LOG_DATE_FORMAT = "%H:%M:%S"


@pytest.fixture
def app():
    app = create_app(config_override=TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.rollback()
        db.session.close()
        db.session.remove()
        db.engine.dispose()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_jwt_validation(monkeypatch):
    import jwt
    from models.user import User
    from database.db import db

    def mock_get_unverified_header(token):
        return {"alg": "HS256"}

    def mock_decode(*args, **kwargs):
        # Extract the user ID from the mock token which is a UUID
        token = args[0]
        return {"sub": token, "email": f"{token}@mock.com"}

    monkeypatch.setattr(jwt, "get_unverified_header", mock_get_unverified_header)
    monkeypatch.setattr(jwt, "decode", mock_decode)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "mock_secret")


@pytest.fixture
def mock_auth_headers():
    token = str(uuid.uuid4())
    return {"Authorization": f"Bearer {token}"}
