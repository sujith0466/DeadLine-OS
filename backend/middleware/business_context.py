"""
DeadlineOS Business OS — Tenancy & RBAC Middleware
==================================================
Provides `@require_workspace(permission)` decorator for row-level
multi-tenant isolation and 5-tier RBAC enforcement.
"""

from functools import wraps
from flask import request, g
from utils.auth import require_auth
from utils.responses import error_response
from models.business import Workspace, WorkspaceMember


# 5-Tier RBAC Role-to-Permissions Mapping
ROLE_PERMISSIONS = {
    'OWNER': {
        'workspace:read',
        'workspace:update',
        'workspace:delete',
        'members:read',
        'members:invite',
        'members:role_update',
        'members:remove',
        'partners:read',
        'partners:create',
        'partners:update',
        'partners:archive',
        'audit:read',
        'staging:read',
        'staging:create',
        'staging:update',
        'staging:confirm',
        'staging:reject',
        'transaction:read',
        'transaction:create',
        'transaction:reverse',
        # C1 Operations permissions
        'tasks:read',
        'tasks:create',
        'tasks:update',
        'tasks:assign',
        'tasks:delete',
        'inventory:read',
        'inventory:create',
        'inventory:update',
        'inventory:adjust',
        'inventory:delete',
        'locations:read',
        'locations:create',
        'locations:update',
        # C2 Procurement permissions
        'procurement:read',
        'procurement:create',
        'procurement:update',
        'procurement:approve',
        'procurement:manage',
        'procurement:receive',
        'intelligence:read',
        'currency:read',
        'currency:write',
    },
    'ADMIN': {
        'workspace:read',
        'workspace:update',
        'members:read',
        'members:invite',
        'members:remove',
        'partners:read',
        'partners:create',
        'partners:update',
        'partners:archive',
        'audit:read',
        'staging:read',
        'staging:create',
        'staging:update',
        'staging:confirm',
        'staging:reject',
        'transaction:read',
        'transaction:create',
        'transaction:reverse',
        # C1 Operations permissions
        'tasks:read',
        'tasks:create',
        'tasks:update',
        'tasks:assign',
        'tasks:delete',
        'inventory:read',
        'inventory:create',
        'inventory:update',
        'inventory:adjust',
        'inventory:delete',
        'locations:read',
        'locations:create',
        'locations:update',
        # C2 Procurement permissions
        'procurement:read',
        'procurement:create',
        'procurement:update',
        'procurement:approve',
        'procurement:manage',
        'procurement:receive',
        'intelligence:read',
        'currency:read',
        'currency:write',
    },
    'MEMBER': {
        'workspace:read',
        'members:read',
        'partners:read',
        'partners:create',
        'partners:update',
        'staging:read',
        'staging:create',
        'staging:update',
        'staging:confirm',
        'staging:reject',
        'transaction:read',
        'transaction:create',
        # C1 Operations permissions
        'tasks:read',
        'tasks:create',
        'tasks:update',
        'tasks:assign',
        'inventory:read',
        'inventory:create',
        'inventory:update',
        'inventory:adjust',
        'locations:read',
        'locations:create',
        'locations:update',
        # C2 Procurement permissions
        'procurement:read',
        'procurement:create',
        'procurement:update',
        'procurement:receive',
        'intelligence:read',
        'currency:read',
    },
    'ACCOUNTANT': {
        'workspace:read',
        'members:read',
        'partners:read',
        'audit:read',
        'staging:read',
        'transaction:read',
        # C1 Operations permissions (Read-Only)
        'tasks:read',
        'inventory:read',
        'locations:read',
        # C2 Procurement permissions (Read-Only)
        'procurement:read',
        'intelligence:read',
        'currency:read',
        'currency:write',
    },
    'VIEWER': {
        'workspace:read',
        'members:read',
        'partners:read',
        'staging:read',
        # C1 Operations permissions (Read-Only)
        'tasks:read',
        'inventory:read',
        'locations:read',
        # C2 Procurement permissions (Read-Only)
        'procurement:read',
        'intelligence:read',
        'currency:read',
    },
}


def require_workspace(permission=None):
    """
    Decorator that enforces two-stage authorization:
    1. Authenticates user (via @require_auth if not already run)
    2. Resolves X-Workspace-Id header and validates active membership
    3. Enforces 5-tier RBAC permission checks
    4. Populates g.workspace_id, g.workspace, g.member, and g.member_role
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            # 1. Extract Workspace ID from Header or Route
            workspace_id = request.headers.get('X-Workspace-Id') or kwargs.get('workspace_id')
            if not workspace_id:
                return error_response(
                    message="Missing required 'X-Workspace-Id' header.",
                    error_code="WORKSPACE_ID_REQUIRED",
                    status_code=400
                )

            # 2. Query Workspace Record
            workspace = Workspace.query.filter_by(id=workspace_id).first()
            if not workspace:
                return error_response(
                    message="Workspace not found.",
                    error_code="WORKSPACE_NOT_FOUND",
                    status_code=404
                )

            if workspace.status != 'ACTIVE':
                return error_response(
                    message="Workspace is not active.",
                    error_code="WORKSPACE_INACTIVE",
                    status_code=403
                )

            # 3. Query Membership for Authenticated User
            user_id = g.get('user_id')
            if not user_id:
                return error_response(
                    message="User authentication required.",
                    error_code="UNAUTHORIZED",
                    status_code=401
                )

            member = WorkspaceMember.query.filter_by(
                workspace_id=workspace.id,
                user_id=user_id
            ).first()

            if not member or member.status != 'ACTIVE':
                return error_response(
                    message="Access denied: You are not an active member of this workspace.",
                    error_code="WORKSPACE_ACCESS_DENIED",
                    status_code=403
                )

            # 4. Evaluate RBAC Permission
            if permission:
                allowed_permissions = ROLE_PERMISSIONS.get(member.role, set())
                if permission not in allowed_permissions:
                    return error_response(
                        message=f"Access denied: Role '{member.role}' lacks permission '{permission}'.",
                        error_code="PERMISSION_DENIED",
                        status_code=403
                    )

            # 5. Populate Business Context
            g.workspace_id = workspace.id
            g.workspace = workspace
            g.member = member
            g.member_role = member.role

            return f(*args, **kwargs)

        return decorated_function
    return decorator
