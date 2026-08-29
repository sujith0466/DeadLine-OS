"""
DeadlineOS Business OS — Rescue Endpoints
=========================================
Overdue aging analysis and prioritized receivable recovery queue.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from middleware.business_context import require_workspace
from services.business.rescue_service import RescueService

rescue_bp = Blueprint('biz_rescue', __name__)


@rescue_bp.route('/rescue/aging', methods=['GET'])
@require_workspace('transaction:read')
def get_aging_summary():
    try:
        data = RescueService.get_aging_summary(g.workspace_id)
        return success_response(data=data)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@rescue_bp.route('/rescue/priorities', methods=['GET'])
@require_workspace('transaction:read')
def get_priority_receivables():
    limit = int(request.args.get('limit', 20))
    try:
        priorities = RescueService.get_priority_receivables(g.workspace_id, limit=limit)
        return success_response(data={'priorities': priorities, 'count': len(priorities)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
