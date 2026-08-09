import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def write_file(path, content):
    full_path = os.path.join(BACKEND_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

def main():
    print("--- Milestone 0: Creating Runtime Models ---")
    
    activity_interface_code = '''from typing import Protocol
from enum import Enum

class ActivityType(Enum):
    TASK = "TASK"
    GOAL = "GOAL"
    HABIT = "HABIT"
    COURSE = "COURSE"
    WORKOUT = "WORKOUT"

class ActivityInterface(Protocol):
    """
    Any domain model (Task, Habit, Course) that can be executed must implement this interface 
    to provide the runtime with necessary metadata without leaking internal schemas.
    """
    def get_runtime_identity(self) -> str: ...
    def get_entity_type(self) -> ActivityType: ...
    def get_planned_duration(self) -> int: ... # seconds
    def can_be_executed(self) -> bool: ...
'''
    write_file('interfaces/activity_interface.py', activity_interface_code)
    
    runtime_state_code = '''import uuid
from datetime import datetime, timezone
from database.db import db
from interfaces.activity_interface import ActivityType

class RuntimeState(db.Model):
    __tablename__ = "runtime_states"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True) # Represents ActivityType Enum
    entity_id = db.Column(db.String(36), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False) # e.g. RUNNING, INTERRUPTED
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_runtime_states_entity', 'entity_type', 'entity_id'),
        db.Index('idx_runtime_states_user_active', 'user_id', 'status'),
    )
'''
    write_file('models/runtime_state.py', runtime_state_code)
    
    runtime_session_code = '''import uuid
from datetime import datetime
from database.db import db

class RuntimeSession(db.Model):
    __tablename__ = "runtime_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    runtime_state_id = db.Column(db.String(36), db.ForeignKey("runtime_states.id"), nullable=False, index=True)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    planned_duration_sec = db.Column(db.Integer, nullable=False)
    paused_duration_sec = db.Column(db.Integer, nullable=False, default=0)
    completion_source = db.Column(db.String(20), nullable=True) # Manual, Auto, Timeout
'''
    write_file('models/runtime_session.py', runtime_session_code)
    
    runtime_outbox_code = '''import uuid
from datetime import datetime, timezone
from database.db import db

class RuntimeOutboxEvent(db.Model):
    __tablename__ = "runtime_outbox_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    dispatched = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
'''
    write_file('models/runtime_outbox.py', runtime_outbox_code)

    print("Models created successfully.")

if __name__ == "__main__":
    main()
