"""
DeadlineOS — Notification Action Router
=======================================
Routes confirmed notification user interactions to approved Runtime / Scheduling
service boundaries without allowing direct unauthorized database mutations.
"""

from typing import Dict, Any, Optional
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.repository import NotificationRepository
from services.runtime.session_engine import RuntimeSessionEngine
from utils.timezone import utc_now


class ActionRouter:
    """Dispatches user notification actions to authoritative services."""

    @classmethod
    def handle_action(
        cls,
        user_id: str,
        notification_id: str,
        action_type: str,
        action_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes an approved user notification action.
        Supported action types: 'START_ACTIVITY', 'COMPLETE_ACTIVITY', 'DISMISS', 'ACKNOWLEDGE'.
        """
        notif = NotificationRepository.get_by_id(notification_id)
        if not notif or notif.user_id != user_id:
            return {"success": False, "error": "Notification not found or unauthorized"}

        action_type_upper = (action_type or "").upper()
        result_data: Dict[str, Any] = {"action": action_type_upper}

        if action_type_upper == "START_ACTIVITY":
            entity_id = notif.entity_id or (action_payload.get("entity_id") if action_payload else None)
            entity_type = notif.entity_type or (action_payload.get("entity_type", "TASK") if action_payload else "TASK")
            if entity_id:
                try:
                    state = RuntimeSessionEngine.start_session(
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        planned_duration_sec=1800
                    )
                    result_data["runtime_state_id"] = state.id if state else None
                    result_data["status"] = "STARTED"
                except Exception as e:
                    return {"success": False, "error": f"Failed to start runtime session: {e}"}

            NotificationRepository.update_status(notification_id, NotificationStatus.ACKNOWLEDGED, user_id)

        elif action_type_upper == "COMPLETE_ACTIVITY":
            entity_id = notif.entity_id
            entity_type = notif.entity_type or "TASK"
            if entity_id:
                try:
                    state = RuntimeSessionEngine.complete_session(
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        source="NOTIFICATION"
                    )
                    result_data["status"] = "COMPLETED"
                except Exception as e:
                    return {"success": False, "error": f"Failed to complete runtime session: {e}"}

            NotificationRepository.update_status(notification_id, NotificationStatus.ACKNOWLEDGED, user_id)

        elif action_type_upper == "DISMISS":
            NotificationRepository.update_status(notification_id, NotificationStatus.DISMISSED, user_id)
            result_data["status"] = "DISMISSED"

        elif action_type_upper == "ACKNOWLEDGE":
            NotificationRepository.update_status(notification_id, NotificationStatus.ACKNOWLEDGED, user_id)
            result_data["status"] = "ACKNOWLEDGED"

        else:
            return {"success": False, "error": f"Unsupported action type: {action_type}"}

        return {"success": True, "result": result_data, "notification": notif.to_dict()}
