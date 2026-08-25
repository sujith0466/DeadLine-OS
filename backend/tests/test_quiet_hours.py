"""
DeadlineOS — Phase 4 Milestone 4 Unit Tests
=============================================
Tests QuietHoursService overnight spans, timezone conversion, deferrals, and critical bypass.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.user_settings import UserSettings
from services.notifications.quiet_hours_service import QuietHoursService


@pytest.fixture
def test_user_id(app):
    user_id = "user-notif-m4"
    with app.app_context():
        user = User(
            id=user_id,
            email="notif_m4@deadlineos.com",
            full_name="Notification M4 User",
            timezone="America/New_York"  # UTC-4 / UTC-5
        )
        settings = UserSettings(
            user_id=user_id,
            notifications={
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "07:00",
                "quiet_hours_allow_critical": True
            }
        )
        db.session.add(user)
        db.session.add(settings)
        db.session.commit()
    return user_id


def test_quiet_hours_overnight_suppression(app, test_user_id):
    with app.app_context():
        # America/New_York 23:30 on 2026-09-01 -> UTC is 03:30 on 2026-09-02 (EDT is UTC-4)
        target_utc = datetime(2026, 9, 2, 3, 30, tzinfo=timezone.utc)

        in_quiet, deferred_utc = QuietHoursService.is_in_quiet_hours(
            user_id=test_user_id,
            target_utc=target_utc,
            is_critical=False
        )

        assert in_quiet is True
        assert deferred_utc is not None
        # Deferred to 07:00 EDT on 2026-09-02 -> UTC 11:00 on 2026-09-02
        assert deferred_utc.hour == 11
        assert deferred_utc.minute == 0


def test_quiet_hours_critical_bypass(app, test_user_id):
    with app.app_context():
        target_utc = datetime(2026, 9, 2, 3, 30, tzinfo=timezone.utc)

        in_quiet, deferred_utc = QuietHoursService.is_in_quiet_hours(
            user_id=test_user_id,
            target_utc=target_utc,
            is_critical=True
        )

        assert in_quiet is False
        assert deferred_utc is None


def test_quiet_hours_daytime_allowed(app, test_user_id):
    with app.app_context():
        # America/New_York 14:00 (EDT) -> UTC 18:00
        target_utc = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)

        in_quiet, deferred_utc = QuietHoursService.is_in_quiet_hours(
            user_id=test_user_id,
            target_utc=target_utc,
            is_critical=False
        )

        assert in_quiet is False
        assert deferred_utc is None
