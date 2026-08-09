import pytest
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.runtime_outbox import RuntimeOutboxEvent
from services.runtime.repository import RuntimeRepository
from interfaces.activity_interface import ActivityType
from datetime import datetime, timezone
import uuid

def test_runtime_repository_save_transaction(app):
    """Test the 6-step transaction lifecycle within the repository."""
    with app.app_context():
        # Setup mock data
        user_id = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())
        
        state_id = str(uuid.uuid4())
        
        state = RuntimeState(
            id=state_id,
            user_id=user_id,
            entity_type=ActivityType.TASK.value,
            entity_id=entity_id,
            status='RUNNING'
        )
        
        session = RuntimeSession(
            runtime_state_id=state_id,
            started_at=datetime.now(timezone.utc),
            planned_duration_sec=1800
        )
        
        events = [{
            'event_type': 'ActivityStarted',
            'payload': {'entity_id': entity_id, 'type': 'TASK'}
        }]
        
        # Save through repository
        RuntimeRepository.save(state, session, events)
        
        # Verify persistence
        saved_state = RuntimeState.query.get(state.id)
        assert saved_state is not None
        assert saved_state.status == 'RUNNING'
        
        saved_session = RuntimeSession.query.filter_by(runtime_state_id=state.id).first()
        assert saved_session is not None
        assert saved_session.planned_duration_sec == 1800
        
        outbox_event = RuntimeOutboxEvent.query.filter_by(event_type='ActivityStarted').first()
        assert outbox_event is not None
        assert outbox_event.payload['entity_id'] == entity_id
        assert outbox_event.dispatched is False
        
        # Verify active state retrieval
        active = RuntimeRepository.get_active_state_for_entity(ActivityType.TASK.value, entity_id)
        assert active is not None
        assert active.id == state.id
