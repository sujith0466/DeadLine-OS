"""
DeadlineOS Business OS — Operational Intelligence REST API Endpoints (Phase C2.3)
================================================================================
Exposes deterministic operational analytics, inventory forecasting, supplier scoring,
and replenishment suggestions.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.operational_intelligence_service import OperationalIntelligenceService

operational_intelligence_bp = Blueprint('operational_intelligence', __name__)


@operational_intelligence_bp.route('/summary', methods=['GET'])
@require_workspace('intelligence:read')
def get_operational_summary():
    """
    Returns aggregate operational health, stockout counts, dead stock, and supplier OTIF.
    """
    try:
        data = OperationalIntelligenceService.get_operational_summary(g.workspace_id)
        return success_response(data=data)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@operational_intelligence_bp.route('/inventory-forecast', methods=['GET'])
@require_workspace('intelligence:read')
def get_inventory_forecast():
    """
    Returns itemized inventory burn rates, Days of Inventory Remaining, and projected stockout dates.
    """
    try:
        window_days = request.args.get('window_days', 30, type=int)
        items = OperationalIntelligenceService.get_inventory_forecast(g.workspace_id, window_days=window_days)
        return success_response(data={
            'items': items,
            'total_count': len(items),
            'window_days': window_days
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@operational_intelligence_bp.route('/suppliers', methods=['GET'])
@require_workspace('intelligence:read')
def get_supplier_performance():
    """
    Returns deterministic supplier performance scorecard (OTIF, quality %, lead times).
    """
    try:
        suppliers = OperationalIntelligenceService.get_supplier_performance_summary(g.workspace_id)
        return success_response(data={
            'suppliers': suppliers,
            'total_count': len(suppliers)
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@operational_intelligence_bp.route('/reorder-suggestions', methods=['GET'])
@require_workspace('intelligence:read')
def get_reorder_suggestions():
    """
    Returns calculated reorder proposals for at-risk products.
    """
    try:
        suggestions = OperationalIntelligenceService.get_reorder_suggestions(g.workspace_id)
        return success_response(data={
            'suggestions': suggestions,
            'total_count': len(suggestions)
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
