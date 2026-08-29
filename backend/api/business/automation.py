"""
DeadlineOS Business OS — Automation Runner Endpoints
====================================================
Batch execution and audit log queries for automation jobs.
"""

from flask import Blueprint, request, g
from datetime import datetime
from utils.responses import success_response, error_response
from middleware.business_context import require_workspace
from services.business.automation_runner_service import AutomationRunnerService

automation_bp = Blueprint('biz_automation', __name__)


@automation_bp.route('/automation/run', methods=['POST'])
@require_workspace('transaction:create')
def run_batch_automations():
    data = request.get_json(silent=True) or {}
    as_of_date = None
    if data.get('as_of_date'):
        try:
            as_of_date = datetime.strptime(data['as_of_date'], '%Y-%m-%d').date()
        except Exception:
            pass

    try:
        res = AutomationRunnerService.run_batch_automations(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            as_of_date=as_of_date
        )
        return success_response(data=res, message="Automation batch execution completed.")
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@automation_bp.route('/automation/logs', methods=['GET'])
@require_workspace('transaction:read')
def get_automation_logs():
    obligation_id = request.args.get('obligation_id')
    limit = int(request.args.get('limit', 50))
    try:
        logs = AutomationRunnerService.get_execution_logs(g.workspace_id, obligation_id=obligation_id, limit=limit)
        return success_response(data={'logs': logs, 'count': len(logs)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
