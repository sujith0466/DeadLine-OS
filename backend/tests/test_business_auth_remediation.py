"""
DeadlineOS Business OS — R2 Remediation: Invitation Email Binding Tests
=======================================================================
Tests verifying that invitation acceptance enforces strict email binding
between the authenticated user's email and the invitation's target email.

These tests address FINDING-008 (P1) from the Final B1–B12 Release Audit
(2026-08-30).

Coverage:
    TC-01  Correct email accepts invitation → PASS
    TC-02  Wrong email is rejected → HTTP 403 / INVITATION_EMAIL_MISMATCH
    TC-03  Wrong-email rejection does NOT create membership
    TC-04  Wrong-email rejection does NOT consume (mark ACCEPTED) invitation
    TC-05  Invitation remains PENDING after wrong-email rejection
    TC-06  Correct user can subsequently accept after wrong-email attempt
    TC-07  Expired invitation rejected before email check
    TC-08  Revoked invitation rejected before email check
    TC-09  Already-accepted invitation rejected before email check
    TC-10  Case-insensitive email normalization works correctly
    TC-11  Whitespace-padded email in user record still matches
    TC-12  Existing invitation lifecycle tests remain compatible
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone

from database.db import db
from models.user import User
from models.business import Workspace, WorkspaceMember, WorkspaceInvitation
from services.business.workspace_service import WorkspaceService
from services.business.invitation_service import InvitationService
from utils.errors import APIError


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_user(email: str, full_name: str = "Test User") -> User:
    """Create and persist a User in the current session."""
    user = User(id=str(uuid.uuid4()), email=email, full_name=full_name)
    db.session.add(user)
    db.session.commit()
    return user


def _make_workspace_with_owner(owner_email: str, ws_name: str = "Test Workspace"):
    """Create a workspace and its OWNER user."""
    owner = _make_user(owner_email, "Workspace Owner")
    ws = WorkspaceService.create_workspace(name=ws_name, owner_user_id=owner.id)
    return owner, ws


def _make_invitation(ws_id: str, actor_id: str, invitee_email: str, role: str = "MEMBER"):
    """Create a PENDING invitation."""
    return InvitationService.create_invitation(
        workspace_id=ws_id,
        actor_user_id=actor_id,
        email=invitee_email,
        role=role
    )


def _make_expired_invitation(ws_id: str, actor_id: str, invitee_email: str) -> WorkspaceInvitation:
    """Create a PENDING invitation with expires_at in the past."""
    inv = InvitationService.create_invitation(
        workspace_id=ws_id,
        actor_user_id=actor_id,
        email=invitee_email,
        role="VIEWER"
    )
    # Force expiry
    inv.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    inv.status = "PENDING"
    db.session.commit()
    return inv


# ── TC-01 ──────────────────────────────────────────────────────────────────────

def test_r2_tc01_correct_email_accepts_invitation(app):
    """TC-01: Authenticated user whose email matches the invitation target can accept."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner01@corp.com", "Corp01")
        invitee = _make_user("member01@corp.com")
        inv = _make_invitation(ws.id, owner.id, "member01@corp.com", "MEMBER")

        result = InvitationService.accept_invitation(token=inv.token, user_id=invitee.id)

        assert result["workspace"]["id"] == ws.id
        assert result["member"]["role"] == "MEMBER"
        assert result["member"]["status"] == "ACTIVE"


# ── TC-02 ──────────────────────────────────────────────────────────────────────

def test_r2_tc02_wrong_email_is_rejected(app):
    """TC-02: Authenticated user with a different email must be rejected with 403."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner02@corp.com", "Corp02")
        _invitee = _make_user("intended@corp.com")
        attacker = _make_user("attacker@evil.com")
        inv = _make_invitation(ws.id, owner.id, "intended@corp.com", "ADMIN")

        with pytest.raises(APIError) as exc_info:
            InvitationService.accept_invitation(token=inv.token, user_id=attacker.id)

        err = exc_info.value
        assert err.status == 403
        assert err.code == "INVITATION_EMAIL_MISMATCH"
        # Verify generic message — does not expose intended email
        assert "not associated" in err.message.lower()
        assert "intended@corp.com" not in err.message


# ── TC-03 ──────────────────────────────────────────────────────────────────────

def test_r2_tc03_wrong_email_rejection_does_not_create_membership(app):
    """TC-03: A rejected wrong-email attempt must not provision WorkspaceMember."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner03@corp.com", "Corp03")
        _intended = _make_user("intended03@corp.com")
        attacker = _make_user("attacker03@evil.com")
        inv = _make_invitation(ws.id, owner.id, "intended03@corp.com", "MEMBER")

        try:
            InvitationService.accept_invitation(token=inv.token, user_id=attacker.id)
        except APIError:
            pass

        # No membership should exist for the attacker
        member = WorkspaceMember.query.filter_by(
            workspace_id=ws.id,
            user_id=attacker.id
        ).first()
        assert member is None, "Attacker must not have been granted workspace membership."


# ── TC-04 ──────────────────────────────────────────────────────────────────────

def test_r2_tc04_wrong_email_rejection_does_not_consume_invitation(app):
    """TC-04: A rejected wrong-email attempt must not mark the invitation ACCEPTED."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner04@corp.com", "Corp04")
        _intended = _make_user("intended04@corp.com")
        attacker = _make_user("attacker04@evil.com")
        inv = _make_invitation(ws.id, owner.id, "intended04@corp.com", "VIEWER")

        try:
            InvitationService.accept_invitation(token=inv.token, user_id=attacker.id)
        except APIError:
            pass

        db.session.expire_all()
        fresh_inv = WorkspaceInvitation.query.filter_by(id=inv.id).first()
        assert fresh_inv.status != "ACCEPTED", (
            "Invitation must not have been consumed by wrong-email rejection."
        )


# ── TC-05 ──────────────────────────────────────────────────────────────────────

def test_r2_tc05_invitation_remains_pending_after_wrong_email(app):
    """TC-05: Invitation must remain PENDING after a wrong-email rejection attempt."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner05@corp.com", "Corp05")
        _intended = _make_user("intended05@corp.com")
        attacker = _make_user("attacker05@evil.com")
        inv = _make_invitation(ws.id, owner.id, "intended05@corp.com", "ACCOUNTANT")

        try:
            InvitationService.accept_invitation(token=inv.token, user_id=attacker.id)
        except APIError:
            pass

        db.session.expire_all()
        fresh_inv = WorkspaceInvitation.query.filter_by(id=inv.id).first()
        assert fresh_inv.status == "PENDING"


# ── TC-06 ──────────────────────────────────────────────────────────────────────

def test_r2_tc06_correct_user_accepts_after_wrong_email_attempt(app):
    """TC-06: After a wrong-email rejection, the correct user can still accept."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner06@corp.com", "Corp06")
        intended = _make_user("intended06@corp.com")
        attacker = _make_user("attacker06@evil.com")
        inv = _make_invitation(ws.id, owner.id, "intended06@corp.com", "MEMBER")

        # Wrong-email attempt (should fail)
        try:
            InvitationService.accept_invitation(token=inv.token, user_id=attacker.id)
        except APIError:
            pass

        # Correct user should succeed
        result = InvitationService.accept_invitation(token=inv.token, user_id=intended.id)
        assert result["member"]["role"] == "MEMBER"
        assert result["member"]["status"] == "ACTIVE"

        db.session.expire_all()
        fresh_inv = WorkspaceInvitation.query.filter_by(id=inv.id).first()
        assert fresh_inv.status == "ACCEPTED"


# ── TC-07 ──────────────────────────────────────────────────────────────────────

def test_r2_tc07_expired_invitation_rejected(app):
    """TC-07: An expired invitation cannot be accepted (rejected before email check)."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner07@corp.com", "Corp07")
        intended = _make_user("intended07@corp.com")
        inv = _make_expired_invitation(ws.id, owner.id, "intended07@corp.com")

        with pytest.raises(APIError) as exc_info:
            InvitationService.accept_invitation(token=inv.token, user_id=intended.id)

        assert "expired" in exc_info.value.message.lower()


# ── TC-08 ──────────────────────────────────────────────────────────────────────

def test_r2_tc08_revoked_invitation_rejected(app):
    """TC-08: A revoked invitation cannot be accepted."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner08@corp.com", "Corp08")
        intended = _make_user("intended08@corp.com")
        inv = _make_invitation(ws.id, owner.id, "intended08@corp.com", "VIEWER")

        InvitationService.revoke_invitation(
            workspace_id=ws.id,
            invitation_id=inv.id,
            actor_user_id=owner.id
        )

        with pytest.raises(APIError) as exc_info:
            InvitationService.accept_invitation(token=inv.token, user_id=intended.id)

        assert "revoked" in exc_info.value.message.lower()


# ── TC-09 ──────────────────────────────────────────────────────────────────────

def test_r2_tc09_already_accepted_invitation_rejected_on_replay(app):
    """TC-09: An already-accepted invitation cannot be replayed."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner09@corp.com", "Corp09")
        intended = _make_user("intended09@corp.com")
        inv = _make_invitation(ws.id, owner.id, "intended09@corp.com", "MEMBER")

        InvitationService.accept_invitation(token=inv.token, user_id=intended.id)

        with pytest.raises(APIError) as exc_info:
            InvitationService.accept_invitation(token=inv.token, user_id=intended.id)

        assert "already been accepted" in exc_info.value.message.lower()


# ── TC-10 ──────────────────────────────────────────────────────────────────────

def test_r2_tc10_case_insensitive_email_normalization_passes(app):
    """TC-10: Email comparison is case-insensitive — 'User@Corp.COM' matches 'user@corp.com'."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner10@corp.com", "Corp10")
        # Invitation was created with lowercase (as create_invitation normalizes)
        inv = _make_invitation(ws.id, owner.id, "uppercaseuser@corp.com", "MEMBER")

        # User record stored with mixed case (as Supabase might store it)
        invitee = _make_user("UpperCaseUser@Corp.COM")

        # Should succeed — normalization brings both to lowercase
        result = InvitationService.accept_invitation(token=inv.token, user_id=invitee.id)
        assert result["member"]["status"] == "ACTIVE"


# ── TC-11 ──────────────────────────────────────────────────────────────────────

def test_r2_tc11_whitespace_padded_email_matches(app):
    """TC-11: Whitespace padding in user.email is stripped before comparison."""
    with app.app_context():
        owner, ws = _make_workspace_with_owner("owner11@corp.com", "Corp11")
        inv = _make_invitation(ws.id, owner.id, "padded@corp.com", "VIEWER")

        # Simulate a user record with leading/trailing whitespace in email
        invitee = User(
            id=str(uuid.uuid4()),
            email="  padded@corp.com  ",
            full_name="Padded User"
        )
        db.session.add(invitee)
        db.session.commit()

        result = InvitationService.accept_invitation(token=inv.token, user_id=invitee.id)
        assert result["member"]["status"] == "ACTIVE"


# ── TC-12 ──────────────────────────────────────────────────────────────────────

def test_r2_tc12_existing_lifecycle_compatibility(app):
    """TC-12: Pre-remediation invitation lifecycle tests remain compatible with email binding."""
    with app.app_context():
        owner_id = str(uuid.uuid4())
        invitee_id = str(uuid.uuid4())

        owner = User(id=owner_id, email="legacy_owner@starlight.com", full_name="Legacy Owner")
        # Invitee email matches the invitation target — binding satisfied
        invitee = User(id=invitee_id, email="legacy_accountant@starlight.com", full_name="Legacy Accountant")
        db.session.add_all([owner, invitee])
        db.session.commit()

        ws = WorkspaceService.create_workspace(name="Legacy Finance Workspace", owner_user_id=owner_id)

        inv = InvitationService.create_invitation(
            workspace_id=ws.id,
            actor_user_id=owner_id,
            email="legacy_accountant@starlight.com",
            role="ACCOUNTANT"
        )

        assert inv.status == "PENDING"
        assert len(inv.token) >= 32

        # Accept — should pass with matching email
        result = InvitationService.accept_invitation(token=inv.token, user_id=invitee_id)
        assert result["workspace"]["id"] == ws.id
        assert result["member"]["role"] == "ACCOUNTANT"

        # Replay — must fail
        with pytest.raises(APIError) as exc_info:
            InvitationService.accept_invitation(token=inv.token, user_id=invitee_id)
        assert "already been accepted" in exc_info.value.message.lower()
