"""
DeadlineOS — Phase 5 Milestone 0 Unit Tests
=============================================
Tests RecoveryRecord persistence, RecoveryRepository, and RecoveryService logging.
"""

import pytest
from datetime import datetime, timezone
from database.db import db
from models.user import User
from models.recovery import RecoveryRecord, RecoveryActionType
from services.recovery.repository import RecoveryRepository
from services.recovery.service import RecoveryService


@pytest.fixture
def test_user_id(app):
    user_id = "user-rec-m0"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m0@deadlineos.com",
            full_name="Recovery M0 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_recovery_record_creation_and_query(app, test_user_id):
    with app.app_context():
        rec = RecoveryService.log_recovery_action(
            user_id=test_user_id,
            action_type=RecoveryActionType.SKIP,
            entity_type="TASK",
            entity_id="task-rec-1",
            details={"reason": "User skipped today due to workload"}
        )

        assert rec is not None
        assert rec.action_type == RecoveryActionType.SKIP
        assert rec.entity_id == "task-rec-1"
        assert rec.details.get("reason") == "User skipped today due to workload"

        records = RecoveryRepository.get_recent_records(test_user_id)
        assert len(records) >= 1
        assert records[0].id == rec.id
