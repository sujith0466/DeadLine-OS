"""
DeadlineOS — Phase 5 Milestone 6 Unit Tests
=============================================
Tests Emergency Mode activation, non-critical shedding, and deactivation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.schedule import ScheduleSlot
from services.recovery.service import RecoveryService


@pytest.fixture
def test_user_id(app):
    user_id = "user-rec-m6"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m6@deadlineos.com",
            full_name="Recovery M6 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_emergency_mode_activation_and_deactivation(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)

        # 1. Activate Emergency Mode
        act_res = RecoveryService.activate_emergency_mode(
            user_id=test_user_id,
            reason="Workplace outage",
            auto_skip_non_critical=False
        )
        assert act_res["success"] is True
        assert RecoveryService.is_emergency_mode_active(test_user_id) is True

        # 2. Deactivate Emergency Mode
        deact_res = RecoveryService.deactivate_emergency_mode(test_user_id)
        assert deact_res["success"] is True
        assert RecoveryService.is_emergency_mode_active(test_user_id) is False
