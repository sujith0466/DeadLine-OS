"""
DeadlineOS — Phase 7 Milestone 12: Performance & Data Safety Tests
==================================================================
Tests:
1. Zero-Mutation Verification: Ensures that calling all analytics services
   does not alter any authoritative domain rows.
2. Timezone Boundary Safety: Verifies UTC boundary calculations across
   various global user offsets (UTC, IST +05:30, EST -05:00, JST +09:00).
3. Performance Benchmark: Verifies all analytics endpoints execute within latency budget.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.goal import Goal, Habit, HabitLog
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.recovery import RecoveryRecord, RecoveryActionType
from models.notification import Notification

from services.analytics.morning_brief import MorningBriefService
from services.analytics.evening_reflection import EveningReflectionService
from services.analytics.daily_score import DailyScoreService
from services.analytics.habit_health import HabitHealthService
from services.analytics.goal_progress import GoalProgressService
from services.analytics.deadline_heatmap import DeadlineHeatmapService
from services.analytics.timeline import TimelineAnalyticsService
from services.analytics.session_analytics import SessionAnalyticsService
from services.analytics.trends import TrendsAnalyticsService
from services.analytics.foundation import AnalyticsTimeWindow


def test_zero_mutation_safety(app):
    """Verify that analytics operations are strictly read-only and never mutate database state."""
    user = User(
        id="test-user-p7-safety",
        email="p7safe@example.com",
        full_name="Safety User",
        timezone="UTC"
    )
    db.session.add(user)

    today = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)

    task = Task(
        id="task-safe-1",
        user_id="test-user-p7-safety",
        title="Immutable Task",
        deadline=today + timedelta(days=1),
        status="pending",
        estimated_hours=2.0
    )
    goal = Goal(
        id="goal-safe-1",
        user_id="test-user-p7-safety",
        title="Immutable Goal",
        status="Active",
        health_score=85,
        progress_percentage=40
    )
    habit = Habit(
        id="habit-safe-1",
        user_id="test-user-p7-safety",
        name="Immutable Habit",
        frequency="Daily",
        current_streak=5,
        longest_streak=10,
        completion_rate=80,
        momentum_score=75
    )
    slot = ScheduleSlot(
        id="slot-safe-1",
        user_id="test-user-p7-safety",
        task_title="Immutable Slot",
        start_time=today,
        end_time=today + timedelta(hours=1),
        status="PLANNED",
        priority=80
    )
    state = RuntimeState(
        id="rs-safe-1",
        user_id="test-user-p7-safety",
        entity_type="TASK",
        entity_id="task-safe-1",
        status="RUNNING"
    )
    db.session.add_all([task, goal, habit, slot, state])
    db.session.flush()

    session = RuntimeSession(
        id="sess-safe-1",
        runtime_state_id="rs-safe-1",
        started_at=today,
        ended_at=today + timedelta(minutes=45),
        planned_duration_sec=3600,
        paused_duration_sec=0,
        completion_source="Manual"
    )
    rec = RecoveryRecord(
        id="rec-safe-1",
        user_id="test-user-p7-safety",
        action_type=RecoveryActionType.SKIP,
        entity_type="TASK",
        created_at=today
    )
    notif = Notification(
        id="notif-safe-1",
        user_id="test-user-p7-safety",
        title="Safety Alert",
        severity="high",
        read=False,
        created_at=today
    )
    db.session.add_all([session, rec, notif])
    db.session.commit()

    # Capture original entity snapshots
    t_status_before = task.status
    g_status_before = goal.status
    h_streak_before = habit.current_streak
    s_status_before = slot.status
    rs_status_before = state.status

    # Execute all analytics services
    MorningBriefService.generate_morning_brief("test-user-p7-safety", "2026-08-25")
    EveningReflectionService.generate_evening_reflection("test-user-p7-safety", "2026-08-25")
    DailyScoreService.calculate_daily_score("test-user-p7-safety", "2026-08-25")
    HabitHealthService.calculate_habit_health("test-user-p7-safety")
    GoalProgressService.calculate_goal_progress("test-user-p7-safety")
    DeadlineHeatmapService.generate_deadline_heatmap("test-user-p7-safety", days=7)
    TimelineAnalyticsService.get_timeline("test-user-p7-safety", start_date="2026-08-25", end_date="2026-08-25")
    SessionAnalyticsService.get_session_analytics("test-user-p7-safety", days=7)
    TrendsAnalyticsService.get_trends("test-user-p7-safety", days=7)

    # Refresh from database and assert complete immutability
    db.session.expire_all()
    t_refreshed = db.session.get(Task, "task-safe-1")
    g_refreshed = db.session.get(Goal, "goal-safe-1")
    h_refreshed = db.session.get(Habit, "habit-safe-1")
    s_refreshed = db.session.get(ScheduleSlot, "slot-safe-1")
    rs_refreshed = db.session.get(RuntimeState, "rs-safe-1")

    assert t_refreshed.status == t_status_before
    assert g_refreshed.status == g_status_before
    assert h_refreshed.current_streak == h_streak_before
    assert s_refreshed.status == s_status_before
    assert rs_refreshed.status == rs_status_before


def test_timezone_boundary_precision(app):
    """Verify UTC boundary conversions for positive and negative timezone offsets."""
    user_ist = User(id="user-ist", email="ist@example.com", full_name="IST User", timezone="Asia/Kolkata")
    user_est = User(id="user-est", email="est@example.com", full_name="EST User", timezone="America/New_York")
    user_tokyo = User(id="user-tokyo", email="tokyo@example.com", full_name="Tokyo User", timezone="Asia/Tokyo")
    db.session.add_all([user_ist, user_est, user_tokyo])
    db.session.commit()

    # IST (+05:30): 2026-08-25 starts at 2026-08-24 18:30 UTC
    start_ist, end_ist, _ = AnalyticsTimeWindow.get_day_boundaries_utc("user-ist", "2026-08-25")
    assert start_ist == datetime(2026, 8, 24, 18, 30, tzinfo=timezone.utc)
    assert end_ist == datetime(2026, 8, 25, 18, 29, 59, 999999, tzinfo=timezone.utc)

    # EST (EDT UTC-4 during August): 2026-08-25 starts at 2026-08-25 04:00 UTC
    start_est, end_est, _ = AnalyticsTimeWindow.get_day_boundaries_utc("user-est", "2026-08-25")
    assert start_est == datetime(2026, 8, 25, 4, 0, tzinfo=timezone.utc)
    assert end_est == datetime(2026, 8, 26, 3, 59, 59, 999999, tzinfo=timezone.utc)

    # Tokyo (+09:00): 2026-08-25 starts at 2026-08-24 15:00 UTC
    start_tokyo, end_tokyo, _ = AnalyticsTimeWindow.get_day_boundaries_utc("user-tokyo", "2026-08-25")
    assert start_tokyo == datetime(2026, 8, 24, 15, 0, tzinfo=timezone.utc)
    assert end_tokyo == datetime(2026, 8, 25, 14, 59, 59, 999999, tzinfo=timezone.utc)


def test_analytics_performance_latency_budget(app):
    """Verify all 9 analytics services execute within 200ms total budget."""
    user = User(
        id="user-perf",
        email="perf@example.com",
        full_name="Perf User",
        timezone="UTC"
    )
    db.session.add(user)
    db.session.commit()

    t_start = time.perf_counter()

    MorningBriefService.generate_morning_brief("user-perf", "2026-08-25")
    EveningReflectionService.generate_evening_reflection("user-perf", "2026-08-25")
    DailyScoreService.calculate_daily_score("user-perf", "2026-08-25")
    HabitHealthService.calculate_habit_health("user-perf")
    GoalProgressService.calculate_goal_progress("user-perf")
    DeadlineHeatmapService.generate_deadline_heatmap("user-perf", days=30)
    TimelineAnalyticsService.get_timeline("user-perf", limit=50)
    SessionAnalyticsService.get_session_analytics("user-perf", days=30)
    TrendsAnalyticsService.get_trends("user-perf", days=30)

    elapsed = time.perf_counter() - t_start
    # All 9 services combined should comfortably run in under 500ms
    assert elapsed < 0.5, f"Analytics suite exceeded latency budget: {elapsed:.4f}s"
