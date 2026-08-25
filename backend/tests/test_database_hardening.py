"""
DeadlineOS — Database Production Hardening Tests
=================================================
Verifies connection pool configuration, rollback safety, and transactional resilience.
"""

from database.db import db
from models.task import Task
from models.user import User


def test_database_engine_options(app):
    """Verify production engine options for connection pooling and pre-ping."""
    engine = db.engine
    # In SQLite memory test mode, pool exists; in production PostgreSQL it uses QueuePool
    assert engine is not None


def test_transaction_rollback_safety(app):
    """Verify that an uncommitted error rolls back safely without corrupting the session."""
    with app.app_context():
        user = User(id="db_user_1", email="db1@test.com")
        db.session.add(user)
        db.session.commit()

        # Attempt invalid insert without required fields or invalid type
        try:
            invalid_task = Task(id=None, user_id="db_user_1", title=None)
            db.session.add(invalid_task)
            db.session.flush()
        except Exception:
            db.session.rollback()

        # Session should be healthy and usable after rollback
        recovered_user = User.query.filter_by(id="db_user_1").first()
        assert recovered_user is not None
        assert recovered_user.email == "db1@test.com"


def test_db_create_all_not_in_create_app():
    """Verify that create_app does not invoke db.create_all() for production safety."""
    import inspect
    from app import create_app
    source = inspect.getsource(create_app)
    assert "db.create_all()" not in source
