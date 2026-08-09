from models.runtime_outbox import RuntimeOutboxEvent
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
