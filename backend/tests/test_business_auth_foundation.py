"""
DeadlineOS Business OS — Stage-3 B1 Auth Foundation Tests
=========================================================
Tests workspace creation, 5-tier RBAC, invitation lifecycle, and Personal Auth freeze integrity.
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone

from models.user import User
from models.business import Workspace, WorkspaceMember, WorkspaceInvitation, AuditEvent
from services.business.workspace_service import WorkspaceService
from services.business.invitation_service import InvitationService
from middleware.business_context import ROLE_PERMISSIONS


def test_rbac_five_tier_permissions():
    """Verify that only the 5 approved roles exist and their permissions are correct."""
    approved_roles = {'OWNER', 'ADMIN', 'MEMBER', 'ACCOUNTANT', 'VIEWER'}
    assert set(ROLE_PERMISSIONS.keys()) == approved_roles

    # OWNER has full governance
    assert 'workspace:delete' in ROLE_PERMISSIONS['OWNER']
    assert 'members:role_update' in ROLE_PERMISSIONS['OWNER']

    # ADMIN cannot delete workspace or update owner role
    assert 'workspace:delete' not in ROLE_PERMISSIONS['ADMIN']
    assert 'members:role_update' not in ROLE_PERMISSIONS['ADMIN']
    assert 'members:invite' in ROLE_PERMISSIONS['ADMIN']

    # MEMBER has operational permissions but no member management
    assert 'staging:create' in ROLE_PERMISSIONS['MEMBER']
    assert 'members:invite' not in ROLE_PERMISSIONS['MEMBER']

    # ACCOUNTANT has audit/read and transaction read, but no operational mutations
    assert 'audit:read' in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'transaction:read' in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'staging:create' not in ROLE_PERMISSIONS['ACCOUNTANT']

    # VIEWER has read only
    assert 'workspace:read' in ROLE_PERMISSIONS['VIEWER']
    assert 'transaction:create' not in ROLE_PERMISSIONS['VIEWER']


def test_atomic_workspace_creation(app):
    """Verify that creating a workspace atomically creates an active OWNER membership and audit log."""
    with app.app_context():
        user_id = str(uuid.uuid4())
        user = User(id=user_id, email="ceo@starlight.com", full_name="Starlight CEO")
        from database.db import db
        db.session.add(user)
        db.session.commit()

        ws = WorkspaceService.create_workspace(
            name="Starlight Ventures",
            owner_user_id=user_id,
            legal_name="Starlight Ventures Private Limited",
            tax_identifier="GSTIN29ABCDE1234F1Z5",
            base_currency="INR"
        )

        assert ws.id is not None
        assert ws.status == "ACTIVE"

        # Check membership
        member = WorkspaceMember.query.filter_by(workspace_id=ws.id, user_id=user_id).first()
        assert member is not None
        assert member.role == "OWNER"
        assert member.status == "ACTIVE"

        # Check audit event
        audit = AuditEvent.query.filter_by(workspace_id=ws.id, action="WORKSPACE_CREATED").first()
        assert audit is not None
        assert audit.actor_user_id == user_id


def test_invitation_lifecycle_and_acceptance(app):
    """Verify invitation creation, token lookup, atomic acceptance, and replay prevention."""
    with app.app_context():
        from database.db import db

        owner_id = str(uuid.uuid4())
        invitee_id = str(uuid.uuid4())

        owner = User(id=owner_id, email="owner@starlight.com", full_name="Owner User")
        invitee = User(id=invitee_id, email="accountant@starlight.com", full_name="Accountant User")
        db.session.add_all([owner, invitee])
        db.session.commit()

        ws = WorkspaceService.create_workspace(name="Starlight Finance", owner_user_id=owner_id)

        # 1. Create Invitation
        inv = InvitationService.create_invitation(
            workspace_id=ws.id,
            actor_user_id=owner_id,
            email="accountant@starlight.com",
            role="ACCOUNTANT"
        )

        assert inv.id is not None
        assert inv.status == "PENDING"
        assert len(inv.token) >= 32
        assert not inv.is_expired()

        # 2. Get by Token
        fetched_inv = InvitationService.get_invitation_by_token(inv.token)
        assert fetched_inv.id == inv.id
        assert fetched_inv.role == "ACCOUNTANT"

        # 3. Accept Invitation
        result = InvitationService.accept_invitation(token=inv.token, user_id=invitee_id)
        assert result["workspace"]["id"] == ws.id
        assert result["member"]["role"] == "ACCOUNTANT"
        assert result["member"]["status"] == "ACTIVE"

        # Verify DB state
        accepted_inv = WorkspaceInvitation.query.get(inv.id)
        assert accepted_inv.status == "ACCEPTED"

        member = WorkspaceMember.query.filter_by(workspace_id=ws.id, user_id=invitee_id).first()
        assert member is not None
        assert member.role == "ACCOUNTANT"

        # 4. Prevent Replay Acceptance
        with pytest.raises(Exception) as exc_info:
            InvitationService.accept_invitation(token=inv.token, user_id=invitee_id)
        assert "already been accepted" in str(exc_info.value)


def test_invitation_revocation(app):
    """Verify that an invitation can be revoked and cannot subsequently be accepted."""
    with app.app_context():
        from database.db import db

        owner_id = str(uuid.uuid4())
        invitee_id = str(uuid.uuid4())

        owner = User(id=owner_id, email="lead@corp.com", full_name="Lead")
        invitee = User(id=invitee_id, email="contractor@corp.com", full_name="Contractor")
        db.session.add_all([owner, invitee])
        db.session.commit()

        ws = WorkspaceService.create_workspace(name="Dev Studio", owner_user_id=owner_id)

        inv = InvitationService.create_invitation(
            workspace_id=ws.id,
            actor_user_id=owner_id,
            email="contractor@corp.com",
            role="VIEWER"
        )

        # Revoke
        revoked = InvitationService.revoke_invitation(
            workspace_id=ws.id,
            invitation_id=inv.id,
            actor_user_id=owner_id
        )
        assert revoked is True

        # Acceptance must fail
        with pytest.raises(Exception) as exc_info:
            InvitationService.accept_invitation(token=inv.token, user_id=invitee_id)
        assert "revoked" in str(exc_info.value)
