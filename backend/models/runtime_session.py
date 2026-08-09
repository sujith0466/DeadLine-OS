import uuid
from datetime import datetime
from database.db import db

class RuntimeSession(db.Model):
    __tablename__ = "runtime_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    runtime_state_id = db.Column(db.String(36), db.ForeignKey("runtime_states.id"), nullable=False, index=True)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    planned_duration_sec = db.Column(db.Integer, nullable=False)
    paused_duration_sec = db.Column(db.Integer, nullable=False, default=0)
    completion_source = db.Column(db.String(20), nullable=True) # Manual, Auto, Timeout
