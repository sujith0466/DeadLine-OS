"""
DeadlineOS Business OS — Workspace Invitation Model
===================================================
SQLAlchemy ORM model for `business_workspace_invitations`.
Tracks invitations to business workspaces with secure random tokens.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class WorkspaceInvitation(db.Model):
    """
    Represents an invitation sent to a user/email to join a Business Workspace with an assigned RBAC role.
    """
    __tablename__ = 'business_workspace_invitations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(db.String(36), db.ForeignKey('business_workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='MEMBER')
    token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    status = db.Column(db.String(20), nullable=False, default='PENDING')  # PENDING, ACCEPTED, EXPIRED, REVOKED
    invited_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_biz_inv_ws_email_status', 'workspace_id', 'email', 'status'),
    )

    workspace = db.relationship('Workspace', backref=db.backref('invitations', lazy=True, cascade='all, delete-orphan'))
    invited_by = db.relationship('User', foreign_keys=[invited_by_user_id])

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return now > exp

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'workspace_name': self.workspace.name if self.workspace else None,
            'email': self.email,
            'role': self.role,
            'status': 'EXPIRED' if (self.status == 'PENDING' and self.is_expired()) else self.status,
            'invited_by_user_id': self.invited_by_user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
