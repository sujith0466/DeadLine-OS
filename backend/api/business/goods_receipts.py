"""
DeadlineOS Business OS — Goods Receipts API (Phase C2.2)
==========================================================
RESTful endpoints for creating and viewing Goods Receipt Notes (GRN),
inspecting delivered lines, and monitoring physical stock receiving sessions.
"""

from flask import Blueprint, request, g
from middleware.business_context import require_workspace
from services.business.goods_receipt_service import GoodsReceiptService
from utils.responses import success_response, error_response
from utils.errors import APIError

goods_receipts_bp = Blueprint('business_goods_receipts', __name__)


@goods_receipts_bp.route('', methods=['GET'])
@require_workspace(permission='procurement:read')
def list_goods_receipts():
    """
    Lists Goods Receipt Notes for the active workspace with optional filters.
    """
    po_id = request.args.get('po_id')
    supplier_partner_id = request.args.get('supplier_partner_id')
    status = request.args.get('status')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))

    items, total = GoodsReceiptService.list_goods_receipts(
        workspace_id=g.workspace_id,
        po_id=po_id,
        supplier_partner_id=supplier_partner_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return success_response(data={
        'items': [item.serialize(include_lines=True) for item in items],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@goods_receipts_bp.route('', methods=['POST'])
@require_workspace(permission='procurement:receive')
def create_goods_receipt():
    """
    Records a physical goods arrival session against an approved/sent Purchase Order.
    Creates immutable stock movements for accepted items and emits an AP staging candidate.
    """
    data = request.get_json() or {}
    try:
        grn = GoodsReceiptService.create_goods_receipt(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(
            data=grn.serialize(include_lines=True),
            message=f"Goods receipt {grn.grn_number} created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)


@goods_receipts_bp.route('/<grn_id>', methods=['GET'])
@require_workspace(permission='procurement:read')
def get_goods_receipt(grn_id):
    """
    Retrieves a single Goods Receipt Note with all itemized lines and inspection details.
    """
    try:
        grn = GoodsReceiptService.get_goods_receipt_by_id(g.workspace_id, grn_id)
        return success_response(data=grn.serialize(include_lines=True))
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)