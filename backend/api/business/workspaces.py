"""
DeadlineOS Business OS — Workspace Endpoints
============================================
Handles workspace creation, listing, switching profile, and updates.
"""

from flask import Blueprint, request, g
from app import limiter
from utils.auth import require_auth
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace, ROLE_PERMISSIONS
from services.business.workspace_service import WorkspaceService
from services.business.invitation_service import InvitationService
from models.business import Workspace

workspaces_bp = Blueprint('biz_workspaces', __name__)


@workspaces_bp.route('/workspaces', methods=['POST'])
@require_auth
@limiter.limit("10 per minute")
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
        return success_response(data={"workspaces": workspaces, "total": len(workspaces)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@workspaces_bp.route('/workspaces/<workspace_id>', methods=['GET'])
@require_auth
def get_workspace_detail(workspace_id):
    try:
        workspace_data = WorkspaceService.get_workspace_by_id_for_user(
            workspace_id=workspace_id,
            user_id=g.user_id
        )
        return success_response(data={"workspace": workspace_data})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
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


# ── WORKSPACE INVITATION ENDPOINTS ─────────────────────────────────────────────

@workspaces_bp.route('/workspaces/invitations', methods=['POST'])
@require_workspace('members:invite')
@limiter.limit("20 per minute")
def create_invitation():
    data = request.get_json() or {}
    email = data.get('email')
    role = data.get('role', 'MEMBER')
    expires_in_days = int(data.get('expires_in_days', 7))

    if not email:
        return error_response("Field 'email' is required.", "VALIDATION_ERROR", 400)

    try:
        invitation = InvitationService.create_invitation(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            email=email,
            role=role,
            expires_in_days=expires_in_days,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"invitation": invitation.serialize(), "token": invitation.token},
            message="Invitation created successfully.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@workspaces_bp.route('/workspaces/invitations', methods=['GET'])
@require_workspace('members:read')
def list_invitations():
    try:
        invitations = InvitationService.list_workspace_invitations(g.workspace_id)
        return success_response(data={"invitations": invitations, "total": len(invitations)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@workspaces_bp.route('/workspaces/invitations/info', methods=['GET', 'POST'])
@limiter.limit("30 per minute")
def get_invitation_info():
    token = request.args.get('token') if request.method == 'GET' else (request.get_json() or {}).get('token')
    if not token:
        return error_response("Field 'token' is required.", "VALIDATION_ERROR", 400)
    try:
        inv = InvitationService.get_invitation_by_token(token)
        ws = Workspace.query.get(inv.workspace_id)
        return success_response(data={
            "id": inv.id,
            "workspace_id": inv.workspace_id,
            "workspace_name": ws.name if ws else "Business Workspace",
            "email": inv.email,
            "role": inv.role,
            "status": inv.status,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@workspaces_bp.route('/workspaces/invitations/accept', methods=['POST'])
@require_auth
@limiter.limit("15 per minute")
def accept_invitation():
    data = request.get_json() or {}
    token = data.get('token')
    if not token:
        return error_response("Field 'token' is required.", "VALIDATION_ERROR", 400)

    try:
        result = InvitationService.accept_invitation(
            token=token,
            user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data=result,
            message="Invitation accepted successfully.",
            status_code=200
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@workspaces_bp.route('/workspaces/invitations/<invitation_id>/revoke', methods=['POST'])
@require_workspace('members:remove')
def revoke_invitation(invitation_id):
    try:
        InvitationService.revoke_invitation(
            workspace_id=g.workspace_id,
            invitation_id=invitation_id,
            actor_user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"revoked": True},
            message="Invitation revoked successfully."
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
