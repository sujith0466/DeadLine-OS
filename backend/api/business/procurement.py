"""
DeadlineOS Business OS — Purchase Requests API
================================================
Endpoints for Purchase Request creation, approval, rejection, cancellation,
and conversion to Purchase Orders under /api/business/procurement.
"""

from flask import Blueprint, request, g
from middleware.business_context import require_workspace
from services.business.purchase_request_service import PurchaseRequestService
from services.business.purchase_order_service import PurchaseOrderService
from utils.responses import success_response, error_response
from utils.errors import APIError

procurement_bp = Blueprint('business_procurement', __name__, url_prefix='/procurement')


@procurement_bp.route('/requests', methods=['GET'])
@require_workspace(permission='procurement:read')
def list_requests():
    status = request.args.get('status')
    priority = request.args.get('priority')
    product_id = request.args.get('product_id')
    location_id = request.args.get('location_id')
    search = request.args.get('search')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    items, total = PurchaseRequestService.get_requests(
        workspace_id=g.workspace_id,
        status=status,
        priority=priority,
        product_id=product_id,
        location_id=location_id,
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


@procurement_bp.route('/requests', methods=['POST'])
@require_workspace(permission='procurement:create')
def create_request():
    data = request.get_json() or {}
    try:
        pr = PurchaseRequestService.create_request(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=pr.serialize(), message="Purchase request created successfully.", status_code=201)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@procurement_bp.route('/requests/<request_id>', methods=['GET'])
@require_workspace(permission='procurement:read')
def get_request(request_id):
    try:
        pr = PurchaseRequestService.get_request_by_id(g.workspace_id, request_id)
        return success_response(data=pr.serialize())
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@procurement_bp.route('/requests/<request_id>', methods=['PUT'])
@require_workspace(permission='procurement:update')
def update_request(request_id):
    data = request.get_json() or {}
    try:
        pr = PurchaseRequestService.update_request(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            request_id=request_id,
            data=data,
            user_role=g.member_role,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=pr.serialize(), message="Purchase request updated successfully.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@procurement_bp.route('/requests/<request_id>/approve', methods=['POST'])
@require_workspace(permission='procurement:approve')
def approve_request(request_id):
    data = request.get_json() or {}
    try:
        pr = PurchaseRequestService.approve_request(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            request_id=request_id,
            approval_notes=data.get('approval_notes'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=pr.serialize(), message="Purchase request approved.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@procurement_bp.route('/requests/<request_id>/reject', methods=['POST'])
@require_workspace(permission='procurement:approve')
def reject_request(request_id):
    data = request.get_json() or {}
    try:
        pr = PurchaseRequestService.reject_request(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            request_id=request_id,
            reason=data.get('reason'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=pr.serialize(), message="Purchase request rejected.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@procurement_bp.route('/requests/<request_id>/cancel', methods=['POST'])
@require_workspace(permission='procurement:update')
def cancel_request(request_id):
    data = request.get_json() or {}
    try:
        pr = PurchaseRequestService.cancel_request(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            request_id=request_id,
            reason=data.get('reason'),
            user_role=g.member_role,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=pr.serialize(), message="Purchase request cancelled.")
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@procurement_bp.route('/requests/<request_id>/convert-to-po', methods=['POST'])
@require_workspace(permission='procurement:manage')
def convert_to_po(request_id):
    data = request.get_json() or {}
    try:
        po = PurchaseOrderService.convert_pr_to_po(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            request_id=request_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(data=po.serialize(), message="Purchase request successfully converted to Purchase Order.", status_code=201)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
