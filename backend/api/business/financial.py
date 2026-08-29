"""
DeadlineOS Business OS — Financial Truth & Runway Endpoints
===========================================================
Exposes Confirmed Cash, Committed Inflows/Outflows, Projected Position,
and deterministic Runway Days.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from middleware.business_context import require_workspace
from services.business.financial_truth_service import FinancialTruthService

financial_bp = Blueprint('biz_financial', __name__)


@financial_bp.route('/financial/cash-position', methods=['GET'])
@require_workspace('transaction:read')
def get_cash_position():
    window_days = int(request.args.get('window_days', 30))
    try:
        pos = FinancialTruthService.get_cash_position(g.workspace_id, window_days=window_days)
        return success_response(data={"cash_position": pos})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@financial_bp.route('/financial/runway', methods=['GET'])
@require_workspace('transaction:read')
def get_runway():
    try:
        runway = FinancialTruthService.calculate_runway_days(g.workspace_id)
        return success_response(data={"runway": runway})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
