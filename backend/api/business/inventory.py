"""
DeadlineOS Business OS — Inventory & Stock Movement Endpoints
==============================================================
Handles live derived stock level queries, append-only stock movement logging,
atomic transfers, and low-stock alerts.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.inventory_service import InventoryService

inventory_bp = Blueprint('biz_inventory', __name__)


@inventory_bp.route('/inventory', methods=['GET'])
@require_workspace('inventory:read')
def get_inventory():
    location_id = request.args.get('location_id')
    category = request.args.get('category')
    status_filter = request.args.get('status')
    search = request.args.get('search')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        data = InventoryService.get_stock_levels(
            workspace_id=g.workspace_id,
            location_id=location_id,
            category=category,
            status_filter=status_filter,
            search=search,
            limit=limit,
            offset=offset
        )
        return success_response(data=data)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@inventory_bp.route('/inventory/movements', methods=['POST'])
@require_workspace('inventory:adjust')
def record_stock_movement():
    data = request.get_json(silent=True) or {}
    try:
        movement = InventoryService.record_stock_movement(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            staged_extraction_id=data.get('staged_extraction_id'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"movement": movement.serialize()},
            message="Stock movement recorded successfully in immutable ledger.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@inventory_bp.route('/inventory/transfers', methods=['POST'])
@require_workspace('inventory:adjust')
def transfer_stock():
    data = request.get_json(silent=True) or {}
    try:
        transfer = InventoryService.transfer_stock(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"transfer": transfer},
            message="Atomic stock transfer executed successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@inventory_bp.route('/inventory/movements', methods=['GET'])
@require_workspace('inventory:read')
def list_movements():
    product_id = request.args.get('product_id')
    location_id = request.args.get('location_id')
    movement_type = request.args.get('movement_type')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        movements, total = InventoryService.get_movement_ledger(
            workspace_id=g.workspace_id,
            product_id=product_id,
            location_id=location_id,
            movement_type=movement_type,
            limit=limit,
            offset=offset
        )
        return success_response(data={"movements": movements, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@inventory_bp.route('/inventory/low-stock', methods=['GET'])
@require_workspace('inventory:read')
def get_low_stock():
    try:
        data = InventoryService.get_stock_levels(
            workspace_id=g.workspace_id,
            status_filter='LOW',
            limit=100,
            offset=0
        )
        return success_response(data=data)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
