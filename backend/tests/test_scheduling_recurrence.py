"""
DeadlineOS — Phase 3 Milestone 2 Unit Tests
=============================================
Tests deterministic recurrence expansion (DAILY, WEEKLY, WEEKDAYS, INTERVAL_DAYS)
and occurrence materialization without duplicate slots.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.recurrence_rule import RecurrenceRule
from services.scheduling.repository import SchedulingRepository
from services.scheduling.recurrence_engine import RecurrenceEngine


@pytest.fixture
def test_user_id(app):
    user_id = "user-sched-m2"
    with app.app_context():
        user = User(
            id=user_id,
            email="sched_m2@deadlineos.com",
            full_name="Schedule M2 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_daily_recurrence_expansion(app, test_user_id):
    with app.app_context():
        start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
        rule = RecurrenceRule(
            id="rule-daily-1",
            user_id=test_user_id,
            frequency="DAILY",
            interval=1,
            start_date=start,
            end_date=start + timedelta(days=5),
            occurrence_count=5
        )
        SchedulingRepository.save_recurrence_rule(rule)

        dates = RecurrenceEngine.expand_dates(
            rule=rule,
            range_start=start,
            range_end=start + timedelta(days=10),
            tz_name="UTC"
        )

        assert len(dates) == 5
        assert dates[0] == start.date()
        assert dates[-1] == (start + timedelta(days=4)).date()


def test_weekday_recurrence_expansion(app, test_user_id):
    with app.app_context():
        # Start on a Monday
        start = datetime(2026, 9, 7, 9, 0, tzinfo=timezone.utc)  # 2026-09-07 is Monday
        rule = RecurrenceRule(
            id="rule-weekdays-1",
            user_id=test_user_id,
            frequency="WEEKDAYS",
            start_date=start,
            end_date=start + timedelta(days=14),
            occurrence_count=10
        )
        SchedulingRepository.save_recurrence_rule(rule)

        dates = RecurrenceEngine.expand_dates(
            rule=rule,
            range_start=start,
            range_end=start + timedelta(days=14),
            tz_name="UTC"
        )

        # 2 weeks of weekdays = 10 days (no Sat/Sun)
        assert len(dates) == 10
        for d in dates:
            assert d.weekday() < 5


def test_occurrence_materialization_and_deduplication(app, test_user_id):
    with app.app_context():
        start = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
        rule = RecurrenceRule(
            id="rule-habit-mat",
            user_id=test_user_id,
            frequency="DAILY",
            interval=1,
            start_date=start,
            occurrence_count=3
        )
        SchedulingRepository.save_recurrence_rule(rule)

        # Materialize first time
        slots1 = RecurrenceEngine.materialize_occurrences(
            rule_id=rule.id,
            user_id=test_user_id,
            entity_type="HABIT",
            entity_id="habit-run-1",
            title="Daily Jogging",
            start_time_local_hhmm="07:00",
            duration_minutes=45,
            range_start=start,
            range_end=start + timedelta(days=5)
        )

        assert len(slots1) == 3
        assert slots1[0].task_title == "Daily Jogging"
        assert slots1[0].recurrence_rule_id == rule.id

        # Materialize second time for same range — must not duplicate
        slots2 = RecurrenceEngine.materialize_occurrences(
            rule_id=rule.id,
            user_id=test_user_id,
            entity_type="HABIT",
            entity_id="habit-run-1",
            title="Daily Jogging",
            start_time_local_hhmm="07:00",
            duration_minutes=45,
            range_start=start,
            range_end=start + timedelta(days=5)
        )

        assert len(slots2) == 0  # No duplicates created
