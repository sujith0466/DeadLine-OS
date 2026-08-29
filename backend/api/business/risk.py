"""
DeadlineOS Business OS — Cash Risk Endpoints
============================================
Exposes deterministic cash risk indicators and burn velocity warnings.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from middleware.business_context import require_workspace
from services.business.cash_risk_service import CashRiskService

risk_bp = Blueprint('biz_risk', __name__)


@risk_bp.route('/financial/risks', methods=['GET'])
@require_workspace('transaction:read')
def get_cash_risks():
    try:
        risks = CashRiskService.evaluate_risks(g.workspace_id)
        return success_response(data={"risks": risks})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
