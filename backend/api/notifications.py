import logging
import traceback
from flask import Blueprint, jsonify, request
from services.notification_service import NotificationService
from utils.auth import require_auth

logger = logging.getLogger(__name__)
notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications", methods=["GET"])
@require_auth
def get_notifications():
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
        unread_only = request.args.get("unread_only", "false").lower() == "true"
        category = request.args.get("category", None)
        
        result = NotificationService.get_notifications(
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            category=category
        )
        
        return jsonify({
            "success": True,
            "data": result
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch notifications: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": "An unexpected server error occurred while fetching notifications."
        }), 500

@notifications_bp.route("/notifications/<notification_id>/read", methods=["PUT", "POST"])
@require_auth
def mark_read(notification_id):
    try:
        success = NotificationService.mark_as_read(notification_id)
        if success:
            return jsonify({"success": True}), 200
        return jsonify({"success": False, "error": "Notification not found"}), 404
    except Exception as e:
        logger.error(f"Failed to mark notification read: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@notifications_bp.route("/notifications/read-all", methods=["PUT", "POST"])
@require_auth
def mark_all_read():
    try:
        success = NotificationService.mark_all_as_read()
        return jsonify({"success": success}), 200
    except Exception as e:
        logger.error(f"Failed to mark all read: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@notifications_bp.route("/notifications/clear", methods=["DELETE"])
@require_auth
def clear_all():
    try:
        success = NotificationService.clear_all()
        return jsonify({"success": success}), 200
    except Exception as e:
        logger.error(f"Failed to clear notifications: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@notifications_bp.route("/notifications/<notification_id>", methods=["DELETE"])
@require_auth
def delete_notification(notification_id):
    try:
        success = NotificationService.delete_notification(notification_id)
        if success:
            return jsonify({"success": True}), 200
        return jsonify({"success": False, "error": "Notification not found"}), 404
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
