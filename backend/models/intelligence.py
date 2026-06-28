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
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_accountability_user'), nullable=True, index=True)
    
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
            "user_id": self.user_id,
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
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_coachreport_user'), nullable=True, index=True)
    
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
            "user_id": self.user_id,
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
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_reflection_user'), nullable=True, index=True)
    
    achievements = db.Column(db.JSON, nullable=True)
    missed_opportunities = db.Column(db.JSON, nullable=True)
    lessons_learned = db.Column(db.JSON, nullable=True)
    tomorrow_priorities = db.Column(db.JSON, nullable=True)
    daily_summary = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievements": self.achievements,
            "missed_opportunities": self.missed_opportunities,
            "lessons_learned": self.lessons_learned,
            "tomorrow_priorities": self.tomorrow_priorities,
            "daily_summary": self.daily_summary,
            "created_at": self.created_at.isoformat()
        }


class ExecutionProfile(db.Model):
    __tablename__ = "execution_profiles"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_executionprofile_user'), nullable=True, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    momentum_score = db.Column(db.Integer, default=50) # 0-100
    burnout_risk = db.Column(db.Integer, default=10) # 0-100
    consistency_score = db.Column(db.Integer, default=50) # 0-100
    preferred_chunk_size = db.Column(db.Integer, default=60) # minutes
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "updated_at": self.updated_at.isoformat(),
            "momentum_score": self.momentum_score,
            "burnout_risk": self.burnout_risk,
            "consistency_score": self.consistency_score,
            "preferred_chunk_size": self.preferred_chunk_size
        }

class WeeklyReview(db.Model):
    __tablename__ = "weekly_reviews"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_weeklyreview_user'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    tasks_completed = db.Column(db.Integer, default=0)
    tasks_overdue = db.Column(db.Integer, default=0)
    ai_feedback = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "tasks_completed": self.tasks_completed,
            "tasks_overdue": self.tasks_overdue,
            "ai_feedback": self.ai_feedback
        }

class CommandLog(db.Model):
    __tablename__ = "command_logs"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', name='fk_commandlog_user'), nullable=True, index=True)
    source = db.Column(db.String(50), nullable=False) # e.g., "voice", "vision", "document"
    transcript = db.Column(db.Text, nullable=False)
    detected_intent = db.Column(db.String(100), nullable=True)
    confidence_score = db.Column(db.Float, default=0.0)
    execution_outcome = db.Column(db.String(100), nullable=True) # e.g., "success", "gemini_fallback", "user_corrected"
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "source": self.source,
            "transcript": self.transcript,
            "detected_intent": self.detected_intent,
            "confidence_score": self.confidence_score,
            "execution_outcome": self.execution_outcome,
            "created_at": self.created_at.isoformat()
        }

