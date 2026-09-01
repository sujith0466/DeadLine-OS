"""
DeadlineOS Business OS — Purchase Orders API
=============================================
Endpoints for Purchase Order creation, lifecycle, line items, and supplier orders
under /api/business/purchase-orders.
"""

from flask import Blueprint, request, g
from middleware.business_context import require_workspace
from services.business.purchase_order_service import PurchaseOrderService
from utils.responses import success_response, error_response
from utils.errors import APIError

purchase_orders_bp = Blueprint('business_purchase_orders', __name__, url_prefix='/purchase-orders')


@purchase_orders_bp.route('', methods=['GET'])
@require_workspace(permission='procurement:read')
def list_purchase_orders():
    status = request.args.get('status')
    supplier_partner_id = request.args.get('supplier_partner_id')
    destination_location_id = request.args.get('destination_location_id')
    search = request.args.get('search')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    items, total = PurchaseOrderService.get_purchase_orders(
        workspace_id=g.workspace_id,
        status=status,
        supplier_partner_id=supplier_partner_id,
        destination_location_id=destination_location_id,
        search=search,
        limit=limit,
        offset=offset
    )

    return success_response(data={
        'items': items,
        'total': total,
        'limit': limit,
        'offset': offset
    })


@purchase_orders_bp.route('', methods=['POST'])
@require_workspace(permission='procurement:manage')
def create_purchase_order():
    data = request.get_json() or {}
    try:
        po = PurchaseOrderService.create_purchase_order(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=po.serialize(), message="Purchase order created successfully.", status_code=201)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@purchase_orders_bp.route('/<po_id>', methods=['GET'])
@require_workspace(permission='procurement:read')
def get_purchase_order(po_id):
    try:
        po = PurchaseOrderService.get_purchase_order_by_id(g.workspace_id, po_id)
        return success_response(data=po.serialize())
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@purchase_orders_bp.route('/<po_id>', methods=['PUT'])
@require_workspace(permission='procurement:manage')
def update_purchase_order(po_id):
    data = request.get_json() or {}
    try:
        po = PurchaseOrderService.update_purchase_order(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            po_id=po_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=po.serialize(), message="Purchase order updated successfully.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@purchase_orders_bp.route('/<po_id>/approve', methods=['POST'])
@require_workspace(permission='procurement:approve')
def approve_purchase_order(po_id):
    try:
        po = PurchaseOrderService.approve_purchase_order(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            po_id=po_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=po.serialize(), message="Purchase order approved.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@purchase_orders_bp.route('/<po_id>/send', methods=['POST'])
@require_workspace(permission='procurement:manage')
def send_purchase_order(po_id):
    try:
        po = PurchaseOrderService.send_purchase_order(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            po_id=po_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=po.serialize(), message="Purchase order sent to supplier.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@purchase_orders_bp.route('/<po_id>/cancel', methods=['POST'])
@require_workspace(permission='procurement:manage')
def cancel_purchase_order(po_id):
    data = request.get_json() or {}
    try:
        po = PurchaseOrderService.cancel_purchase_order(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            po_id=po_id,
            reason=data.get('reason'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=po.serialize(), message="Purchase order cancelled.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
