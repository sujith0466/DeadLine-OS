import pytest
from datetime import datetime, timezone, timedelta
from services.runtime.session_engine import DurationCalculator
from models import *
from models.runtime_session import RuntimeSession
import uuid

def test_duration_calculator_running_session(app):
    now = datetime.now(timezone.utc)
    started_at = now - timedelta(minutes=30)
    
    session = RuntimeSession(
        id=str(uuid.uuid4()),
        runtime_state_id=str(uuid.uuid4()),
        started_at=started_at,
        paused_duration_sec=0,
        planned_duration_sec=1800
    )
    
    duration = DurationCalculator.calculate_active_duration(session, now)
    assert duration == 1800

def test_duration_calculator_paused_session(app):
    now = datetime.now(timezone.utc)
    started_at = now - timedelta(minutes=45)
    
    session = RuntimeSession(
        id=str(uuid.uuid4()),
        runtime_state_id=str(uuid.uuid4()),
        started_at=started_at,
        paused_duration_sec=15 * 60, # 15 minutes paused
        planned_duration_sec=1800
    )
    
    duration = DurationCalculator.calculate_active_duration(session, now)
    assert duration == 1800

def test_duration_calculator_ended_session(app):
    now = datetime.now(timezone.utc)
    started_at = now - timedelta(minutes=60)
    ended_at = now - timedelta(minutes=15)
    
    session = RuntimeSession(
        id=str(uuid.uuid4()),
        runtime_state_id=str(uuid.uuid4()),
        started_at=started_at,
        ended_at=ended_at,
        paused_duration_sec=5 * 60,
        planned_duration_sec=1800
    )
    
    # Passing a future 'now' shouldn't affect an ended session
    duration = DurationCalculator.calculate_active_duration(session, now)
    # Total time = 45 mins. Paused = 5 mins. Active = 40 mins = 2400 sec.
    assert duration == 2400
