"""
DeadlineOS Business OS — Workspace Invitation Service
=====================================================
Handles generation, validation, acceptance, and revocation of workspace invitations.
Enforces atomic database transactions and audit logging.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from database.db import db
from models.business import Workspace, WorkspaceMember, WorkspaceInvitation, AuditEvent
from models.user import User
from utils.errors import APIError


class InvitationService:
    """
    Manages the lifecycle of Business Workspace invitations.
    """

    @staticmethod
    def create_invitation(
        workspace_id: str,
        actor_user_id: str,
        email: str,
        role: str = 'MEMBER',
        expires_in_days: int = 7,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> WorkspaceInvitation:
        """
        Create a secure tokenized invitation to join a workspace with an assigned RBAC role.
        """
        email_clean = email.strip().lower()
        if not email_clean or '@' not in email_clean:
            raise APIError("A valid email address is required.", "INVALID_EMAIL", 400)

        valid_roles = {'ADMIN', 'MEMBER', 'ACCOUNTANT', 'VIEWER'}
        if role not in valid_roles:
            raise APIError(f"Invalid role '{role}'. Allowed roles: {', '.join(valid_roles)}", "INVALID_ROLE", 400)

        # Verify workspace exists and is active
        workspace = Workspace.query.filter_by(id=workspace_id).first()
        if not workspace or workspace.status != 'ACTIVE':
            raise APIError("Workspace not found or inactive.", "WORKSPACE_NOT_FOUND", 404)

        # Check if user is already an active member of this workspace
        existing_user = User.query.filter_by(email=email_clean).first()
        if existing_user:
            existing_member = WorkspaceMember.query.filter_by(
                workspace_id=workspace_id,
                user_id=existing_user.id
            ).first()
            if existing_member and existing_member.status == 'ACTIVE':
                raise APIError(f"User '{email_clean}' is already an active member of this workspace.", "ALREADY_MEMBER", 409)

        # Check for existing pending invitation to this email
        pending_inv = WorkspaceInvitation.query.filter_by(
            workspace_id=workspace_id,
            email=email_clean,
            status='PENDING'
        ).first()

        if pending_inv and not pending_inv.is_expired():
            # Refresh expiration and return existing pending invite
            pending_inv.expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            pending_inv.role = role
            pending_inv.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return pending_inv

        # Generate 64-char crypto secure random token
        token = secrets.token_urlsafe(48)[:64]
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        inv_id = str(uuid.uuid4())
        invitation = WorkspaceInvitation(
            id=inv_id,
            workspace_id=workspace_id,
            email=email_clean,
            role=role,
            token=token,
            status='PENDING',
            invited_by_user_id=actor_user_id,
            expires_at=expires_at
        )
        db.session.add(invitation)

        # Audit Event
        audit = AuditEvent(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="MEMBER_INVITED",
            entity_type="WorkspaceInvitation",
            entity_id=inv_id,
            after_state={"email": email_clean, "role": role, "expires_at": expires_at.isoformat()},
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(audit)
        db.session.commit()

        return invitation

    @staticmethod
    def get_invitation_by_token(token: str) -> WorkspaceInvitation:
        """
        Fetch invitation by token and validate that it is active and not expired.
        """
        if not token or len(token) < 16:
            raise APIError("Invalid invitation token.", "INVALID_TOKEN", 400)

        inv = WorkspaceInvitation.query.filter_by(token=token).first()
        if not inv:
            raise APIError("Invitation not found.", "INVITATION_NOT_FOUND", 404)

        if inv.status == 'REVOKED':
            raise APIError("This invitation has been revoked by the workspace administrator.", "INVITATION_REVOKED", 410)

        if inv.status == 'ACCEPTED':
            raise APIError("This invitation has already been accepted.", "INVITATION_ALREADY_ACCEPTED", 409)

        if inv.is_expired():
            inv.status = 'EXPIRED'
            db.session.commit()
            raise APIError("This invitation has expired. Please request a new invitation.", "INVITATION_EXPIRED", 410)

        return inv

    @staticmethod
    def accept_invitation(
        token: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Accept an invitation atomically and provision the WorkspaceMember record.
        """
        inv = InvitationService.get_invitation_by_token(token)

        user = User.query.get(user_id)
        if not user:
            raise APIError("User identity not found in application database.", "USER_NOT_FOUND", 404)

        workspace = Workspace.query.filter_by(id=inv.workspace_id).first()
        if not workspace or workspace.status != 'ACTIVE':
            raise APIError("The workspace for this invitation is no longer active.", "WORKSPACE_INACTIVE", 403)

        try:
            # Check if membership already exists (e.g. was suspended or rejoining)
            member = WorkspaceMember.query.filter_by(
                workspace_id=inv.workspace_id,
                user_id=user_id
            ).first()

            if member:
                member.role = inv.role
                member.status = 'ACTIVE'
                member.updated_at = datetime.now(timezone.utc)
            else:
                member = WorkspaceMember(
                    id=str(uuid.uuid4()),
                    workspace_id=inv.workspace_id,
                    user_id=user_id,
                    role=inv.role,
                    status='ACTIVE'
                )
                db.session.add(member)

            # Mark invitation as accepted
            inv.status = 'ACCEPTED'
            inv.updated_at = datetime.now(timezone.utc)

            # Write Audit Event
            audit = AuditEvent(
                workspace_id=inv.workspace_id,
                actor_user_id=user_id,
                action="INVITATION_ACCEPTED",
                entity_type="WorkspaceMember",
                entity_id=member.id,
                after_state={"user_id": user_id, "role": inv.role, "email": inv.email},
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(audit)
            db.session.commit()

            return {
                "workspace": workspace.serialize(),
                "member": member.serialize(),
                "role": member.role
            }
        except Exception as e:
            db.session.rollback()
            raise APIError(f"Failed to accept invitation: {str(e)}", "INTERNAL_ERROR", 500)

    @staticmethod
    def revoke_invitation(
        workspace_id: str,
        invitation_id: str,
        actor_user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Revoke a pending invitation.
        """
        inv = WorkspaceInvitation.query.filter_by(
            id=invitation_id,
            workspace_id=workspace_id
        ).first()

        if not inv:
            raise APIError("Invitation not found in this workspace.", "NOT_FOUND", 404)

        if inv.status != 'PENDING':
            raise APIError(f"Cannot revoke invitation with status '{inv.status}'.", "INVALID_STATE", 400)

        inv.status = 'REVOKED'
        inv.updated_at = datetime.now(timezone.utc)

        audit = AuditEvent(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="INVITATION_REVOKED",
            entity_type="WorkspaceInvitation",
            entity_id=inv.id,
            before_state={"status": "PENDING"},
            after_state={"status": "REVOKED"},
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(audit)
        db.session.commit()
        return True

    @staticmethod
    def list_workspace_invitations(workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all invitations for a workspace.
        """
        invs = WorkspaceInvitation.query.filter_by(workspace_id=workspace_id).order_by(
            WorkspaceInvitation.created_at.desc()
        ).all()
        return [inv.serialize() for inv in invs]
