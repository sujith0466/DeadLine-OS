"""
DeadlineOS Business OS — Location Endpoints
============================================
Handles physical facility and store location registration and management.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.location_service import LocationService

locations_bp = Blueprint('biz_locations', __name__)


@locations_bp.route('/locations', methods=['GET'])
@require_workspace('locations:read')
def list_locations():
    status = request.args.get('status')
    location_type = request.args.get('location_type')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    try:
        locations, total = LocationService.get_locations(
            workspace_id=g.workspace_id,
            status=status,
            location_type=location_type,
            limit=limit,
            offset=offset
        )
        return success_response(data={"locations": locations, "total": total})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@locations_bp.route('/locations', methods=['POST'])
@require_workspace('locations:create')
def create_location():
    data = request.get_json(silent=True) or {}
    try:
        location = LocationService.create_location(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"location": location.serialize()},
            message="Location registered successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@locations_bp.route('/locations/<location_id>', methods=['GET'])
@require_workspace('locations:read')
def get_location(location_id):
    try:
        location = LocationService.get_location_by_id(g.workspace_id, location_id)
        return success_response(data={"location": location.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@locations_bp.route('/locations/<location_id>', methods=['PUT'])
@require_workspace('locations:update')
def update_location(location_id):
    data = request.get_json(silent=True) or {}
    try:
        location = LocationService.update_location(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            location_id=location_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"location": location.serialize()},
            message="Location updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
