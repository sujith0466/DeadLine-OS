"""
DeadlineOS Business OS — Workspace Members Endpoints
====================================================
Handles listing, inviting, and managing roles for workspace members.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.workspace_service import WorkspaceService

members_bp = Blueprint('biz_members', __name__)


@members_bp.route('/members', methods=['GET'])
@require_workspace('members:read')
def list_members():
    try:
        members = WorkspaceService.get_workspace_members(g.workspace_id)
        return success_response(data={"members": members, "total": len(members)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@members_bp.route('/members/invite', methods=['POST'])
@require_workspace('members:invite')
def invite_member():
    data = request.get_json() or {}
    email = data.get('email')
    role = data.get('role', 'MEMBER')

    if not email:
        return error_response("Field 'email' is required.", "VALIDATION_ERROR", 400)

    try:
        member = WorkspaceService.invite_member(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            email=email,
            role=role,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"member": member.serialize()},
            message="Member invited successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@members_bp.route('/members/<member_id>/role', methods=['PATCH'])
@require_workspace('members:role_update')
def update_member_role(member_id):
    data = request.get_json() or {}
    new_role = data.get('role')

    if not new_role:
        return error_response("Field 'role' is required.", "VALIDATION_ERROR", 400)

    try:
        member = WorkspaceService.update_member_role(
            workspace_id=g.workspace_id,
            member_id=member_id,
            actor_user_id=g.user_id,
            new_role=new_role,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"member": member.serialize()},
            message="Member role updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@members_bp.route('/members/<member_id>/status', methods=['PATCH'])
@require_workspace('members:remove')
def update_member_status(member_id):
    data = request.get_json() or {}
    new_status = data.get('status')

    if not new_status:
        return error_response("Field 'status' is required.", "VALIDATION_ERROR", 400)

    try:
        member = WorkspaceService.update_member_status(
            workspace_id=g.workspace_id,
            member_id=member_id,
            actor_user_id=g.user_id,
            new_status=new_status,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"member": member.serialize()},
            message="Member status updated successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@members_bp.route('/members/<member_id>', methods=['DELETE'])
@require_workspace('members:remove')
def remove_member(member_id):
    try:
        WorkspaceService.remove_member(
            workspace_id=g.workspace_id,
            member_id=member_id,
            actor_user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"removed": True},
            message="Member removed successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
