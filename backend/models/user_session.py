"""
DeadlineOS — User Session Model
================================
Tracks active sessions, devices, and logins.
"""

from datetime import datetime, timezone
import uuid
from database.db import db

class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    browser = db.Column(db.String(100), nullable=True)
    os = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    login_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    is_current = db.Column(db.Boolean, default=False) # Helper for API representation, not strict DB truth

    user = db.relationship('User', backref=db.backref('sessions', lazy=True, cascade='all, delete-orphan'))

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "browser": self.browser or "Unknown Browser",
            "os": self.os or "Unknown OS",
            "location": self.location or "Unknown Location",
            "ip_address": self.ip_address or "Unknown IP",
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "is_current": getattr(self, 'is_current', False)
        }
