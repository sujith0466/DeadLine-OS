"""
DeadlineOS Business OS — Business Entities Endpoints
====================================================
CRUD operations for operating entities, branches, and inter-entity transfers.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.entity_service import EntityService

entities_bp = Blueprint('biz_entities', __name__)


@entities_bp.route('/entities', methods=['POST'])
@require_workspace('transaction:create')
def create_entity():
    data = request.get_json(silent=True) or {}
    try:
        entity = EntityService.create_entity(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={'entity': entity.to_dict()},
            message="Business entity created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@entities_bp.route('/entities', methods=['GET'])
@require_workspace('transaction:read')
def list_entities():
    status = request.args.get('status')
    try:
        entities = EntityService.get_entities(g.workspace_id, status=status)
        return success_response(data={'entities': entities, 'count': len(entities)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@entities_bp.route('/entities/<entity_id>', methods=['GET'])
@require_workspace('transaction:read')
def get_entity(entity_id):
    try:
        entity = EntityService.get_entity(g.workspace_id, entity_id)
        return success_response(data={'entity': entity.to_dict()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@entities_bp.route('/entities/<entity_id>', methods=['PATCH'])
@require_workspace('transaction:create')
def update_entity(entity_id):
    data = request.get_json(silent=True) or {}
    try:
        entity = EntityService.update_entity(
            workspace_id=g.workspace_id,
            entity_id=entity_id,
            user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={'entity': entity.to_dict()},
            message="Business entity updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@entities_bp.route('/entities/<entity_id>/archive', methods=['POST'])
@require_workspace('transaction:create')
def archive_entity(entity_id):
    data = request.get_json(silent=True) or {}
    reason = data.get('reason')
    try:
        entity = EntityService.archive_entity(
            workspace_id=g.workspace_id,
            entity_id=entity_id,
            user_id=g.user_id,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={'entity': entity.to_dict()},
            message="Business entity archived successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@entities_bp.route('/transfers', methods=['POST'])
@require_workspace('transaction:create')
def create_inter_entity_transfer():
    data = request.get_json(silent=True) or {}
    try:
        transfer = EntityService.record_transfer(
            source_workspace_id=g.workspace_id,
            user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={'transfer': transfer.to_dict()},
            message="Inter-entity transfer recorded successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@entities_bp.route('/transfers', methods=['GET'])
@require_workspace('transaction:read')
def list_inter_entity_transfers():
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    try:
        transfers = EntityService.get_transfers(g.workspace_id, limit=limit, offset=offset)
        return success_response(data={'transfers': transfers, 'count': len(transfers)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
