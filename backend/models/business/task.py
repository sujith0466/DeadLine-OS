"""
DeadlineOS Business OS — Business Task Model
============================================
SQLAlchemy ORM model for `business_tasks`.
Represents multi-tenant, assignable operational tasks and work allocation.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessTask(db.Model):
    """
    Represents an operational business task in a workspace.
    """
    __tablename__ = 'business_tasks'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assignee_member_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspace_members.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    created_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    priority = db.Column(db.String(20), nullable=False, default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    status = db.Column(db.String(20), nullable=False, default='TODO', index=True)  # TODO, IN_PROGRESS, BLOCKED, DONE, CANCELLED
    due_date = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    entity_id = db.Column(
        db.String(36),
        db.ForeignKey('business_entities.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    location_id = db.Column(
        db.String(36),
        db.ForeignKey('business_locations.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey('business_products.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    parent_task_id = db.Column(
        db.String(36),
        db.ForeignKey('business_tasks.id', ondelete='CASCADE'),
        nullable=True
    )
    category = db.Column(db.String(50), nullable=False, default='GENERAL')
    notes = db.Column(db.Text, nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.Index('idx_biz_tasks_ws_status', 'workspace_id', 'status'),
        db.Index('idx_biz_tasks_ws_due', 'workspace_id', 'due_date'),
        db.CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')", name='chk_biz_task_priority'),
        db.CheckConstraint("status IN ('TODO', 'IN_PROGRESS', 'BLOCKED', 'DONE', 'CANCELLED')", name='chk_biz_task_status'),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('tasks', lazy='dynamic', cascade='all, delete-orphan'))
    assignee = db.relationship('WorkspaceMember', foreign_keys=[assignee_member_id], backref=db.backref('assigned_tasks', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('created_business_tasks', lazy='dynamic'))
    completer = db.relationship('User', foreign_keys=[completed_by_user_id], backref=db.backref('completed_business_tasks', lazy='dynamic'))
    entity = db.relationship('BusinessEntity', backref=db.backref('tasks', lazy='dynamic'))
    location = db.relationship('BusinessLocation', backref=db.backref('tasks', lazy='dynamic'))
    product = db.relationship('BusinessProduct', backref=db.backref('tasks', lazy='dynamic'))
    subtasks = db.relationship('BusinessTask', backref=db.backref('parent_task', remote_side=[id]), lazy='dynamic')

    @property
    def is_overdue(self) -> bool:
        if self.status in ('DONE', 'CANCELLED') or not self.due_date:
            return False
        return datetime.now(timezone.utc) > (self.due_date if self.due_date.tzinfo else self.due_date.replace(tzinfo=timezone.utc))

    def serialize(self):
        assignee_user = self.assignee.user if self.assignee else None
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'title': self.title,
            'description': self.description,
            'assignee_member_id': self.assignee_member_id,
            'assignee_name': assignee_user.full_name if assignee_user and assignee_user.full_name else (assignee_user.email if assignee_user else None),
            'assignee_email': assignee_user.email if assignee_user else None,
            'created_by_user_id': self.created_by_user_id,
            'creator_name': self.creator.full_name if self.creator and self.creator.full_name else (self.creator.email if self.creator else None),
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_overdue': self.is_overdue,
            'entity_id': self.entity_id,
            'entity_name': self.entity.name if self.entity else None,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'parent_task_id': self.parent_task_id,
            'category': self.category,
            'notes': self.notes,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by_user_id': self.completed_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
