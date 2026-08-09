import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def write_file(path, content):
    full_path = os.path.join(BACKEND_DIR, path)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated: {path}")

def main():
    print("--- Milestone 1: Extending State Machine ---")
    
    state_machine_code = '''from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime, timezone
import uuid
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from services.runtime.repository import RuntimeRepository

class RuntimeLifecycleState(Enum):
    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
    UPCOMING = "UPCOMING"
    REMINDER_PENDING = "REMINDER_PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    EXTENDED = "EXTENDED"
    INTERRUPTED = "INTERRUPTED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    COMPLETED_MANUAL = "COMPLETED_MANUAL"
    COMPLETED_AUTO = "COMPLETED_AUTO"
    SKIPPED = "SKIPPED"
    MISSED = "MISSED"
    RECOVERED = "RECOVERED"
    VACATION = "VACATION"
    ARCHIVED = "ARCHIVED"

class IllegalTransitionError(Exception):
    pass

class RuntimeStateMachine:
    VALID_TRANSITIONS: Dict[RuntimeLifecycleState, List[RuntimeLifecycleState]] = {
        RuntimeLifecycleState.CREATED: [RuntimeLifecycleState.SCHEDULED],
        RuntimeLifecycleState.SCHEDULED: [RuntimeLifecycleState.UPCOMING, RuntimeLifecycleState.SKIPPED, RuntimeLifecycleState.VACATION],
        RuntimeLifecycleState.UPCOMING: [RuntimeLifecycleState.REMINDER_PENDING, RuntimeLifecycleState.RUNNING, RuntimeLifecycleState.SKIPPED],
        RuntimeLifecycleState.REMINDER_PENDING: [RuntimeLifecycleState.RUNNING, RuntimeLifecycleState.SKIPPED, RuntimeLifecycleState.MISSED],
        RuntimeLifecycleState.RUNNING: [RuntimeLifecycleState.PAUSED, RuntimeLifecycleState.EXTENDED, RuntimeLifecycleState.INTERRUPTED, RuntimeLifecycleState.COMPLETED_MANUAL, RuntimeLifecycleState.PENDING_CONFIRMATION],
        RuntimeLifecycleState.PAUSED: [RuntimeLifecycleState.RUNNING, RuntimeLifecycleState.COMPLETED_MANUAL, RuntimeLifecycleState.SKIPPED],
        RuntimeLifecycleState.INTERRUPTED: [RuntimeLifecycleState.RUNNING, RuntimeLifecycleState.MISSED],
        RuntimeLifecycleState.EXTENDED: [RuntimeLifecycleState.COMPLETED_MANUAL, RuntimeLifecycleState.PENDING_CONFIRMATION],
        RuntimeLifecycleState.PENDING_CONFIRMATION: [RuntimeLifecycleState.COMPLETED_AUTO, RuntimeLifecycleState.RUNNING],
        RuntimeLifecycleState.MISSED: [RuntimeLifecycleState.RECOVERED, RuntimeLifecycleState.ARCHIVED],
        RuntimeLifecycleState.RECOVERED: [RuntimeLifecycleState.RUNNING],
        RuntimeLifecycleState.VACATION: [],
        RuntimeLifecycleState.COMPLETED_MANUAL: [],
        RuntimeLifecycleState.COMPLETED_AUTO: [],
        RuntimeLifecycleState.SKIPPED: [],
        RuntimeLifecycleState.ARCHIVED: []
    }

    @staticmethod
    def validate_transition(current_state_str: str, target_state: RuntimeLifecycleState) -> None:
        try:
            current = RuntimeLifecycleState(current_state_str)
        except ValueError:
            raise IllegalTransitionError(f"Unknown current state: {current_state_str}")
            
        allowed = RuntimeStateMachine.VALID_TRANSITIONS.get(current, [])
        if target_state not in allowed:
            raise IllegalTransitionError(f"Cannot transition from {current.value} to {target_state.value}")

    @staticmethod
    def transition(user_id: str, entity_type: str, entity_id: str, target_state: RuntimeLifecycleState, payload: dict = None) -> RuntimeState:
        """Executes a state transition and persists it through the RuntimeRepository."""
        
        # 1. Get current state (or assume CREATED if not exists)
        current_state_obj = RuntimeRepository.get_active_state_for_entity(entity_type, entity_id)
        current_state_str = current_state_obj.status if current_state_obj else RuntimeLifecycleState.CREATED.value

        # 2. Validate
        if current_state_obj:
            RuntimeStateMachine.validate_transition(current_state_str, target_state)
            state_to_save = current_state_obj
            state_to_save.status = target_state.value
        else:
            if target_state != RuntimeLifecycleState.CREATED:
                RuntimeStateMachine.validate_transition(RuntimeLifecycleState.CREATED.value, target_state)
            
            # Fresh state
            state_to_save = RuntimeState(
                id=str(uuid.uuid4()),
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                status=target_state.value
            )

        # 3. Handle Session logic based on transition
        session_to_save = None
        if target_state == RuntimeLifecycleState.RUNNING and current_state_str != RuntimeLifecycleState.PAUSED.value and current_state_str != RuntimeLifecycleState.INTERRUPTED.value:
            # Start new session
            session_to_save = RuntimeSession(
                id=str(uuid.uuid4()),
                runtime_state_id=state_to_save.id,
                started_at=datetime.now(timezone.utc),
                planned_duration_sec=payload.get('planned_duration_sec', 1800) if payload else 1800
            )

        # 4. Generate Event
        events = [{
            'event_type': f"TransitionedTo{target_state.value}",
            'payload': {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'previous_state': current_state_str,
                'new_state': target_state.value,
                **(payload or {})
            }
        }]

        # 5. Persist
        RuntimeRepository.save(state_to_save, session_to_save, events)
        return state_to_save

    @staticmethod
    def recover_interrupted(user_id: str) -> None:
        """
        Recovers activities that were INTERRUPTED (e.g. server crash).
        In a real scenario, this recalculates active duration.
        """
        # A full implementation would query all INTERRUPTED states for the user
        pass
'''
    write_file('services/runtime/state_machine.py', state_machine_code)
    
    test_code = '''import pytest
from services.runtime.state_machine import RuntimeStateMachine, RuntimeLifecycleState, IllegalTransitionError
from models.runtime_state import RuntimeState
import uuid

def test_valid_transitions():
    RuntimeStateMachine.validate_transition("CREATED", RuntimeLifecycleState.SCHEDULED)
    RuntimeStateMachine.validate_transition("SCHEDULED", RuntimeLifecycleState.UPCOMING)
    RuntimeStateMachine.validate_transition("UPCOMING", RuntimeLifecycleState.RUNNING)
    RuntimeStateMachine.validate_transition("RUNNING", RuntimeLifecycleState.PAUSED)
    RuntimeStateMachine.validate_transition("PAUSED", RuntimeLifecycleState.RUNNING)
    RuntimeStateMachine.validate_transition("RUNNING", RuntimeLifecycleState.INTERRUPTED)
    RuntimeStateMachine.validate_transition("INTERRUPTED", RuntimeLifecycleState.RUNNING)
    RuntimeStateMachine.validate_transition("RUNNING", RuntimeLifecycleState.COMPLETED_MANUAL)

def test_illegal_transitions():
    with pytest.raises(IllegalTransitionError):
        RuntimeStateMachine.validate_transition("CREATED", RuntimeLifecycleState.PAUSED)
        
    with pytest.raises(IllegalTransitionError):
        RuntimeStateMachine.validate_transition("PAUSED", RuntimeLifecycleState.PAUSED)
        
    with pytest.raises(IllegalTransitionError):
        RuntimeStateMachine.validate_transition("COMPLETED_MANUAL", RuntimeLifecycleState.RUNNING)

def test_transition_persistence(app):
    with app.app_context():
        user_id = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())
        
        # Fresh state transition
        state = RuntimeStateMachine.transition(user_id, "TASK", entity_id, RuntimeLifecycleState.CREATED)
        assert state.status == "CREATED"
        
        # Valid transition
        state = RuntimeStateMachine.transition(user_id, "TASK", entity_id, RuntimeLifecycleState.SCHEDULED)
        assert state.status == "SCHEDULED"
        
        # Illegal transition
        with pytest.raises(IllegalTransitionError):
            RuntimeStateMachine.transition(user_id, "TASK", entity_id, RuntimeLifecycleState.RUNNING)
'''
    write_file('tests/test_runtime_state_machine.py', test_code)

    print("State Machine persistence logic generated.")

if __name__ == "__main__":
    main()
