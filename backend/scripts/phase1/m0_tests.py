import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def write_file(path, content):
    full_path = os.path.join(BACKEND_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

def main():
    print("--- Milestone 0: Creating Runtime Repository Tests ---")
    
    test_code = '''import pytest
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.runtime_outbox import RuntimeOutboxEvent
from services.runtime.repository import RuntimeRepository
from interfaces.activity_interface import ActivityType
from datetime import datetime, timezone
import uuid

def test_runtime_repository_save_transaction(app, db):
    """Test the 6-step transaction lifecycle within the repository."""
    with app.app_context():
        # Setup mock data
        user_id = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())
        
        state = RuntimeState(
            user_id=user_id,
            entity_type=ActivityType.TASK.value,
            entity_id=entity_id,
            status='RUNNING'
        )
        
        session = RuntimeSession(
            runtime_state_id=state.id,
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
'''
    write_file('tests/test_runtime_repository.py', test_code)

    print("Runtime Repository Tests created successfully.")

if __name__ == "__main__":
    main()
