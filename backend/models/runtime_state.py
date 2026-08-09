import uuid
from datetime import datetime, timezone
from database.db import db
from interfaces.activity_interface import ActivityType

class RuntimeState(db.Model):
    __tablename__ = "runtime_states"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True) # Represents ActivityType Enum
    entity_id = db.Column(db.String(36), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False) # e.g. RUNNING, INTERRUPTED
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_runtime_states_entity', 'entity_type', 'entity_id'),
        db.Index('idx_runtime_states_user_active', 'user_id', 'status'),
    )
