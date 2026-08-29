"""
DeadlineOS Business OS — Audit Service
======================================
Provides append-only, immutable forensic audit logging.
"""

from database.db import db
from models.business import AuditEvent


class AuditService:
    @staticmethod
    def log_event(
        workspace_id: str,
        actor_user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        before_state: dict = None,
        after_state: dict = None,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuditEvent:
        """
        Creates and persists an immutable audit event record.
        """
        event = AuditEvent(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def get_events(
        workspace_id: str,
        entity_type: str = None,
        entity_id: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        """
        Queries audit events scoped strictly to the specified workspace_id.
        """
        query = AuditEvent.query.filter_by(workspace_id=workspace_id)
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        if entity_id:
            query = query.filter_by(entity_id=entity_id)

        total = query.count()
        events = query.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()
        return [e.serialize() for e in events], total
