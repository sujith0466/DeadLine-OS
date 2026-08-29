"""
DeadlineOS Business OS — Workspace Endpoints
============================================
Handles workspace creation, listing, switching profile, and updates.
"""

from flask import Blueprint, request, g
from utils.auth import require_auth
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace, ROLE_PERMISSIONS
from services.business.workspace_service import WorkspaceService

workspaces_bp = Blueprint('biz_workspaces', __name__)


@workspaces_bp.route('/workspaces', methods=['POST'])
@require_auth
def create_workspace():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return error_response("Workspace 'name' is required.", "VALIDATION_ERROR", 400)

    try:
        workspace = WorkspaceService.create_workspace(
            name=name,
            owner_user_id=g.user_id,
            legal_name=data.get('legal_name'),
            tax_identifier=data.get('tax_identifier'),
            base_currency=data.get('base_currency', 'INR'),
            timezone=data.get('timezone', 'Asia/Kolkata'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"workspace": workspace.serialize()},
            message="Workspace created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@workspaces_bp.route('/workspaces', methods=['GET'])
@require_auth
def list_workspaces():
    try:
        workspaces = WorkspaceService.get_user_workspaces(g.user_id)
        return success_response(data={"workspaces": workspaces})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@workspaces_bp.route('/workspaces/current', methods=['GET'])
@require_workspace('workspace:read')
def get_current_workspace():
    permissions = list(ROLE_PERMISSIONS.get(g.member_role, set()))
    return success_response(data={
        "workspace": g.workspace.serialize(),
        "member": g.member.serialize(),
        "permissions": permissions
    })


@workspaces_bp.route('/workspaces/current', methods=['PATCH'])
@require_workspace('workspace:update')
def update_current_workspace():
    data = request.get_json() or {}
    try:
        updated = WorkspaceService.update_workspace(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            updates=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"workspace": updated.serialize()},
            message="Workspace updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
