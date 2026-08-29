"""
B1 Foundation Test Suite — Workspace Scoping
============================================
Tests workspace provisioning, automatic OWNER role assignment,
workspace switching, and workspace profile updates.
"""

import uuid
from models.business import Workspace, WorkspaceMember


def test_create_workspace_success(client):
    user_token = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

    res = client.post(
        "/api/business/workspaces",
        headers=headers,
        json={
            "name": "Apex Innovations",
            "legal_name": "Apex Innovations Pvt Ltd",
            "tax_identifier": "GST29ABCDE1234F1Z5",
            "base_currency": "INR",
            "timezone": "Asia/Kolkata"
        }
    )

    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["workspace"]["name"] == "Apex Innovations"
    ws_id = data["data"]["workspace"]["id"]

    # Verify OWNER membership was created atomically
    owner_member = WorkspaceMember.query.filter_by(workspace_id=ws_id, user_id=user_token).first()
    assert owner_member is not None
    assert owner_member.role == "OWNER"
    assert owner_member.status == "ACTIVE"


def test_list_user_workspaces(client):
    user_token = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

    # Create 2 workspaces
    client.post("/api/business/workspaces", headers=headers, json={"name": "Workspace One"})
    client.post("/api/business/workspaces", headers=headers, json={"name": "Workspace Two"})

    res = client.get("/api/business/workspaces", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]["workspaces"]) == 2
    names = [w["name"] for w in data["data"]["workspaces"]]
    assert "Workspace One" in names
    assert "Workspace Two" in names


def test_get_current_workspace_profile(client):
    user_token = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

    res_create = client.post("/api/business/workspaces", headers=headers, json={"name": "Workspace Delta"})
    ws_id = res_create.get_json()["data"]["workspace"]["id"]

    ws_headers = {
        "Authorization": f"Bearer {user_token}",
        "X-Workspace-Id": ws_id,
        "Content-Type": "application/json"
    }

    res_profile = client.get("/api/business/workspaces/current", headers=ws_headers)
    assert res_profile.status_code == 200
    profile_data = res_profile.get_json()["data"]
    assert profile_data["workspace"]["id"] == ws_id
    assert profile_data["member"]["role"] == "OWNER"
    assert "workspace:update" in profile_data["permissions"]


def test_update_workspace_profile(client):
    user_token = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

    res_create = client.post("/api/business/workspaces", headers=headers, json={"name": "Original Name"})
    ws_id = res_create.get_json()["data"]["workspace"]["id"]

    ws_headers = {
        "Authorization": f"Bearer {user_token}",
        "X-Workspace-Id": ws_id,
        "Content-Type": "application/json"
    }

    res_patch = client.patch(
        "/api/business/workspaces/current",
        headers=ws_headers,
        json={"name": "Updated Enterprise Name", "legal_name": "Updated Corp"}
    )
    assert res_patch.status_code == 200
    updated_data = res_patch.get_json()["data"]["workspace"]
    assert updated_data["name"] == "Updated Enterprise Name"
    assert updated_data["legal_name"] == "Updated Corp"
