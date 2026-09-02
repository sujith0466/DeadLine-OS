"""
DeadlineOS Business OS — Operational Alerts REST API Endpoints (Phase C2.4)
===========================================================================
Endpoints for listing, evaluating, acknowledging, resolving, dismissing,
and converting operational alerts to actionable BusinessTasks.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.operational_alert_service import OperationalAlertService

alerts_bp = Blueprint('business_alerts', __name__)


@alerts_bp.route('', methods=['GET'])
@require_workspace('tasks:read')
def list_alerts():
    """
    Lists operational alerts for the active workspace.
    """
    status = request.args.get('status')
    severity = request.args.get('severity')
    entity_type = request.args.get('entity_type')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    try:
        alerts, total = OperationalAlertService.get_alerts(
            workspace_id=g.workspace_id,
            status=status,
            severity=severity,
            entity_type=entity_type,
            limit=limit,
            offset=offset
        )
        return success_response(data={
            'alerts': alerts,
            'total_count': total,
            'limit': limit,
            'offset': offset
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@alerts_bp.route('/evaluate', methods=['POST'])
@require_workspace('tasks:create')
def evaluate_alerts():
    """
    Triggers an on-demand signal evaluation run for the workspace.
    """
    try:
        created = OperationalAlertService.evaluate_operational_signals(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id
        )
        return success_response(
            message=f"Evaluation complete. Generated {len(created)} new alerts.",
            data={'created_count': len(created), 'alerts': [a.to_dict() for a in created]}
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@alerts_bp.route('/<alert_id>', methods=['GET'])
@require_workspace('tasks:read')
def get_alert(alert_id: str):
    try:
        alert = OperationalAlertService.get_alert_by_id(g.workspace_id, alert_id)
        return success_response(data=alert)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@alerts_bp.route('/<alert_id>/acknowledge', methods=['POST'])
@require_workspace('tasks:update')
def acknowledge_alert(alert_id: str):
    try:
        alert = OperationalAlertService.acknowledge_alert(g.workspace_id, alert_id, g.user_id)
        return success_response(message="Alert acknowledged.", data=alert)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@alerts_bp.route('/<alert_id>/resolve', methods=['POST'])
@require_workspace('tasks:update')
def resolve_alert(alert_id: str):
    try:
        body = request.get_json() or {}
        note = body.get('resolution_note')
        alert = OperationalAlertService.resolve_alert(g.workspace_id, alert_id, g.user_id, resolution_note=note)
        return success_response(message="Alert resolved.", data=alert)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@alerts_bp.route('/<alert_id>/dismiss', methods=['POST'])
@require_workspace('tasks:update')
def dismiss_alert(alert_id: str):
    try:
        alert = OperationalAlertService.dismiss_alert(g.workspace_id, alert_id, g.user_id)
        return success_response(message="Alert dismissed.", data=alert)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@alerts_bp.route('/<alert_id>/create-task', methods=['POST'])
@require_workspace('tasks:create')
def create_task_from_alert(alert_id: str):
    try:
        body = request.get_json() or {}
        assignee_id = body.get('assignee_member_id')
        priority = body.get('priority')
        due_date = body.get('due_date')

        res = OperationalAlertService.create_task_from_alert(
            workspace_id=g.workspace_id,
            alert_id=alert_id,
            actor_user_id=g.user_id,
            assignee_member_id=assignee_id,
            priority=priority,
            due_date=due_date
        )
        return success_response(message="Task generated from alert successfully.", data=res)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
