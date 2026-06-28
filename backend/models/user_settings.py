"""
DeadlineOS — User Settings Model
================================
Stores configuration and preferences for a user using JSON columns for flexibility.
One-to-One relationship with the User model.
"""

from datetime import datetime, timezone
from database.db import db

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    # JSON columns for flexible settings mapping
    profile = db.Column(db.JSON, default=dict)
    appearance = db.Column(db.JSON, default=dict)
    notifications = db.Column(db.JSON, default=dict)
    planner = db.Column(db.JSON, default=dict)
    ai = db.Column(db.JSON, default=dict)
    security = db.Column(db.JSON, default=dict)
    
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('settings', uselist=False))

    def serialize(self):
        return {
            "user_id": self.user_id,
            "profile": self.profile or {},
            "appearance": self.appearance or {},
            "notifications": self.notifications or {},
            "planner": self.planner or {},
            "ai": self.ai or {},
            "security": self.security or {},
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_or_create(user_id):
        settings = UserSettings.query.get(user_id)
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        return settings
