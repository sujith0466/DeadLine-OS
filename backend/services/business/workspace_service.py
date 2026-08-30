"""
DeadlineOS Business OS — Workspace Service
==========================================
Manages Workspace creation (with atomic OWNER provisioning),
membership invitations, role updates, and audit emission.
"""

from database.db import db
from models.user import User
from models.business import Workspace, WorkspaceMember
from services.business.audit_service import AuditService
from utils.errors import APIError


class WorkspaceService:
    @staticmethod
    def create_workspace(
        name: str,
        owner_user_id: str,
        legal_name: str = None,
        tax_identifier: str = None,
        base_currency: str = 'INR',
        timezone: str = 'Asia/Kolkata',
        ip_address: str = None,
        user_agent: str = None
    ) -> Workspace:
        if not name or not name.strip():
            raise APIError("Workspace name is required.", code="VALIDATION_ERROR", status=400)

        # 1. Create Workspace
        workspace = Workspace(
            name=name.strip(),
            legal_name=legal_name.strip() if legal_name else None,
            tax_identifier=tax_identifier.strip() if tax_identifier else None,
            base_currency=base_currency.strip().upper() if base_currency else 'INR',
            timezone=timezone.strip() if timezone else 'Asia/Kolkata',
            status='ACTIVE'
        )
        db.session.add(workspace)
        db.session.flush()  # Obtain workspace.id

        # 2. Create Atomic OWNER Membership
        owner_membership = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_user_id,
            role='OWNER',
            status='ACTIVE'
        )
        db.session.add(owner_membership)
        db.session.commit()

        # 3. Log Audit Event
        AuditService.log_event(
            workspace_id=workspace.id,
            actor_user_id=owner_user_id,
            action='WORKSPACE_CREATED',
            entity_type='WORKSPACE',
            entity_id=workspace.id,
            after_state=workspace.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return workspace

    @staticmethod
    def get_user_workspaces(user_id: str):
        """
        Returns all workspaces where the user holds an active membership.
        """
        memberships = WorkspaceMember.query.filter_by(
            user_id=user_id,
            status='ACTIVE'
        ).all()

        results = []
        for m in memberships:
            if m.workspace and m.workspace.status == 'ACTIVE':
                ws_data = m.workspace.serialize()
                ws_data['member_role'] = m.role
                ws_data['member_status'] = m.status
                results.append(ws_data)
        return results

    @staticmethod
    def update_workspace(
        workspace_id: str,
        actor_user_id: str,
        updates: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> Workspace:
        workspace = Workspace.query.filter_by(id=workspace_id).first()
        if not workspace:
            raise APIError("Workspace not found.", code="WORKSPACE_NOT_FOUND", status=404)

        before_state = workspace.serialize()

        if 'name' in updates and updates['name']:
            workspace.name = updates['name'].strip()
        if 'legal_name' in updates:
            workspace.legal_name = updates['legal_name'].strip() if updates['legal_name'] else None
        if 'tax_identifier' in updates:
            workspace.tax_identifier = updates['tax_identifier'].strip() if updates['tax_identifier'] else None
        if 'base_currency' in updates and updates['base_currency']:
            workspace.base_currency = updates['base_currency'].strip().upper()
        if 'timezone' in updates and updates['timezone']:
            workspace.timezone = updates['timezone'].strip()

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace.id,
            actor_user_id=actor_user_id,
            action='WORKSPACE_UPDATED',
            entity_type='WORKSPACE',
            entity_id=workspace.id,
            before_state=before_state,
            after_state=workspace.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return workspace

    @staticmethod
    def invite_member(
        workspace_id: str,
        actor_user_id: str,
        email: str,
        role: str = 'MEMBER',
        ip_address: str = None,
        user_agent: str = None
    ) -> WorkspaceMember:
        if not email or not email.strip():
            raise APIError("Target user email is required.", code="VALIDATION_ERROR", status=400)

        role = role.upper() if role else 'MEMBER'
        if role not in ('OWNER', 'ADMIN', 'MEMBER', 'ACCOUNTANT', 'VIEWER'):
            raise APIError(f"Invalid role '{role}'.", code="VALIDATION_ERROR", status=400)

        # Lookup user by email in system
        target_user = User.query.filter_by(email=email.strip().lower()).first()
        if not target_user:
            raise APIError(f"User with email '{email.strip()}' does not have a DeadlineOS account.", code="USER_NOT_FOUND", status=404)

        # Check existing membership
        existing = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=target_user.id
        ).first()

        if existing:
            if existing.status == 'ACTIVE':
                raise APIError(f"User is already an active member of this workspace.", code="MEMBER_ALREADY_EXISTS", status=409)
            elif existing.status in ('INVITED', 'SUSPENDED'):
                existing.status = 'ACTIVE'
                existing.role = role
                db.session.commit()
                return existing

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=target_user.id,
            role=role,
            status='ACTIVE'
        )
        db.session.add(member)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='MEMBER_INVITED',
            entity_type='WORKSPACE_MEMBER',
            entity_id=member.id,
            after_state=member.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return member

    @staticmethod
    def update_member_role(
        workspace_id: str,
        member_id: str,
        actor_user_id: str,
        new_role: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> WorkspaceMember:
        new_role = new_role.upper() if new_role else ''
        if new_role not in ('OWNER', 'ADMIN', 'MEMBER', 'ACCOUNTANT', 'VIEWER'):
            raise APIError(f"Invalid role '{new_role}'.", code="VALIDATION_ERROR", status=400)

        member = WorkspaceMember.query.filter_by(
            id=member_id,
            workspace_id=workspace_id
        ).first()
        if not member:
            raise APIError("Workspace member not found.", code="MEMBER_NOT_FOUND", status=404)

        before_state = member.serialize()

        # Prevent demoting the last active OWNER
        if member.role == 'OWNER' and new_role != 'OWNER':
            active_owners = WorkspaceMember.query.filter_by(
                workspace_id=workspace_id,
                role='OWNER',
                status='ACTIVE'
            ).count()
            if active_owners <= 1:
                raise APIError("Cannot demote the last active OWNER of the workspace.", code="LAST_OWNER_PROTECTION", status=400)

        member.role = new_role
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='MEMBER_ROLE_UPDATED',
            entity_type='WORKSPACE_MEMBER',
            entity_id=member.id,
            before_state=before_state,
            after_state=member.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return member

    @staticmethod
    def update_member_status(
        workspace_id: str,
        member_id: str,
        actor_user_id: str,
        new_status: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> WorkspaceMember:
        new_status = new_status.upper() if new_status else ''
        if new_status not in ('ACTIVE', 'SUSPENDED'):
            raise APIError(f"Invalid status '{new_status}'. Allowed: ACTIVE, SUSPENDED", code="VALIDATION_ERROR", status=400)

        member = WorkspaceMember.query.filter_by(
            id=member_id,
            workspace_id=workspace_id
        ).first()
        if not member:
            raise APIError("Workspace member not found.", code="MEMBER_NOT_FOUND", status=404)

        if member.user_id == actor_user_id and new_status == 'SUSPENDED':
            raise APIError("You cannot suspend your own workspace membership.", code="SELF_SUSPENSION_BLOCKED", status=400)

        if member.role == 'OWNER' and new_status == 'SUSPENDED':
            active_owners = WorkspaceMember.query.filter_by(
                workspace_id=workspace_id,
                role='OWNER',
                status='ACTIVE'
            ).count()
            if active_owners <= 1:
                raise APIError("Cannot suspend the last active OWNER of the workspace.", code="LAST_OWNER_PROTECTION", status=400)

        before_state = member.serialize()
        member.status = new_status
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='MEMBER_STATUS_UPDATED',
            entity_type='WORKSPACE_MEMBER',
            entity_id=member.id,
            before_state=before_state,
            after_state=member.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return member

    @staticmethod
    def remove_member(
        workspace_id: str,
        member_id: str,
        actor_user_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        member = WorkspaceMember.query.filter_by(
            id=member_id,
            workspace_id=workspace_id
        ).first()
        if not member:
            raise APIError("Workspace member not found.", code="MEMBER_NOT_FOUND", status=404)

        if member.user_id == actor_user_id:
            raise APIError("You cannot remove yourself via member administration. Use workspace leave if supported.", code="SELF_REMOVAL_BLOCKED", status=400)

        if member.role == 'OWNER':
            active_owners = WorkspaceMember.query.filter_by(
                workspace_id=workspace_id,
                role='OWNER',
                status='ACTIVE'
            ).count()
            if active_owners <= 1:
                raise APIError("Cannot remove the last active OWNER of the workspace.", code="LAST_OWNER_PROTECTION", status=400)

        before_state = member.serialize()
        db.session.delete(member)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='MEMBER_REMOVED',
            entity_type='WORKSPACE_MEMBER',
            entity_id=member_id,
            before_state=before_state,
            after_state={"status": "REMOVED"},
            ip_address=ip_address,
            user_agent=user_agent
        )
        return True

    @staticmethod
    def get_workspace_members(workspace_id: str):
        members = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id
        ).all()
        return [m.serialize() for m in members]

    @staticmethod
    def get_workspace_by_id_for_user(workspace_id: str, user_id: str) -> dict:
        member = WorkspaceMember.query.filter_by(
            workspace_id=workspace_id,
            user_id=user_id
        ).first()
        if not member or member.status != 'ACTIVE':
            raise APIError("Workspace not found or you do not have permission to view it.", code="WORKSPACE_ACCESS_DENIED", status=403)

        workspace = Workspace.query.filter_by(id=workspace_id).first()
        if not workspace or workspace.status != 'ACTIVE':
            raise APIError("Workspace not found or inactive.", code="WORKSPACE_NOT_FOUND", status=404)

        ws_data = workspace.serialize()
        ws_data['member_role'] = member.role
        ws_data['member_status'] = member.status
        return ws_data
