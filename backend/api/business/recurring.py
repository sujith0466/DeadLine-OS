"""
DeadlineOS Business OS — Recurring Obligations Endpoints
========================================================
CRUD and lifecycle operations for recurring business contracts.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.recurring_obligation_service import RecurringObligationService
from services.business.automation_runner_service import AutomationRunnerService

recurring_bp = Blueprint('biz_recurring', __name__)


@recurring_bp.route('/recurring', methods=['POST'])
@require_workspace('transaction:create')
def create_recurring_obligation():
    data = request.get_json(silent=True) or {}
    try:
        obligation = RecurringObligationService.create_obligation(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={'obligation': obligation.to_dict()},
            message="Recurring obligation created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@recurring_bp.route('/recurring', methods=['GET'])
@require_workspace('transaction:read')
def list_recurring_obligations():
    obligation_type = request.args.get('obligation_type')
    status = request.args.get('status')
    try:
        obligations = RecurringObligationService.get_obligations(
            workspace_id=g.workspace_id,
            obligation_type=obligation_type,
            status=status
        )
        return success_response(data={'obligations': obligations, 'count': len(obligations)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@recurring_bp.route('/recurring/<obligation_id>', methods=['GET'])
@require_workspace('transaction:read')
def get_recurring_obligation(obligation_id):
    try:
        obligation = RecurringObligationService.get_obligation(g.workspace_id, obligation_id)
        return success_response(data={'obligation': obligation.to_dict()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@recurring_bp.route('/recurring/<obligation_id>/pause', methods=['POST'])
@require_workspace('transaction:create')
def pause_recurring_obligation(obligation_id):
    try:
        obligation = RecurringObligationService.pause_obligation(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            obligation_id=obligation_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(data={'obligation': obligation.to_dict()}, message="Recurring obligation paused.")
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@recurring_bp.route('/recurring/<obligation_id>/resume', methods=['POST'])
@require_workspace('transaction:create')
def resume_recurring_obligation(obligation_id):
    try:
        obligation = RecurringObligationService.resume_obligation(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            obligation_id=obligation_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(data={'obligation': obligation.to_dict()}, message="Recurring obligation resumed.")
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@recurring_bp.route('/recurring/<obligation_id>/cancel', methods=['POST'])
@require_workspace('transaction:create')
def cancel_recurring_obligation(obligation_id):
    try:
        obligation = RecurringObligationService.cancel_obligation(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            obligation_id=obligation_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(data={'obligation': obligation.to_dict()}, message="Recurring obligation cancelled.")
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@recurring_bp.route('/recurring/<obligation_id>/trigger', methods=['POST'])
@require_workspace('transaction:create')
def trigger_single_obligation(obligation_id):
    data = request.get_json(silent=True) or {}
    target_date = None
    if data.get('target_date'):
        try:
            from datetime import datetime
            target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        except Exception:
            pass
    try:
        res = AutomationRunnerService.trigger_obligation(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            obligation_id=obligation_id,
            target_date=target_date,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(data=res, message="Obligation triggered successfully.")
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
