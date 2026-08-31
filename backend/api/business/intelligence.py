"""
DeadlineOS Business OS — Business Intelligence Endpoints
========================================================
Exposes historical trends, deterministic cash flow forecasting,
scenario simulation models, and executive decision briefings.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.intelligence_service import BusinessIntelligenceService

intelligence_bp = Blueprint('biz_intelligence', __name__)


@intelligence_bp.route('/intelligence/trends', methods=['GET'])
@require_workspace('transaction:read')
def get_trends():
    months = int(request.args.get('months', 6))
    try:
        data = BusinessIntelligenceService.get_historical_trends(
            workspace_id=g.workspace_id,
            months=months
        )
        return success_response(data={"trends": data})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@intelligence_bp.route('/intelligence/forecast', methods=['GET'])
@require_workspace('transaction:read')
def get_forecast():
    horizon_days = int(request.args.get('horizon_days', 90))
    try:
        data = BusinessIntelligenceService.calculate_cash_forecast(
            workspace_id=g.workspace_id,
            horizon_days=horizon_days
        )
        return success_response(data={"forecast": data})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@intelligence_bp.route('/intelligence/scenarios', methods=['POST'])
@require_workspace('transaction:read')
def get_scenarios():
    body = request.get_json(silent=True) or {}
    custom_params = body.get('custom_params')
    horizon_days = int(body.get('horizon_days', 90))
    try:
        data = BusinessIntelligenceService.simulate_scenarios(
            workspace_id=g.workspace_id,
            custom_params=custom_params,
            horizon_days=horizon_days
        )
        return success_response(data={"scenarios": data})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@intelligence_bp.route('/intelligence/brief', methods=['GET'])
@require_workspace('transaction:read')
def get_decision_brief():
    try:
        data = BusinessIntelligenceService.get_executive_decision_brief(
            workspace_id=g.workspace_id
        )
        return success_response(data={"brief": data})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
