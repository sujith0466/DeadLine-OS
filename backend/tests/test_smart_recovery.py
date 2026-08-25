"""
DeadlineOS — Phase 5 Milestone 4 Unit Tests
=============================================
Tests deterministic Smart Recovery rules and recommendations.
"""

import pytest
from datetime import datetime, timezone, timedelta
from database.db import db
from models.user import User
from models.task import Task
from models.schedule import ScheduleSlot
from models.runtime_state import RuntimeState
from services.recovery.smart_recovery import SmartRecoveryService


@pytest.fixture
def test_user_id(app):
    user_id = "user-rec-m4"
    with app.app_context():
        user = User(
            id=user_id,
            email="rec_m4@deadlineos.com",
            full_name="Recovery M4 User",
            timezone="UTC"
        )
        db.session.add(user)
        db.session.commit()
    return user_id


def test_smart_recovery_generates_explainable_strategies(app, test_user_id):
    with app.app_context():
        now = datetime.now(timezone.utc)

        # 1. Create interrupted runtime state
        int_state = RuntimeState(
            id="rt-state-m4",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id="task-int-m4",
            status="INTERRUPTED"
        )
        db.session.add(int_state)

        # 2. Create missed slot
        missed_slot = ScheduleSlot(
            id="slot-m4-missed",
            user_id=test_user_id,
            entity_type="TASK",
            entity_id="task-missed-m4",
            task_title="Compile Phase 5 Specification",
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=2),
            status="PLANNED"
        )
        db.session.add(missed_slot)
        db.session.commit()

        # Evaluate recommendations
        res = SmartRecoveryService.evaluate_recommendations(test_user_id)
        assert res["threats_count"] >= 2
        assert len(res["strategies"]) >= 1

        strategy_names = [s["name"] for s in res["strategies"]]
        assert any("Schedule Shift" in name or "Resume" in name or "Clean Slate" in name for name in strategy_names)

        # Verify strategy is deterministic and explainable
        strat = res["strategies"][0]
        assert "rationale" in strat
        assert "actions" in strat
        assert len(strat["actions"]) > 0
