"""
DeadlineOS — Personal Intelligence Models
=========================================
SQLAlchemy models for persisting outputs of the Accountability,
Coach, and Reflection agents.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class AccountabilityMetrics(db.Model):
    __tablename__ = "accountability_metrics"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(50), nullable=False, default="default")
    
    completion_rate = db.Column(db.Float, default=0.0)
    consistency_score = db.Column(db.Float, default=0.0)
    procrastination_score = db.Column(db.Float, default=0.0)
    productivity_score = db.Column(db.Float, default=0.0)
    risk_profile = db.Column(db.String(100), nullable=True)
    
    key_findings = db.Column(db.JSON, nullable=True)
    recommendations = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "completion_rate": self.completion_rate,
            "consistency_score": self.consistency_score,
            "procrastination_score": self.procrastination_score,
            "productivity_score": self.productivity_score,
            "risk_profile": self.risk_profile,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat()
        }


class CoachReport(db.Model):
    __tablename__ = "coach_reports"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(50), nullable=False, default="default")
    
    strengths = db.Column(db.JSON, nullable=True)
    weaknesses = db.Column(db.JSON, nullable=True)
    insights = db.Column(db.JSON, nullable=True)
    improvement_plan = db.Column(db.JSON, nullable=True)
    weekly_challenge = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "insights": self.insights,
            "improvement_plan": self.improvement_plan,
            "weekly_challenge": self.weekly_challenge,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat()
        }


class ReflectionReport(db.Model):
    __tablename__ = "reflection_reports"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(50), nullable=False, default="default")
    
    achievements = db.Column(db.JSON, nullable=True)
    missed_opportunities = db.Column(db.JSON, nullable=True)
    lessons_learned = db.Column(db.JSON, nullable=True)
    tomorrow_priorities = db.Column(db.JSON, nullable=True)
    daily_summary = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "achievements": self.achievements,
            "missed_opportunities": self.missed_opportunities,
            "lessons_learned": self.lessons_learned,
            "tomorrow_priorities": self.tomorrow_priorities,
            "daily_summary": self.daily_summary,
            "created_at": self.created_at.isoformat()
        }
