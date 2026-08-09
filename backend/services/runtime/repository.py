from typing import Optional, List, Dict
from models.runtime_state import RuntimeState
from models.runtime_session import RuntimeSession
from models.runtime_outbox import RuntimeOutboxEvent
from database.db import db
from datetime import datetime, timezone

class RuntimeRepository:
    """The ONLY persistence layer used by the Runtime Engine."""

    @staticmethod
    def get_state(runtime_id: str) -> Optional[RuntimeState]:
        return RuntimeState.query.get(runtime_id)
        
    @staticmethod
    def get_latest_state_for_entity(entity_type: str, entity_id: str) -> Optional[RuntimeState]:
        return RuntimeState.query.filter_by(entity_type=entity_type, entity_id=entity_id).order_by(RuntimeState.updated_at.desc()).first()
        
    @staticmethod
    def get_active_state_for_entity(entity_type: str, entity_id: str) -> Optional[RuntimeState]:
        return RuntimeState.query.filter_by(entity_type=entity_type, entity_id=entity_id).filter(
            RuntimeState.status.in_(['RUNNING', 'PAUSED', 'INTERRUPTED'])
        ).first()

    @staticmethod
    def save(state: RuntimeState, session: Optional[RuntimeSession], events: List[Dict]) -> None:
        """
        Executes the strict 6-step transaction lifecycle for Runtime execution.
        1. (Validation done prior to call)
        2. Update RuntimeState
        3. Update RuntimeSession
        4. Write RuntimeOutboxEvent
        5. Commit Database Transaction
        6. (Publish to Bus handled externally by EventBus after successful save)
        """
        try:
            db.session.add(state)
            if session:
                db.session.add(session)
            
            for event_payload in events:
                outbox_event = RuntimeOutboxEvent(
                    event_type=event_payload.get('event_type'),
                    payload=event_payload.get('payload', {}),
                    dispatched=False
                )
                db.session.add(outbox_event)
                
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
