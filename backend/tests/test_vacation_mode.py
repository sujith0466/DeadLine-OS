"""
DeadlineOS — Phase 5 Milestone 5 Unit Tests
=============================================
Tests Vacation Mode activation, date evaluation, and deactivation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from services.recovery.service import RecoveryService


@pytest.fixture
def test_user_id(app):
    user_id = "user-rec-m5"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m5@deadlineos.com",
            full_name="Recovery M5 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_vacation_mode_lifecycle(app, test_user_id):
    with app.app_context():
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tomorrow_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

        # 1. Activate vacation mode
        start_res = RecoveryService.set_vacation_mode(
            user_id=test_user_id,
            start_date=today_str,
            end_date=tomorrow_str,
            reason="Summer Retreat"
        )
        assert start_res["success"] is True
        assert start_res["vacation_mode"]["enabled"] is True

        # Verify active today
        assert RecoveryService.is_user_on_vacation(test_user_id) is True

        # 2. End vacation mode
        end_res = RecoveryService.end_vacation_mode(test_user_id)
        assert end_res["success"] is True
        assert end_res["vacation_mode"]["enabled"] is False

        # Verify no longer active
        assert RecoveryService.is_user_on_vacation(test_user_id) is False
