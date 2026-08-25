"""
DeadlineOS — Notification Repository
====================================
Data access and transactional persistence for notifications.
Guarantees deduplication, query filtering, and status transitions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from utils.timezone import utc_now


class NotificationRepository:
    """Repository for managing notification persistence."""

    @classmethod
    def get_by_id(cls, notification_id: str) -> Optional[Notification]:
        return db.session.get(Notification, notification_id)

    @classmethod
    def get_by_deduplication_key(cls, user_id: str, dedup_key: str) -> Optional[Notification]:
        """Find an existing notification with the same deduplication key."""
        if not dedup_key:
            return None
        return Notification.query.filter_by(
            user_id=user_id,
            deduplication_key=dedup_key
        ).first()

    @classmethod
    def save(cls, notification: Notification) -> Notification:
        """Persists a notification record."""
        db.session.add(notification)
        db.session.commit()
        return notification

    @classmethod
    def get_user_notifications(
        cls,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Notification]:
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(read=False)
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)

        return (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @classmethod
    def count_unread(cls, user_id: str) -> int:
        return Notification.query.filter_by(user_id=user_id, read=False).count()

    @classmethod
    def update_status(cls, notification_id: str, new_status: str, user_id: Optional[str] = None) -> Optional[Notification]:
        notif = cls.get_by_id(notification_id)
        if not notif or (user_id and notif.user_id != user_id):
            return None

        notif.status = new_status
        now = utc_now()
        notif.updated_at = now
        
        if new_status == NotificationStatus.DELIVERED and not notif.delivered_at:
            notif.delivered_at = now
        elif new_status == NotificationStatus.ACKNOWLEDGED:
            notif.acknowledged_at = now
            notif.read = True
        elif new_status == NotificationStatus.DISMISSED:
            notif.dismissed_at = now
            notif.read = True

        db.session.commit()
        return notif

    @classmethod
    def delete(cls, notification_id: str, user_id: Optional[str] = None) -> bool:
        notif = cls.get_by_id(notification_id)
        if not notif or (user_id and notif.user_id != user_id):
            return False
        db.session.delete(notif)
        db.session.commit()
        return True

    @classmethod
    def cancel_pending_for_entity(cls, user_id: str, entity_id: str) -> int:
        """Cancels all pending/scheduled notifications for an entity when rescheduled or deleted."""
        cancelled = (
            Notification.query.filter_by(user_id=user_id, entity_id=entity_id)
            .filter(Notification.status.in_([NotificationStatus.PENDING, NotificationStatus.SCHEDULED]))
            .all()
        )
        count = len(cancelled)
        for n in cancelled:
            n.status = NotificationStatus.CANCELLED
            n.updated_at = utc_now()
        if count > 0:
            db.session.commit()
        return count
