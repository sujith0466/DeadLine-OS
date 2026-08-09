import pytest
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
