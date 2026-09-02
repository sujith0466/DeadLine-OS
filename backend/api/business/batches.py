"""
DeadlineOS Business OS — Batches, Lots & Expiry REST API
=========================================================
Endpoints for batch registration, quarantine lifecycle, FEFO suggestions,
and dynamic batch stock inspections.
"""

from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, g, jsonify
from middleware.business_context import require_workspace
from services.business.batch_service import BatchService
from utils.responses import success_response, error_response
from utils.errors import APIError

batches_bp = Blueprint('business_batches', __name__)


@batches_bp.route('', methods=['POST'])
@require_workspace('batch:write')
def create_batch():
    """Creates a new batch/lot master record."""
    data = request.get_json() or {}
    try:
        batch = BatchService.create_batch(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data
        )
        avail = BatchService.get_batch_available_stock(g.workspace_id, batch.id)
        return success_response(batch.serialize(available_quantity=avail), status_code=201)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
    except Exception as e:
        return error_response(str(e), error_code="INTERNAL_ERROR", status_code=500)


@batches_bp.route('', methods=['GET'])
@require_workspace('batch:read')
def list_batches():
    """Lists batches with filtering, search, and dynamic stock calculation."""
    try:
        product_id = request.args.get('product_id')
        status = request.args.get('status')
        expiring_soon_days = request.args.get('expiring_soon_days', type=int)
        search = request.args.get('search')
        limit = min(request.args.get('limit', default=50, type=int), 100)
        offset = request.args.get('offset', default=0, type=int)

        result = BatchService.list_batches(
            workspace_id=g.workspace_id,
            product_id=product_id,
            status=status,
            expiring_soon_days=expiring_soon_days,
            search=search,
            limit=limit,
            offset=offset
        )
        return success_response(result)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
    except Exception as e:
        return error_response(str(e), error_code="INTERNAL_ERROR", status_code=500)


@batches_bp.route('/fefo-suggestions', methods=['GET'])
@require_workspace('batch:read')
def get_fefo_suggestions():
    """Advisory FEFO engine providing batch allocation suggestions."""
    product_id = request.args.get('product_id')
    if not product_id:
        return error_response("Query parameter 'product_id' is required.", error_code="MISSING_PARAM", status_code=400)

    req_qty = None
    raw_qty = request.args.get('requested_quantity')
    if raw_qty is not None:
        try:
            req_qty = Decimal(str(raw_qty)).quantize(Decimal('0.01'))
            if req_qty <= Decimal('0.00'):
                return error_response("requested_quantity must be greater than zero.", error_code="INVALID_QUANTITY", status_code=400)
        except (InvalidOperation, TypeError, ValueError):
            return error_response("Invalid requested_quantity format.", error_code="INVALID_QUANTITY", status_code=400)

    try:
        result = BatchService.get_fefo_allocation(
            workspace_id=g.workspace_id,
            product_id=product_id,
            requested_quantity=req_qty
        )
        return success_response(result)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
    except Exception as e:
        return error_response(str(e), error_code="INTERNAL_ERROR", status_code=500)


@batches_bp.route('/<batch_id>', methods=['GET'])
@require_workspace('batch:read')
def get_batch(batch_id):
    """Fetches details and available stock of a single batch."""
    try:
        result = BatchService.get_batch(workspace_id=g.workspace_id, batch_id=batch_id)
        return success_response(result)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
    except Exception as e:
        return error_response(str(e), error_code="INTERNAL_ERROR", status_code=500)


@batches_bp.route('/<batch_id>/quarantine', methods=['POST'])
@require_workspace('batch:quarantine')
def quarantine_batch(batch_id):
    """Puts a batch into quarantine state."""
    data = request.get_json() or {}
    reason = data.get('reason')
    try:
        result = BatchService.quarantine_batch(
            workspace_id=g.workspace_id,
            batch_id=batch_id,
            actor_user_id=g.user_id,
            reason=reason
        )
        return success_response(result)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
    except Exception as e:
        return error_response(str(e), error_code="INTERNAL_ERROR", status_code=500)


@batches_bp.route('/<batch_id>/release', methods=['POST'])
@require_workspace('batch:quarantine')
def release_quarantine(batch_id):
    """Releases a batch from quarantine back to active status."""
    data = request.get_json() or {}
    release_notes = data.get('notes')
    try:
        result = BatchService.release_quarantine(
            workspace_id=g.workspace_id,
            batch_id=batch_id,
            actor_user_id=g.user_id,
            release_notes=release_notes
        )
        return success_response(result)
    except APIError as e:
        return error_response(e.message, error_code=e.code, status_code=e.status)
    except Exception as e:
        return error_response(str(e), error_code="INTERNAL_ERROR", status_code=500)
