import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def write_file(path, content):
    full_path = os.path.join(BACKEND_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

def main():
    print("--- Milestone 3: Creating Outbox & Event Bus ---")
    
    event_bus_code = '''from blinker import Namespace

# Runtime Events Namespace
runtime_signals = Namespace()

activity_created = runtime_signals.signal('activity-created')
activity_scheduled = runtime_signals.signal('activity-scheduled')
activity_started = runtime_signals.signal('activity-started')
activity_paused = runtime_signals.signal('activity-paused')
activity_resumed = runtime_signals.signal('activity-resumed')
activity_extended = runtime_signals.signal('activity-extended')
activity_completed = runtime_signals.signal('activity-completed')
activity_skipped = runtime_signals.signal('activity-skipped')
activity_missed = runtime_signals.signal('activity-missed')
activity_interrupted = runtime_signals.signal('activity-interrupted')
activity_recovered = runtime_signals.signal('activity-recovered')

def get_signal_by_name(name: str):
    mapping = {
        'ActivityCreated': activity_created,
        'ActivityScheduled': activity_scheduled,
        'ActivityStarted': activity_started,
        'ActivityPaused': activity_paused,
        'ActivityResumed': activity_resumed,
        'ActivityExtended': activity_extended,
        'ActivityCompleted': activity_completed,
        'ActivitySkipped': activity_skipped,
        'ActivityMissed': activity_missed,
        'ActivityInterrupted': activity_interrupted,
        'ActivityRecovered': activity_recovered,
        'TransitionedToRUNNING': activity_started,
        'TransitionedToPAUSED': activity_paused,
        'TransitionedToCOMPLETED_MANUAL': activity_completed,
        'TransitionedToCOMPLETED_AUTO': activity_completed,
        'TransitionedToSKIPPED': activity_skipped,
        'TransitionedToMISSED': activity_missed,
        'TransitionedToINTERRUPTED': activity_interrupted,
        'TransitionedToSCHEDULED': activity_scheduled
    }
    return mapping.get(name)
'''
    write_file('services/runtime/event_bus.py', event_bus_code)

    dispatcher_code = '''from models.runtime_outbox import RuntimeOutboxEvent
from services.runtime.event_bus import get_signal_by_name
from database.db import db
import logging

logger = logging.getLogger(__name__)

class OutboxDispatcher:
    """Dispatches events safely from the outbox table to the event bus."""
    
    @staticmethod
    def dispatch_pending_events():
        # Query un-dispatched events
        pending_events = RuntimeOutboxEvent.query.filter_by(dispatched=False).order_by(RuntimeOutboxEvent.created_at.asc()).all()
        
        dispatched_count = 0
        for event in pending_events:
            signal = get_signal_by_name(event.event_type)
            if signal:
                try:
                    # Fire the signal
                    signal.send(event, payload=event.payload)
                    event.dispatched = True
                    dispatched_count += 1
                except Exception as e:
                    logger.error(f"Failed to dispatch event {event.id}: {e}")
            else:
                logger.warning(f"No signal mapped for event type: {event.event_type}")
                # Mark dispatched anyway to avoid poison pills, or leave for manual fix
                event.dispatched = True 
                
        if dispatched_count > 0:
            db.session.commit()
            
        return dispatched_count
'''
    write_file('services/runtime/outbox_dispatcher.py', dispatcher_code)
    
    test_code = '''import pytest
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
'''
    write_file('tests/test_runtime_outbox.py', test_code)

    print("Outbox & Event Bus logic generated.")

if __name__ == "__main__":
    main()
