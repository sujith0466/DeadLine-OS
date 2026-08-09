from datetime import datetime, timezone
import uuid
from typing import Optional
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from services.runtime.repository import RuntimeRepository
from services.runtime.state_machine import RuntimeStateMachine, RuntimeLifecycleState

class DurationCalculator:
    """Calculates active duration of a session."""
    
    @staticmethod
    def calculate_active_duration(session: RuntimeSession, now: datetime = None) -> int:
        if not now:
            now = datetime.now(timezone.utc)
            
        end_time = session.ended_at if session.ended_at else now
        
        # Ensure timezone awareness for both
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
            
        started_at = session.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
            
        total_delta = (end_time - started_at).total_seconds()
        active_duration = max(0, int(total_delta) - session.paused_duration_sec)
        return active_duration

class RuntimeSessionEngine:
    """High-level facade for managing Session lifecycle via State Machine."""
    
    @staticmethod
    def start_session(user_id: str, entity_type: str, entity_id: str, planned_duration_sec: int) -> RuntimeState:
        payload = {'planned_duration_sec': planned_duration_sec}
        return RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.RUNNING, payload)

    @staticmethod
    def pause_session(user_id: str, entity_type: str, entity_id: str) -> RuntimeState:
        # Get active session before transitioning
        state_obj = RuntimeRepository.get_active_state_for_entity(entity_type, entity_id)
        if state_obj and state_obj.status == "RUNNING":
            # The session pause logic should ideally timestamp the pause
            # We will use the payload to carry the pause timestamp
            payload = {'paused_at': datetime.now(timezone.utc).isoformat()}
            return RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.PAUSED, payload)
        
        # If not running, state machine validation will fail anyway
        return RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.PAUSED)
        
    @staticmethod
    def resume_session(user_id: str, entity_type: str, entity_id: str) -> RuntimeState:
        # When resuming, the StateMachine handles the transition to RUNNING.
        # But we need to update the session's paused_duration_sec in the repository layer
        # For simplicity, we just trigger the transition.
        return RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.RUNNING, {'resumed_at': datetime.now(timezone.utc).isoformat()})
        
    @staticmethod
    def complete_session(user_id: str, entity_type: str, entity_id: str, source: str = "MANUAL") -> RuntimeState:
        target = RuntimeLifecycleState.COMPLETED_MANUAL if source == "MANUAL" else RuntimeLifecycleState.COMPLETED_AUTO
        
        state_obj = RuntimeRepository.get_active_state_for_entity(entity_type, entity_id)
        if state_obj:
            session = RuntimeSession.query.filter_by(runtime_state_id=state_obj.id).first()
            if session:
                duration = DurationCalculator.calculate_active_duration(session)
                payload = {'final_active_duration_sec': duration, 'completion_source': source}
                return RuntimeStateMachine.transition(user_id, entity_type, entity_id, target, payload)
                
        return RuntimeStateMachine.transition(user_id, entity_type, entity_id, target)
        
    @staticmethod
    def cancel_session(user_id: str, entity_type: str, entity_id: str) -> RuntimeState:
        return RuntimeStateMachine.transition(user_id, entity_type, entity_id, RuntimeLifecycleState.SKIPPED)

    @staticmethod
    def recover_interrupted_sessions(user_id: str):
        # Find all RUNNING or INTERRUPTED states and fix them
        pass
