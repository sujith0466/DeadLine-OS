"""
DeadlineOS — Notifications API Blueprint (Phase 4)
===================================================
REST API endpoints for notification feeds, actions, confirmations, and dismissals.
"""

import logging
from flask import Blueprint, jsonify, request, g
from utils.auth import require_auth
from utils.responses import success_response, error_response
from services.notifications.repository import NotificationRepository
from services.notifications.action_router import ActionRouter

logger = logging.getLogger(__name__)
notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications", methods=["GET"])
@require_auth
def get_notifications():
    """Retrieve user notifications with optional filters."""
    try:
        limit = min(int(request.args.get("limit", 50)), 100)
        offset = int(request.args.get("offset", 0))
        unread_only = request.args.get("unread_only", "").lower() in ("true", "1")
        category = request.args.get("category")
        status = request.args.get("status")

        notifs = NotificationRepository.get_user_notifications(
            user_id=g.user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            status=status,
            category=category
        )
        unread_count = NotificationRepository.count_unread(g.user_id)

        return success_response("Notifications retrieved", {
            "notifications": [n.to_dict() for n in notifs],
            "total": len(notifs),
            "unread_count": unread_count
        })
    except Exception as e:
        logger.error(f"Failed to fetch notifications: {e}")
        return error_response("Failed to fetch notifications", status_code=500)


@notifications_bp.route("/notifications/<notification_id>/action", methods=["POST"])
@require_auth
def execute_notification_action(notification_id):
    """Execute an action on a notification (e.g. START_ACTIVITY, COMPLETE_ACTIVITY, DISMISS)."""
    data = request.get_json(silent=True) or {}
    action_type = data.get("action")
    payload = data.get("payload")

    if not action_type:
        return error_response("Action type is required", status_code=400)

    res = ActionRouter.handle_action(
        user_id=g.user_id,
        notification_id=notification_id,
        action_type=action_type,
        action_payload=payload
    )

    if not res.get("success"):
        return error_response(res.get("error", "Action failed"), status_code=400)

    return success_response("Action executed successfully", res)


@notifications_bp.route("/notifications/<notification_id>/read", methods=["PUT", "POST"])
@require_auth
def mark_read(notification_id):
    """Mark a specific notification as read / acknowledged."""
    notif = NotificationRepository.update_status(notification_id, "ACKNOWLEDGED", g.user_id)
    if not notif:
        return error_response("Notification not found", status_code=404)
    return success_response("Notification marked read", notif.to_dict())


@notifications_bp.route("/notifications/<notification_id>/dismiss", methods=["POST"])
@require_auth
def dismiss_notification(notification_id):
    """Dismiss a specific notification."""
    notif = NotificationRepository.update_status(notification_id, "DISMISSED", g.user_id)
    if not notif:
        return error_response("Notification not found", status_code=404)
    return success_response("Notification dismissed", notif.to_dict())


@notifications_bp.route("/notifications/read-all", methods=["PUT", "POST"])
@require_auth
def mark_all_read():
    """Mark all unread notifications as read."""
    unread = NotificationRepository.get_user_notifications(g.user_id, limit=200, unread_only=True)
    for n in unread:
        NotificationRepository.update_status(n.id, "ACKNOWLEDGED", g.user_id)
    return success_response("All notifications marked read")


@notifications_bp.route("/notifications/clear", methods=["DELETE"])
@require_auth
def clear_all():
    """Delete all notifications for user."""
    notifs = NotificationRepository.get_user_notifications(g.user_id, limit=500)
    for n in notifs:
        NotificationRepository.delete(n.id, g.user_id)
    return success_response("Notifications cleared")


@notifications_bp.route("/notifications/<notification_id>", methods=["DELETE"])
@require_auth
def delete_notification(notification_id):
    """Delete a single notification."""
    success = NotificationRepository.delete(notification_id, g.user_id)
    if not success:
        return error_response("Notification not found", status_code=404)
    return success_response("Notification deleted")
