"""
B7 Test Suite — Business Entity Management
==========================================
Tests CRUD, tax identifier validation (GSTIN/PAN), and default entity switching.
"""

import uuid


def test_business_entity_crud_and_validation(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Multi Entity Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # 1. Create valid entity with GSTIN
    res_create = client.post("/api/business/entities", headers=ws_headers, json={
        "name": "Mumbai Division",
        "legal_name": "Multi Entity India Pvt Ltd",
        "entity_code": "MUM-01",
        "tax_identifier": "27ABCDE1234F1Z5",
        "is_default": True
    })
    assert res_create.status_code == 201
    ent1 = res_create.get_json()["data"]["entity"]
    assert ent1["is_default"] is True
    assert ent1["name"] == "Mumbai Division"

    # 2. Create second entity and set as default -> first should be unset
    res_create2 = client.post("/api/business/entities", headers=ws_headers, json={
        "name": "Bangalore Division",
        "entity_code": "BLR-01",
        "tax_identifier": "29ABCDE1234F1Z5",
        "is_default": True
    })
    assert res_create2.status_code == 201
    ent2 = res_create2.get_json()["data"]["entity"]
    assert ent2["is_default"] is True

    # 3. List entities -> verify first is no longer default
    res_list = client.get("/api/business/entities", headers=ws_headers)
    assert res_list.status_code == 200
    entities = res_list.get_json()["data"]["entities"]
    assert len(entities) == 2
    ent1_updated = next(e for e in entities if e["id"] == ent1["id"])
    assert ent1_updated["is_default"] is False


def test_invalid_tax_id_rejected(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Tax Validate Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Invalid tax identifier format
    res_fail = client.post("/api/business/entities", headers=ws_headers, json={
        "name": "Invalid Tax Entity",
        "tax_identifier": "INVALID!@#$"
    })
    assert res_fail.status_code == 400


def test_business_entity_update_and_archive(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}", "Content-Type": "application/json"}

    res_ws = client.post("/api/business/workspaces", headers=headers, json={"name": "Lifecycle Corp"})
    ws_id = res_ws.get_json()["data"]["workspace"]["id"]
    ws_headers = {**headers, "X-Workspace-Id": ws_id}

    # Create entity
    res_create = client.post("/api/business/entities", headers=ws_headers, json={
        "name": "Delhi Branch",
        "entity_code": "DEL-01"
    })
    assert res_create.status_code == 201
    ent_id = res_create.get_json()["data"]["entity"]["id"]

    # Update entity
    res_patch = client.patch(f"/api/business/entities/{ent_id}", headers=ws_headers, json={
        "name": "Delhi NCR Operations Hub",
        "legal_name": "Acme North India Private Limited"
    })
    assert res_patch.status_code == 200
    assert res_patch.get_json()["data"]["entity"]["name"] == "Delhi NCR Operations Hub"
    assert res_patch.get_json()["data"]["entity"]["legal_name"] == "Acme North India Private Limited"

    # Archive entity
    res_archive = client.post(f"/api/business/entities/{ent_id}/archive", headers=ws_headers, json={
        "reason": "Branch restructuring"
    })
    assert res_archive.status_code == 200
    assert res_archive.get_json()["data"]["entity"]["status"] == "INACTIVE"
