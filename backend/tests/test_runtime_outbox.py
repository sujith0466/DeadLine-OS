import pytest
from services.runtime.outbox_dispatcher import OutboxDispatcher
from services.runtime.event_bus import activity_started
from models.runtime_outbox import RuntimeOutboxEvent
from database.db import db
import uuid
import json

def test_outbox_dispatcher_fires_signals(app):
    with app.app_context():
        # Insert a mock outbox event
        event_id = str(uuid.uuid4())
        event = RuntimeOutboxEvent(
            id=event_id,
            event_type='ActivityStarted',
            payload={'entity_id': '123', 'entity_type': 'TASK'}
        )
        db.session.add(event)
        db.session.commit()
        
        received = []
        def receiver(sender, payload, **kwargs):
            received.append(payload)
            
        # Connect the signal
        activity_started.connect(receiver)
        
        # Dispatch
        count = OutboxDispatcher.dispatch_pending_events()
        
        assert count == 1
        assert len(received) == 1
        assert received[0]['entity_id'] == '123'
        
        # Check that event is marked dispatched
        db_event = RuntimeOutboxEvent.query.get(event_id)
        assert db_event.dispatched is True
        
        # Cleanup signal
        activity_started.disconnect(receiver)
