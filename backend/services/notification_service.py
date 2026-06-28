from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from database.db import db
from models.notification import Notification
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def create_notification(
        title: str,
        description: str = None,
        severity: str = "info",
        priority: str = "info",
        module: str = None,
        entity_type: str = None,
        entity_id: str = None,
        action_url: str = None,
        icon: str = None,
        color: str = None,
        category: str = "System",
        user_id: str = None
    ) -> Notification:
        try:
            from flask import g
            uid = user_id or getattr(g, "user_id", None)
            notif = Notification(
                user_id=uid,
                title=title,
                description=description,
                severity=severity,
                priority=priority,
                module=module,
                entity_type=entity_type,
                entity_id=entity_id,
                action_url=action_url,
                icon=icon,
                color=color,
                category=category
            )
            db.session.add(notif)
            db.session.commit()
            return notif
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def get_notifications(
        limit: int = 100,
        offset: int = 0,
        unread_only: bool = False,
        category: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        query = Notification.query.filter_by(user_id=uid)
        
        if unread_only:
            query = query.filter_by(read=False)
        if category:
            query = query.filter_by(category=category)
            
        total = query.count()
        unread_count = Notification.query.filter_by(user_id=uid, read=False).count()
        
        notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "notifications": [n.to_dict() for n in notifications],
            "total": total,
            "unread_count": unread_count
        }

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str = None) -> bool:
        try:
            from flask import g
            uid = user_id or getattr(g, "user_id", None)
            notif = Notification.query.filter_by(user_id=uid, id=notification_id).first()
            if notif:
                notif.read = True
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def mark_all_as_read(user_id: str = None) -> bool:
        try:
            from flask import g
            uid = user_id or getattr(g, "user_id", None)
            db.session.query(Notification).filter_by(user_id=uid, read=False).update({"read": True})
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def clear_all(user_id: str = None) -> bool:
        try:
            from flask import g
            uid = user_id or getattr(g, "user_id", None)
            db.session.query(Notification).filter_by(user_id=uid).delete()
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to clear notifications: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def delete_notification(notification_id: str, user_id: str = None) -> bool:
        try:
            from flask import g
            uid = user_id or getattr(g, "user_id", None)
            notif = Notification.query.filter_by(user_id=uid, id=notification_id).first()
            if notif:
                db.session.delete(notif)
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            db.session.rollback()
            return False
