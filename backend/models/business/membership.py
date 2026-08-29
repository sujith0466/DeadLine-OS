"""
DeadlineOS Business OS — Workspace Member Model
===============================================
SQLAlchemy ORM model for `business_workspace_members`.
Maps users to workspaces with 5-tier RBAC roles.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class WorkspaceMember(db.Model):
    """
    Represents a user membership in a business workspace with assigned RBAC role.
    """
    __tablename__ = 'business_workspace_members'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='MEMBER')
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('workspace_id', 'user_id', name='uq_biz_ws_member'),
        db.Index('idx_biz_ws_member_user_status', 'user_id', 'status'),
    )

    user = db.relationship('User', backref=db.backref('workspace_memberships', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'user_id': self.user_id,
            'role': self.role,
            'status': self.status,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': {
                'id': self.user.id if self.user else self.user_id,
                'email': self.user.email if self.user else None,
                'full_name': self.user.full_name if self.user else None,
            } if self.user else None
        }
