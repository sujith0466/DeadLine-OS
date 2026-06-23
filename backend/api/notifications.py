import logging
from flask import Blueprint, jsonify
from services.intervention_engine import InterventionEngine
from services.orchestrator import OrchestratorService

logger = logging.getLogger(__name__)
notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """
    Returns aggregated notifications for the Notification Center.
    Includes Interventions and high-priority Orchestrator events.
    """
    notifications = []
    
    # 1. Active Interventions
    interventions = InterventionEngine.get_active_interventions()
    for inv in interventions:
        notifications.append({
            "id": inv["id"],
            "title": f"Intervention: {inv['type'].title()}",
            "message": inv["message"],
            "severity": inv["severity"].lower(),
            "timestamp": inv["created_at"],
            "read": False,
            "type": "intervention"
        })
        
    # 2. Orchestrator Feed Warnings/Errors
    feed = OrchestratorService.get_feed()
    for ev in feed[:20]: # Check recent
        if ev.get("status") in ["warning", "error"]:
            notifications.append({
                "id": f"event-{ev['id']}",
                "title": f"Agent Alert: {ev['agent']}",
                "message": ev["action"],
                "severity": "high" if ev["status"] == "error" else "medium",
                "timestamp": ev["timestamp"],
                "read": False,
                "type": "system"
            })
            
    # Sort by timestamp descending
    notifications.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return jsonify({
        "status": "success",
        "data": {
            "notifications": notifications,
            "unread_count": len(notifications)
        }
    }), 200
