"""
DeadlineOS Business OS — Landed Cost Allocation REST API (Phase C3.4)
====================================================================
REST API endpoints for landed cost vouchers, itemized expenditure intake,
allocation preview, execution, approval, and reversal.
"""

from flask import Blueprint, request, g
from middleware.business_context import require_workspace
from services.business.landed_cost_service import LandedCostService
from utils.errors import APIError
from utils.responses import success_response, error_response

landed_cost_bp = Blueprint('business_landed_cost', __name__)


@landed_cost_bp.route('', methods=['POST'])
@require_workspace('landed_cost:write')
def create_voucher():
    """Creates a new draft Landed Cost Voucher."""
    data = request.get_json() or {}
    try:
        voucher = LandedCostService.create_voucher(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Landed cost voucher '{voucher.voucher_number}' created successfully.",
            'voucher': voucher.serialize()
        }, status=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('', methods=['GET'])
@require_workspace('landed_cost:read')
def list_vouchers():
    """Lists and filters landed cost vouchers in the active workspace."""
    status = request.args.get('status')
    po_id = request.args.get('purchase_order_id')
    grn_id = request.args.get('goods_receipt_id')
    search = request.args.get('search')
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = max(int(request.args.get('offset', 0)), 0)

    try:
        res = LandedCostService.list_vouchers(
            workspace_id=g.workspace_id,
            status=status,
            purchase_order_id=po_id,
            goods_receipt_id=grn_id,
            search=search,
            limit=limit,
            offset=offset
        )
        return success_response(res)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('/<voucher_id>', methods=['GET'])
@require_workspace('landed_cost:read')
def get_voucher(voucher_id: str):
    """Retrieves full landed cost voucher details including items and allocations."""
    try:
        voucher = LandedCostService.get_voucher(
            workspace_id=g.workspace_id,
            voucher_id=voucher_id,
            include_items=True,
            include_allocations=True
        )
        return success_response({
            'voucher': voucher.serialize(include_items=True, include_allocations=True)
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('/<voucher_id>/items', methods=['POST'])
@require_workspace('landed_cost:write')
def add_cost_item(voucher_id: str):
    """Adds an itemized expenditure to a DRAFT landed cost voucher."""
    data = request.get_json() or {}
    try:
        item = LandedCostService.add_cost_item(
            workspace_id=g.workspace_id,
            voucher_id=voucher_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Cost item '{item.cost_category}' added successfully.",
            'item': item.serialize()
        }, status=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('/<voucher_id>/items/<item_id>', methods=['DELETE'])
@require_workspace('landed_cost:write')
def remove_cost_item(voucher_id: str, item_id: str):
    """Removes a cost item from a DRAFT landed cost voucher."""
    try:
        LandedCostService.remove_cost_item(
            workspace_id=g.workspace_id,
            voucher_id=voucher_id,
            item_id=item_id,
            actor_user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({'message': 'Cost item removed successfully.'})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('/<voucher_id>/preview', methods=['GET', 'POST'])
@require_workspace('landed_cost:read')
def preview_allocation(voucher_id: str):
    """Previews line allocations and residual-cent apportionment without database mutation."""
    basis = request.args.get('allocation_basis')
    if not basis and request.is_json:
        data = request.get_json() or {}
        basis = data.get('allocation_basis')

    try:
        preview = LandedCostService.preview_allocation(
            workspace_id=g.workspace_id,
            voucher_id=voucher_id,
            allocation_basis=basis
        )
        return success_response(preview)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('/<voucher_id>/allocate', methods=['POST'])
@require_workspace('landed_cost:allocate')
def execute_allocation(voucher_id: str):
    """Executes and persists line allocations, advancing voucher to ALLOCATED."""
    data = request.get_json() or {}
    basis = data.get('allocation_basis')

    try:
        voucher = LandedCostService.execute_allocation(
            workspace_id=g.workspace_id,
            voucher_id=voucher_id,
            actor_user_id=g.user_id,
            allocation_basis=basis,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Landed cost voucher '{voucher.voucher_number}' successfully allocated.",
            'voucher': voucher.serialize(include_items=True, include_allocations=True)
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('/<voucher_id>/approve', methods=['POST'])
@require_workspace('landed_cost:approve')
def approve_voucher(voucher_id: str):
    """Formally approves an allocated landed cost voucher, rendering it immutable."""
    try:
        voucher = LandedCostService.approve_voucher(
            workspace_id=g.workspace_id,
            voucher_id=voucher_id,
            actor_user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Landed cost voucher '{voucher.voucher_number}' successfully approved and locked.",
            'voucher': voucher.serialize(include_items=True, include_allocations=True)
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@landed_cost_bp.route('/<voucher_id>/reverse', methods=['POST'])
@require_workspace('landed_cost:reverse')
def reverse_voucher(voucher_id: str):
    """Reverses an approved landed cost voucher with mandatory justification."""
    data = request.get_json() or {}
    reason = data.get('reason')
    if not reason or not reason.strip():
        return error_response("Field 'reason' is mandatory for reversal.", "MISSING_REVERSAL_REASON", 400)

    try:
        voucher = LandedCostService.reverse_voucher(
            workspace_id=g.workspace_id,
            voucher_id=voucher_id,
            actor_user_id=g.user_id,
            reason=reason.strip(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return success_response({
            'message': f"Landed cost voucher '{voucher.voucher_number}' successfully reversed.",
            'voucher': voucher.serialize()
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
