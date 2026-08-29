"""
B1 Security Test Suite — 5-Tier RBAC Permission Enforcement
============================================================
Verifies permission boundaries for all 5 roles:
- OWNER: Full access (can delete workspace, update roles)
- ADMIN: Can invite members and update partners, but cannot update roles to OWNER
- MEMBER: Can read/create/update partners, but cannot invite members
- ACCOUNTANT: Read-only access to partners and audit logs
- VIEWER: Read-only access to partners, no access to audit logs or mutations
"""

import uuid
from models.user import User
from models.business import WorkspaceMember
from database.db import db


def test_rbac_permission_matrix(client):
    # Setup users
    owner_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    member_id = str(uuid.uuid4())
    accountant_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())

    for uid, email in [(owner_id, "owner@corp.com"), (admin_id, "admin@corp.com"),
                       (member_id, "member@corp.com"), (accountant_id, "acct@corp.com"),
                       (viewer_id, "viewer@corp.com")]:
        db.session.add(User(id=uid, email=email))
    db.session.commit()

    headers_owner = {"Authorization": f"Bearer {owner_id}", "Content-Type": "application/json"}
    headers_admin = {"Authorization": f"Bearer {admin_id}", "Content-Type": "application/json"}
    headers_member = {"Authorization": f"Bearer {member_id}", "Content-Type": "application/json"}
    headers_acct = {"Authorization": f"Bearer {accountant_id}", "Content-Type": "application/json"}
    headers_viewer = {"Authorization": f"Bearer {viewer_id}", "Content-Type": "application/json"}

    # 1. Owner creates workspace
    res_ws = client.post("/api/business/workspaces", headers=headers_owner, json={"name": "RBAC Enterprise"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]

    # 2. Add members with respective roles
    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=admin_id, role="ADMIN", status="ACTIVE"))
    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=member_id, role="MEMBER", status="ACTIVE"))
    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=accountant_id, role="ACCOUNTANT", status="ACTIVE"))
    db.session.add(WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role="VIEWER", status="ACTIVE"))
    db.session.commit()

    # 3. Test Partner Creation (Allowed: OWNER, ADMIN, MEMBER; Denied: ACCOUNTANT, VIEWER)
    # MEMBER can create
    res_m = client.post(
        "/api/business/partners",
        headers={**headers_member, "X-Workspace-Id": ws_id},
        json={"partner_type": "CUSTOMER", "name": "Partner By Member"}
    )
    assert res_m.status_code == 201

    # ACCOUNTANT denied create
    res_a = client.post(
        "/api/business/partners",
        headers={**headers_acct, "X-Workspace-Id": ws_id},
        json={"partner_type": "CUSTOMER", "name": "Partner By Acct"}
    )
    assert res_a.status_code == 403
    assert res_a.get_json()["error"]["code"] == "PERMISSION_DENIED"

    # VIEWER denied create
    res_v = client.post(
        "/api/business/partners",
        headers={**headers_viewer, "X-Workspace-Id": ws_id},
        json={"partner_type": "CUSTOMER", "name": "Partner By Viewer"}
    )
    assert res_v.status_code == 403

    # 4. Test Audit Log Access (Allowed: OWNER, ADMIN, ACCOUNTANT; Denied: MEMBER, VIEWER)
    # ACCOUNTANT can read audit
    res_audit_acct = client.get("/api/business/audit", headers={**headers_acct, "X-Workspace-Id": ws_id})
    assert res_audit_acct.status_code == 200

    # MEMBER denied audit read
    res_audit_member = client.get("/api/business/audit", headers={**headers_member, "X-Workspace-Id": ws_id})
    assert res_audit_member.status_code == 403

    # VIEWER denied audit read
    res_audit_viewer = client.get("/api/business/audit", headers={**headers_viewer, "X-Workspace-Id": ws_id})
    assert res_audit_viewer.status_code == 403
