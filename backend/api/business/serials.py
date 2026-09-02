"""
DeadlineOS Business OS — Serial Numbers & Unit Provenance API
============================================================
REST API endpoints for serial registration, listing, provenance lookup,
and lifecycle state machine transitions.
"""

from flask import Blueprint, request, jsonify, g
from middleware.business_context import require_workspace, ROLE_PERMISSIONS
from services.business.serial_service import SerialService
from database.db import db
from utils.errors import APIError
from utils.responses import success_response, error_response

serials_bp = Blueprint('business_serials', __name__)


@serials_bp.route('', methods=['POST'])
@require_workspace('serial:write')
def register_serials():
    """
    Registers a batch of serial numbers for a product.
    """
    data = request.get_json() or {}
    product_id = data.get('product_id')
    serial_numbers = data.get('serial_numbers') or data.get('serials') or []

    if not product_id:
        raise APIError("Field 'product_id' is required.", code="MISSING_PRODUCT_ID", status=400)
    if not serial_numbers or not isinstance(serial_numbers, list):
        raise APIError("Field 'serial_numbers' must be a non-empty list of strings.", code="INVALID_SERIALS_PAYLOAD", status=400)

    try:
        serials = SerialService.register_or_receive_serials(
            workspace_id=g.workspace_id,
            product_id=product_id,
            serial_numbers=serial_numbers,
            actor_user_id=g.user_id,
            location_id=data.get('location_id'),
            batch_id=data.get('batch_id'),
            goods_receipt_id=data.get('goods_receipt_id'),
            notes=data.get('notes')
        )
        db.session.commit()
        return success_response({
            'message': f"Registered {len(serials)} serial numbers.",
            'serials': [s.serialize() for s in serials]
        }, status=201)
    except APIError as e:
        db.session.rollback()
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), "INTERNAL_ERROR", 500)


@serials_bp.route('', methods=['GET'])
@require_workspace('serial:read')
def list_serials():
    """
    Lists and searches serial numbers within the active workspace.
    """
    product_id = request.args.get('product_id')
    batch_id = request.args.get('batch_id')
    status = request.args.get('status')
    location_id = request.args.get('location_id')
    search = request.args.get('search')
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = max(int(request.args.get('offset', 0)), 0)

    try:
        res = SerialService.list_serials(
            workspace_id=g.workspace_id,
            product_id=product_id,
            batch_id=batch_id,
            status=status,
            location_id=location_id,
            search=search,
            limit=limit,
            offset=offset
        )
        return success_response(res)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@serials_bp.route('/<serial_id>', methods=['GET'])
@require_workspace('serial:read')
def get_serial(serial_id: str):
    """
    Retrieves individual serial number details.
    """
    try:
        serial = SerialService.get_serial(g.workspace_id, serial_id)
        return success_response({'serial': serial.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@serials_bp.route('/<serial_id>/provenance', methods=['GET'])
@require_workspace('serial:read')
def get_serial_provenance(serial_id: str):
    """
    Retrieves complete lifecycle provenance history for a serialized unit.
    """
    try:
        provenance = SerialService.get_serial_provenance(g.workspace_id, serial_id)
        return success_response(provenance)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@serials_bp.route('/<serial_id>/transition', methods=['POST'])
@require_workspace('serial:write')
def transition_serial(serial_id: str):
    """
    Transitions the lifecycle status of a serialized unit.
    """
    data = request.get_json() or {}
    target_status = data.get('target_status') or data.get('status')
    if not target_status:
        return error_response("Field 'target_status' is required.", "MISSING_TARGET_STATUS", 400)

    # Restrict transitions to DEFECTIVE/DISPOSED to serial:quarantine permission
    if target_status.upper() in ('DEFECTIVE', 'DISPOSED'):
        if 'serial:quarantine' not in ROLE_PERMISSIONS.get(g.member_role, set()):
            return error_response("Insufficient permissions to flag serial as defective or disposed.", "FORBIDDEN", 403)

    try:
        serial = SerialService.transition_lifecycle(
            workspace_id=g.workspace_id,
            serial_id=serial_id,
            target_status=target_status,
            actor_user_id=g.user_id,
            reason=data.get('reason'),
            location_id=data.get('location_id'),
            notes=data.get('notes')
        )
        db.session.commit()
        return success_response({
            'message': f"Serial '{serial.serial_number}' transitioned to '{serial.status}'.",
            'serial': serial.serialize()
        })
    except APIError as e:
        db.session.rollback()
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), "INTERNAL_ERROR", 500)


@serials_bp.route('/<serial_id>/quarantine', methods=['POST'])
@require_workspace('serial:quarantine')
def quarantine_serial(serial_id: str):
    """
    Flags a serialized unit as DEFECTIVE / quarantined.
    """
    data = request.get_json() or {}
    reason = data.get('reason') or "Flagged as defective"

    try:
        serial = SerialService.transition_lifecycle(
            workspace_id=g.workspace_id,
            serial_id=serial_id,
            target_status='DEFECTIVE',
            actor_user_id=g.user_id,
            reason=reason,
            notes=data.get('notes')
        )
        db.session.commit()
        return success_response({
            'message': f"Serial '{serial.serial_number}' quarantined / flagged as defective.",
            'serial': serial.serialize()
        })
    except APIError as e:
        db.session.rollback()
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), "INTERNAL_ERROR", 500)


@serials_bp.route('/<serial_id>/dispose', methods=['POST'])
@require_workspace('serial:quarantine')
def dispose_serial(serial_id: str):
    """
    Marks a serialized unit as DISPOSED / scrapped.
    """
    data = request.get_json() or {}
    reason = data.get('reason') or "Disposed / Scrapped"

    try:
        serial = SerialService.transition_lifecycle(
            workspace_id=g.workspace_id,
            serial_id=serial_id,
            target_status='DISPOSED',
            actor_user_id=g.user_id,
            reason=reason,
            notes=data.get('notes')
        )
        db.session.commit()
        return success_response({
            'message': f"Serial '{serial.serial_number}' permanently disposed.",
            'serial': serial.serialize()
        })
    except APIError as e:
        db.session.rollback()
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), "INTERNAL_ERROR", 500)
