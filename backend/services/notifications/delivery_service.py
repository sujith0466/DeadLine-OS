"""
DeadlineOS — Notification Delivery Reliability Service
======================================================
Manages notification dispatching, retry backoff, error isolation boundaries,
and dead-letter recording.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.notification import Notification, NotificationStatus
from services.notifications.repository import NotificationRepository
from utils.timezone import utc_now

logger = logging.getLogger(__name__)


class DeliveryService:
    """Robust delivery processor with error boundaries and exponential backoff."""

    MAX_RETRIES = 3
    BACKOFF_BASE_SECONDS = 30

    @classmethod
    def calculate_backoff(cls, retry_count: int) -> timedelta:
        """Calculates exponential backoff delay."""
        seconds = cls.BACKOFF_BASE_SECONDS * (2 ** retry_count)
        return timedelta(seconds=seconds)

    @classmethod
    def deliver_notification(cls, notification_id: str, sender_callable=None) -> Dict[str, Any]:
        """
        Attempts delivery of a notification.
        If sender_callable fails, increments retry_count or marks FAILED.
        """
        notif = NotificationRepository.get_by_id(notification_id)
        if not notif:
            return {"success": False, "error": "Notification not found"}

        # Idempotency guard
        if notif.status in (NotificationStatus.DELIVERED, NotificationStatus.ACKNOWLEDGED, NotificationStatus.DISMISSED):
            return {"success": True, "status": notif.status, "message": "Already delivered or terminal"}

        if notif.status in (NotificationStatus.FAILED, NotificationStatus.CANCELLED, NotificationStatus.EXPIRED):
            return {"success": False, "status": notif.status, "error": "Cannot deliver terminal notification"}

        try:
            # If external channel sender provided, invoke it
            if sender_callable:
                sender_callable(notif)

            # Mark delivered
            now = utc_now()
            notif.status = NotificationStatus.DELIVERED
            notif.delivered_at = now
            notif.updated_at = now
            db.session.commit()

            return {"success": True, "status": NotificationStatus.DELIVERED, "delivered_at": now.isoformat()}

        except Exception as e:
            logger.error(f"Delivery failed for notification {notification_id}: {e}")
            notif.retry_count = (notif.retry_count or 0) + 1
            now = utc_now()
            notif.updated_at = now

            if notif.retry_count >= cls.MAX_RETRIES:
                notif.status = NotificationStatus.FAILED
                db.session.commit()
                return {"success": False, "status": NotificationStatus.FAILED, "error": "Max retries exceeded"}
            else:
                # Reschedule with backoff
                delay = cls.calculate_backoff(notif.retry_count)
                notif.scheduled_at = now + delay
                notif.status = NotificationStatus.SCHEDULED
                db.session.commit()
                return {"success": False, "status": NotificationStatus.SCHEDULED, "retry_count": notif.retry_count, "next_retry": (now + delay).isoformat()}
