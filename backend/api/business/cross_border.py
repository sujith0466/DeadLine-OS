"""
DeadlineOS Business OS — Cross-Border Hub & Copilot REST API (Phase C3.5)
========================================================================
REST API endpoints for cross-border shipments, customs context, operational
timeline, and grounded copilot conversational queries and proposal staging.
"""

from flask import Blueprint, request, g
from middleware.business_context import require_workspace
from services.business.cross_border_hub_service import CrossBorderHubService
from services.business.copilot_service import CopilotService
from utils.errors import APIError
from utils.responses import success_response, error_response

cross_border_bp = Blueprint('business_cross_border', __name__)


@cross_border_bp.route('/summary', methods=['GET'])
@require_workspace('cross_border:read')
def get_hub_summary():
    """Retrieves operational summary metrics, transit statuses, and risk signals."""
    try:
        summary = CrossBorderHubService.get_operations_summary(g.workspace_id)
        return success_response(summary)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@cross_border_bp.route('/shipments', methods=['POST'])
@require_workspace('cross_border:write')
def create_shipment():
    """Creates a new operational cross-border shipment."""
    data = request.get_json() or {}
    try:
        shipment = CrossBorderHubService.create_shipment(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Shipment '{shipment.shipment_number}' created successfully.",
            'shipment': shipment.serialize()
        }, status=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@cross_border_bp.route('/shipments', methods=['GET'])
@require_workspace('cross_border:read')
def list_shipments():
    """Lists and filters cross-border shipments in the workspace."""
    status = request.args.get('status')
    customs_status = request.args.get('customs_status')
    supplier_id = request.args.get('supplier_partner_id')
    search = request.args.get('search')
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = max(int(request.args.get('offset', 0)), 0)

    try:
        res = CrossBorderHubService.list_shipments(
            workspace_id=g.workspace_id,
            status=status,
            customs_status=customs_status,
            supplier_id=supplier_id,
            search=search,
            limit=limit,
            offset=offset
        )
        return success_response(res)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@cross_border_bp.route('/shipments/<shipment_id>', methods=['GET'])
@require_workspace('cross_border:read')
def get_shipment_detail(shipment_id: str):
    """Retrieves correlated shipment details including PO, GRN, Landed Costs, batches, and serials."""
    try:
        res = CrossBorderHubService.get_shipment_detail(g.workspace_id, shipment_id)
        return success_response({'shipment': res})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@cross_border_bp.route('/shipments/<shipment_id>/status', methods=['PUT'])
@require_workspace('cross_border:status')
def update_shipment_status(shipment_id: str):
    """Updates shipment operational state and customs status with state machine enforcement."""
    data = request.get_json() or {}
    try:
        shipment = CrossBorderHubService.update_shipment_status(
            workspace_id=g.workspace_id,
            shipment_id=shipment_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Shipment '{shipment.shipment_number}' updated successfully.",
            'shipment': shipment.serialize()
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@cross_border_bp.route('/timeline', methods=['GET'])
@require_workspace('cross_border:read')
def get_operational_timeline():
    """Retrieves the chronological operational timeline across procurement, shipments, and inventory."""
    shipment_id = request.args.get('shipment_id')
    po_id = request.args.get('purchase_order_id')
    grn_id = request.args.get('goods_receipt_id')

    try:
        timeline = CrossBorderHubService.get_operational_timeline(
            workspace_id=g.workspace_id,
            shipment_id=shipment_id,
            purchase_order_id=po_id,
            goods_receipt_id=grn_id
        )
        return success_response({'timeline': timeline})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@cross_border_bp.route('/copilot/query', methods=['POST'])
@require_workspace('copilot:query')
def query_copilot():
    """Queries the Grounded Business Copilot with strict semantic separation (FACTS, SIGNALS, FORECASTS, RECS)."""
    data = request.get_json() or {}
    prompt = data.get('prompt')
    if not prompt or not prompt.strip():
        return error_response("Field 'prompt' is required.", "MISSING_PROMPT", 400)

    try:
        res = CopilotService.ask_copilot(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            prompt=prompt.strip(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response(res)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@cross_border_bp.route('/copilot/propose', methods=['POST'])
@require_workspace('copilot:propose')
def propose_copilot_action():
    """Stages an AI-suggested operational proposal into StagedExtraction for human review."""
    data = request.get_json() or {}
    action_type = data.get('action_type')
    payload = data.get('payload') or {}
    rationale = data.get('rationale') or "AI operational recommendation"

    if not action_type:
        return error_response("Field 'action_type' is required.", "MISSING_ACTION_TYPE", 400)

    try:
        staged = CopilotService.propose_action(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            action_type=action_type,
            payload=payload,
            rationale=rationale,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Proposal '{action_type}' staged successfully for human review.",
            'staged_extraction': staged.serialize()
        }, status=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
