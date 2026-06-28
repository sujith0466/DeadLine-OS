"""
DeadlineOS — User Model
=========================
SQLAlchemy ORM model for the `users` table.
Stores user profile data and maps to Supabase Auth UUID.
"""

from datetime import datetime, timezone
from database.db import db

class User(db.Model):
    """
    Represents an authenticated user in DeadlineOS.
    The ID is a UUID string matching the Supabase auth.users UUID.
    """
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True) # Matches Supabase UUID
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=True)
    full_name = db.Column(db.String(255), nullable=True)
    avatar_url = db.Column(db.String(512), nullable=True)
    timezone = db.Column(db.String(100), default="UTC")
    country = db.Column(db.String(100), nullable=True)
    working_hours_start = db.Column(db.String(10), default="09:00")
    working_hours_end = db.Column(db.String(10), default="17:00")
    focus_hours_start = db.Column(db.String(10), nullable=True)
    focus_hours_end = db.Column(db.String(10), nullable=True)
    daily_capacity = db.Column(db.Float, default=8.0)
    preferred_planning_mode = db.Column(db.String(50), default="balanced")
    theme_preference = db.Column(db.String(20), default="system")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships mapped from other tables (e.g. tasks, goals)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "country": self.country,
            "working_hours": {
                "start": self.working_hours_start,
                "end": self.working_hours_end
            },
            "focus_hours": {
                "start": self.focus_hours_start,
                "end": self.focus_hours_end
            },
            "daily_capacity": self.daily_capacity,
            "preferred_planning_mode": self.preferred_planning_mode,
            "theme_preference": self.theme_preference,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
