"""
DeadlineOS — Goal & Habit Models
================================
Tracks long-term execution, milestones, and daily habits.
"""

import uuid
from datetime import datetime, timezone
from database.db import db

class Goal(db.Model):
    __tablename__ = "goals"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_goal_user'), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    target_date = db.Column(db.String(50), nullable=True) # ISO format or readable
    status = db.Column(db.String(50), default="Active")
    progress_percentage = db.Column(db.Integer, default=0)
    health_score = db.Column(db.Integer, default=100) # Out of 100
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    archived = db.Column(db.Boolean, default=False)
    pinned = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(50), default="Medium")
    duration = db.Column(db.String(50), nullable=True)
    success_score = db.Column(db.Integer, default=0)

    milestones = db.relationship('Milestone', backref='goal', lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "target_date": self.target_date,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "health_score": self.health_score,
            "created_at": self.created_at.isoformat(),
            "archived": self.archived,
            "pinned": self.pinned,
            "priority": self.priority,
            "duration": self.duration,
            "success_score": self.success_score,
            "milestones": [m.to_dict() for m in self.milestones]
        }


class Milestone(db.Model):
    __tablename__ = "milestones"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_milestone_user'), nullable=True, index=True)
    goal_id = db.Column(db.String(36), db.ForeignKey('goals.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    target_date = db.Column(db.String(50), nullable=True)
    completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default="NOT_STARTED")
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goal_id": self.goal_id,
            "title": self.title,
            "target_date": self.target_date,
            "completed": self.completed,
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class Habit(db.Model):
    __tablename__ = "habits"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_habit_user'), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    frequency = db.Column(db.String(50), default="Daily")
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    completion_rate = db.Column(db.Integer, default=0) # Percentage
    momentum_score = db.Column(db.Integer, default=0) # 0-100 metric tracking consistency velocity
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="Active")
    archived = db.Column(db.Boolean, default=False)
    reminder_schedule = db.Column(db.String(50), nullable=True)
    target_duration = db.Column(db.String(50), nullable=True)
    last_checkin_date = db.Column(db.String(50), nullable=True)

    logs = db.relationship('HabitLog', backref='habit_ref', lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "category": self.category,
            "frequency": self.frequency,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "completion_rate": self.completion_rate,
            "momentum_score": self.momentum_score,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "archived": self.archived,
            "reminder_schedule": self.reminder_schedule,
            "target_duration": self.target_duration,
            "last_checkin_date": self.last_checkin_date,
            "logs": [l.to_dict() for l in self.logs]
        }

class HabitLog(db.Model):
    __tablename__ = "habit_logs"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_habitlog_user'), nullable=True, index=True)
    habit_id = db.Column(db.String(36), db.ForeignKey('habits.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False) # YYYY-MM-DD
    completed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "habit_id": self.habit_id,
            "date": self.date,
            "completed": self.completed,
            "created_at": self.created_at.isoformat()
        }
