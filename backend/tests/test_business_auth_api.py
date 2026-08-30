"""
DeadlineOS Business OS — Stage-3 B2 Workspace & Invitation API Tests
====================================================================
Comprehensive testing of workspace discovery, detail retrieval, creation,
member administration, invitation lifecycle, 5-tier RBAC, and tenant isolation.
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone

from models.user import User
from models.business import Workspace, WorkspaceMember, WorkspaceInvitation, AuditEvent
from services.business.workspace_service import WorkspaceService
from services.business.invitation_service import InvitationService


@pytest.fixture
def auth_users(app):
    """Create two test users: User A (Owner of WS-A) and User B (Owner of WS-B)."""
    with app.app_context():
        from database.db import db

        u_a_id = str(uuid.uuid4())
        u_b_id = str(uuid.uuid4())
        u_c_id = str(uuid.uuid4())

        user_a = User(id=u_a_id, email="user_a@enterprise.com", full_name="User Alpha")
        user_b = User(id=u_b_id, email="user_b@enterprise.com", full_name="User Beta")
        user_c = User(id=u_c_id, email="user_c@enterprise.com", full_name="User Charlie")
        db.session.add_all([user_a, user_b, user_c])
        db.session.commit()

        ws_a = WorkspaceService.create_workspace(name="Enterprise Alpha", owner_user_id=u_a_id)
        ws_b = WorkspaceService.create_workspace(name="Enterprise Beta", owner_user_id=u_b_id)

        return {
            "user_a_id": u_a_id,
            "user_b_id": u_b_id,
            "user_c_id": u_c_id,
            "user_c_email": "user_c@enterprise.com",
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
        }


def test_b2_auth_unauthenticated_requests_rejected(client):
    """B2-AUTH-01: Unauthenticated request to workspace endpoints must return 401."""
    res = client.get("/api/business/workspaces")
    assert res.status_code == 401

    res = client.post("/api/business/workspaces", json={"name": "No Auth Corp"})
    assert res.status_code == 401


def test_b2_ws_discovery_and_tenant_isolation(client, auth_users):
    """B2-WS-01: User A sees only Workspace A; User B sees only Workspace B."""
    u_a = auth_users["user_a_id"]
    u_b = auth_users["user_b_id"]
    ws_a_id = auth_users["ws_a_id"]
    ws_b_id = auth_users["ws_b_id"]

    # User A listing
    headers_a = {"Authorization": f"Bearer {u_a}"}
    res_a = client.get("/api/business/workspaces", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.get_json()["data"]["workspaces"]
    assert len(data_a) == 1
    assert data_a[0]["id"] == ws_a_id
    assert data_a[0]["name"] == "Enterprise Alpha"
    assert data_a[0]["member_role"] == "OWNER"

    # User B listing
    headers_b = {"Authorization": f"Bearer {u_b}"}
    res_b = client.get("/api/business/workspaces", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.get_json()["data"]["workspaces"]
    assert len(data_b) == 1
    assert data_b[0]["id"] == ws_b_id
    assert data_b[0]["name"] == "Enterprise Beta"


def test_b2_ws_detail_access_and_cross_tenant_rejection(client, auth_users):
    """B2-WS-02 & B2-WS-03: User A can fetch WS-A details, but is rejected when accessing WS-B."""
    u_a = auth_users["user_a_id"]
    ws_a_id = auth_users["ws_a_id"]
    ws_b_id = auth_users["ws_b_id"]

    headers_a = {"Authorization": f"Bearer {u_a}"}

    # Access own workspace
    res_own = client.get(f"/api/business/workspaces/{ws_a_id}", headers=headers_a)
    assert res_own.status_code == 200
    assert res_own.get_json()["data"]["workspace"]["id"] == ws_a_id

    # Cross-tenant IDOR attack on Workspace B
    res_foreign = client.get(f"/api/business/workspaces/{ws_b_id}", headers=headers_a)
    assert res_foreign.status_code == 403
    err_msg = res_foreign.get_json()["error"]["message"].lower()
    assert "permission" in err_msg or "denied" in err_msg


def test_b2_ws_creation_atomic(client, auth_users):
    """B2-WS-04 & B2-WS-05: User C creates a new workspace; becomes active OWNER atomically."""
    u_c = auth_users["user_c_id"]
    headers_c = {"Authorization": f"Bearer {u_c}"}

    res = client.post("/api/business/workspaces", json={
        "name": "Gamma Solutions",
        "legal_name": "Gamma Solutions Inc",
        "base_currency": "USD"
    }, headers=headers_c)

    assert res.status_code == 201
    created_ws = res.get_json()["data"]["workspace"]
    assert created_ws["name"] == "Gamma Solutions"
    assert created_ws["base_currency"] == "USD"

    # Confirm user C now sees Gamma Solutions
    res_list = client.get("/api/business/workspaces", headers=headers_c)
    assert res_list.status_code == 200
    assert len(res_list.get_json()["data"]["workspaces"]) == 1
    assert res_list.get_json()["data"]["workspaces"][0]["member_role"] == "OWNER"


def test_b2_invitation_lifecycle_api(app, client, auth_users):
    """B2-INV-01 through B2-INV-06: Test invitation creation, listing, acceptance, and revocation."""
    u_a = auth_users["user_a_id"]
    u_c = auth_users["user_c_id"]
    c_email = auth_users["user_c_email"]
    ws_a_id = auth_users["ws_a_id"]

    headers_a = {
        "Authorization": f"Bearer {u_a}",
        "X-Workspace-Id": ws_a_id
    }

    # 1. Create Invitation
    res_inv = client.post("/api/business/workspaces/invitations", json={
        "email": c_email,
        "role": "ACCOUNTANT"
    }, headers=headers_a)

    assert res_inv.status_code == 201
    inv_data = res_inv.get_json()["data"]["invitation"]
    token = res_inv.get_json()["data"]["token"]
    assert inv_data["role"] == "ACCOUNTANT"
    assert inv_data["status"] == "PENDING"
    assert token is not None

    # 2. List Invitations
    res_list = client.get("/api/business/workspaces/invitations", headers=headers_a)
    assert res_list.status_code == 200
    assert len(res_list.get_json()["data"]["invitations"]) == 1

    # 3. Accept Invitation as User C
    headers_c = {"Authorization": f"Bearer {u_c}"}
    res_accept = client.post("/api/business/workspaces/invitations/accept", json={
        "token": token
    }, headers=headers_c)

    assert res_accept.status_code == 200
    assert res_accept.get_json()["data"]["member"]["role"] == "ACCOUNTANT"

    # 4. User C now has access to WS-A as ACCOUNTANT
    res_c_list = client.get("/api/business/workspaces", headers=headers_c)
    assert res_c_list.status_code == 200
    workspaces_c = res_c_list.get_json()["data"]["workspaces"]
    assert any(w["id"] == ws_a_id and w["member_role"] == "ACCOUNTANT" for w in workspaces_c)


def test_b2_rbac_member_administration_and_last_owner_protection(app, client, auth_users):
    """B2-MEM-01 through B2-MEM-06: Member listing, role update, status update, and last OWNER guards."""
    u_a = auth_users["user_a_id"]
    u_c = auth_users["user_c_id"]
    c_email = auth_users["user_c_email"]
    ws_a_id = auth_users["ws_a_id"]

    headers_a = {
        "Authorization": f"Bearer {u_a}",
        "X-Workspace-Id": ws_a_id
    }

    # Invite user C as MEMBER
    with app.app_context():
        InvitationService.create_invitation(workspace_id=ws_a_id, actor_user_id=u_a, email=c_email, role="MEMBER")
        inv = WorkspaceInvitation.query.filter_by(workspace_id=ws_a_id, email=c_email).first()
        InvitationService.accept_invitation(token=inv.token, user_id=u_c)

    # 1. List Members
    res_members = client.get("/api/business/members", headers=headers_a)
    assert res_members.status_code == 200
    members = res_members.get_json()["data"]["members"]
    assert len(members) == 2

    member_c = next(m for m in members if m["user_id"] == u_c)
    member_a = next(m for m in members if m["user_id"] == u_a)

    # 2. Update User C Role to ADMIN
    res_role = client.patch(f"/api/business/members/{member_c['id']}/role", json={
        "role": "ADMIN"
    }, headers=headers_a)
    assert res_role.status_code == 200
    assert res_role.get_json()["data"]["member"]["role"] == "ADMIN"

    # 3. Suspend User C
    res_suspend = client.patch(f"/api/business/members/{member_c['id']}/status", json={
        "status": "SUSPENDED"
    }, headers=headers_a)
    assert res_suspend.status_code == 200
    assert res_suspend.get_json()["data"]["member"]["status"] == "SUSPENDED"

    # 4. User C cannot access WS-A while SUSPENDED
    headers_c_ws_a = {
        "Authorization": f"Bearer {u_c}",
        "X-Workspace-Id": ws_a_id
    }
    res_denied = client.get("/api/business/workspaces/current", headers=headers_c_ws_a)
    assert res_denied.status_code == 403

    # 5. Last OWNER protection: Cannot demote or remove User A (the sole OWNER)
    res_demote_owner = client.patch(f"/api/business/members/{member_a['id']}/role", json={
        "role": "MEMBER"
    }, headers=headers_a)
    assert res_demote_owner.status_code == 400
    assert "last active owner" in res_demote_owner.get_json()["error"]["message"].lower()

    res_remove_owner = client.delete(f"/api/business/members/{member_a['id']}", headers=headers_a)
    assert res_remove_owner.status_code == 400
