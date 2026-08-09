import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def write_file(path, content):
    full_path = os.path.join(BACKEND_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

def main():
    print("--- Milestone 1: Creating State Machine ---")
    
    state_machine_code = '''from typing import List, Dict, Tuple
from enum import Enum

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
    """Raised when an invalid state transition is attempted."""
    pass

class RuntimeStateMachine:
    """Deterministic state machine for Runtime execution."""
    
    VALID_TRANSITIONS: Dict[RuntimeLifecycleState, List[RuntimeLifecycleState]] = {
        RuntimeLifecycleState.CREATED: [
            RuntimeLifecycleState.SCHEDULED
        ],
        RuntimeLifecycleState.SCHEDULED: [
            RuntimeLifecycleState.UPCOMING, 
            RuntimeLifecycleState.SKIPPED, 
            RuntimeLifecycleState.VACATION
        ],
        RuntimeLifecycleState.UPCOMING: [
            RuntimeLifecycleState.REMINDER_PENDING, 
            RuntimeLifecycleState.RUNNING, 
            RuntimeLifecycleState.SKIPPED
        ],
        RuntimeLifecycleState.REMINDER_PENDING: [
            RuntimeLifecycleState.RUNNING, 
            RuntimeLifecycleState.SKIPPED, 
            RuntimeLifecycleState.MISSED
        ],
        RuntimeLifecycleState.RUNNING: [
            RuntimeLifecycleState.PAUSED, 
            RuntimeLifecycleState.EXTENDED, 
            RuntimeLifecycleState.INTERRUPTED, 
            RuntimeLifecycleState.COMPLETED_MANUAL, 
            RuntimeLifecycleState.PENDING_CONFIRMATION
        ],
        RuntimeLifecycleState.PAUSED: [
            RuntimeLifecycleState.RUNNING, 
            RuntimeLifecycleState.COMPLETED_MANUAL, 
            RuntimeLifecycleState.SKIPPED
        ],
        RuntimeLifecycleState.INTERRUPTED: [
            RuntimeLifecycleState.RUNNING, 
            RuntimeLifecycleState.MISSED
        ],
        RuntimeLifecycleState.EXTENDED: [
            RuntimeLifecycleState.COMPLETED_MANUAL, 
            RuntimeLifecycleState.PENDING_CONFIRMATION
        ],
        RuntimeLifecycleState.PENDING_CONFIRMATION: [
            RuntimeLifecycleState.COMPLETED_AUTO, 
            RuntimeLifecycleState.RUNNING
        ],
        RuntimeLifecycleState.MISSED: [
            RuntimeLifecycleState.RECOVERED, 
            RuntimeLifecycleState.ARCHIVED
        ],
        RuntimeLifecycleState.RECOVERED: [
            RuntimeLifecycleState.RUNNING
        ],
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
'''
    write_file('services/runtime/state_machine.py', state_machine_code)
    
    test_code = '''import pytest
from services.runtime.state_machine import RuntimeStateMachine, RuntimeLifecycleState, IllegalTransitionError

def test_valid_transitions():
    """Test every legal transition documented in the architecture."""
    # Test a few critical paths
    RuntimeStateMachine.validate_transition("CREATED", RuntimeLifecycleState.SCHEDULED)
    RuntimeStateMachine.validate_transition("SCHEDULED", RuntimeLifecycleState.UPCOMING)
    RuntimeStateMachine.validate_transition("UPCOMING", RuntimeLifecycleState.RUNNING)
    RuntimeStateMachine.validate_transition("RUNNING", RuntimeLifecycleState.PAUSED)
    RuntimeStateMachine.validate_transition("PAUSED", RuntimeLifecycleState.RUNNING)
    RuntimeStateMachine.validate_transition("RUNNING", RuntimeLifecycleState.INTERRUPTED)
    RuntimeStateMachine.validate_transition("INTERRUPTED", RuntimeLifecycleState.RUNNING)
    RuntimeStateMachine.validate_transition("RUNNING", RuntimeLifecycleState.COMPLETED_MANUAL)

def test_illegal_transitions():
    """Test illegal transition protection."""
    # Cannot pause if not running
    with pytest.raises(IllegalTransitionError):
        RuntimeStateMachine.validate_transition("CREATED", RuntimeLifecycleState.PAUSED)
        
    with pytest.raises(IllegalTransitionError):
        RuntimeStateMachine.validate_transition("PAUSED", RuntimeLifecycleState.PAUSED)
        
    with pytest.raises(IllegalTransitionError):
        RuntimeStateMachine.validate_transition("COMPLETED_MANUAL", RuntimeLifecycleState.RUNNING)
        
    with pytest.raises(IllegalTransitionError):
        RuntimeStateMachine.validate_transition("UNKNOWN_STATE", RuntimeLifecycleState.RUNNING)

def test_full_branch_coverage():
    """Ensure all valid transitions defined in the state machine dict are actually allowed."""
    for current, targets in RuntimeStateMachine.VALID_TRANSITIONS.items():
        for target in targets:
            # Should not raise exception
            RuntimeStateMachine.validate_transition(current.value, target)
'''
    write_file('tests/test_runtime_state_machine.py', test_code)

    print("State Machine implementation and tests generated.")

if __name__ == "__main__":
    main()
