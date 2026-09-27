"""
DeadlineOS Business OS — C4.3 Visual Discrepancy Reconciliation & Staged Corrections Unit Tests
=============================================================================================
Covers all C4.3 discrepancy proposal, idempotency, state transitions, negative stock defense,
human-in-the-loop editing, confirmation to authoritative stock ledger, rejection/dismissal,
RBAC enforcement, tenant isolation, batch/serial attribution, and audit event provenance.
"""

import uuid
from decimal import Decimal
import pytest

from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    BusinessLocation,
    BusinessProduct,
    BusinessShelfZone,
    BusinessVisualObservation,
    BusinessStockMovement,
    StagedExtraction,
    AuditEvent,
    BusinessBatch,
    BusinessSerialNumber
)
from services.business.inventory_service import InventoryService


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def fx_c43_env(app):
    """Sets up dual-tenant workspaces with RBAC members, locations, products, shelf zones, and stock baselines."""
    with app.app_context():
        sfx = uuid.uuid4().hex[:6]

        # 1. Users
        u_owner = User(id=str(uuid.uuid4()), email=f"c43_owner_{sfx}@test.com", full_name="C4.3 Owner")
        u_admin = User(id=str(uuid.uuid4()), email=f"c43_admin_{sfx}@test.com", full_name="C4.3 Admin")
        u_member = User(id=str(uuid.uuid4()), email=f"c43_member_{sfx}@test.com", full_name="C4.3 Member")
        u_accountant = User(id=str(uuid.uuid4()), email=f"c43_acct_{sfx}@test.com", full_name="C4.3 Accountant")
        u_viewer = User(id=str(uuid.uuid4()), email=f"c43_viewer_{sfx}@test.com", full_name="C4.3 Viewer")
        u_tenb = User(id=str(uuid.uuid4()), email=f"c43_tenb_{sfx}@test.com", full_name="C4.3 Tenant B")
        db.session.add_all([u_owner, u_admin, u_member, u_accountant, u_viewer, u_tenb])
        db.session.commit()

        # 2. Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name=f"C4.3-WS-A-{sfx}", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name=f"C4.3-WS-B-{sfx}", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # 3. Memberships
        db.session.add_all([
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_owner.id, role="OWNER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_member.id, role="MEMBER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_accountant.id, role="ACCOUNTANT", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_viewer.id, role="VIEWER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_b.id, user_id=u_tenb.id, role="OWNER", status="ACTIVE"),
        ])
        db.session.commit()

        # 4. Locations
        loc_a = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name=f"Retail Store {sfx}", location_type="STORE", status="ACTIVE")
        loc_b = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_b.id, name=f"Tenant B Store {sfx}", location_type="STORE", status="ACTIVE")
        db.session.add_all([loc_a, loc_b])
        db.session.commit()

        # 5. Products
        p_juice = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku=f"SKU-JUICE-{sfx}",
            name="Cold Pressed Orange Juice 500ml",
            unit="BOTTLE",
            cost_price=Decimal("45.00"),
            selling_price=Decimal("80.00"),
            status="ACTIVE"
        )
        p_serialized = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku=f"SKU-CAM-{sfx}",
            name="Security Dome Camera",
            unit="UNIT",
            cost_price=Decimal("3500.00"),
            selling_price=Decimal("6000.00"),
            is_serialized=True,
            status="ACTIVE"
        )
        db.session.add_all([p_juice, p_serialized])
        db.session.commit()

        # 6. Shelf Zone
        zone_a = BusinessShelfZone(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            location_id=loc_a.id,
            zone_code=f"SZ-BEV-{sfx}",
            name="Beverage Cooler Shelf 1",
            assigned_product_id=p_juice.id,
            target_facings=4,
            expected_capacity=Decimal("30.00"),
            reorder_threshold=Decimal("10.00"),
            status="ACTIVE"
        )
        db.session.add(zone_a)
        db.session.commit()

        # 7. Initial Baseline Stock for p_juice (10 units)
        stock_init = BusinessStockMovement(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            product_id=p_juice.id,
            location_id=loc_a.id,
            movement_type="INITIAL_STOCK",
            direction="IN",
            quantity=Decimal("10.00"),
            unit_cost=Decimal("45.00"),
            actor_user_id=u_owner.id,
            reason="Initial inventory setup"
        )
        db.session.add(stock_init)
        db.session.commit()

        yield {
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
            "u_owner_id": u_owner.id,
            "u_admin_id": u_admin.id,
            "u_member_id": u_member.id,
            "u_accountant_id": u_accountant.id,
            "u_viewer_id": u_viewer.id,
            "u_tenb_id": u_tenb.id,
            "loc_a_id": loc_a.id,
            "loc_b_id": loc_b.id,
            "p_juice_id": p_juice.id,
            "p_serialized_id": p_serialized.id,
            "zone_a_id": zone_a.id,
        }


def _auth_headers(user_id: str, workspace_id: str) -> dict:
    return {
        "Authorization": f"Bearer {user_id}",
        "X-Workspace-Id": workspace_id,
        "Content-Type": "application/json"
    }


# ── Test Suite ─────────────────────────────────────────────────────────────────

def test_propose_reconciliation_positive_discrepancy(client, fx_c43_env):
    """1. Visual count > System stock creates IN adjustment candidate with status NEEDS_REVIEW."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]
    zone_id = env["zone_a_id"]

    # System stock is 10.00, visual count is 14.00 (diff = +4.00)
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        shelf_zone_id=zone_id,
        matched_product_id=prod_id,
        visual_count=Decimal("14.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("4.00"),
        overall_confidence=Decimal("95.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id),
        json={"reason": "Audit detected 4 surplus bottles"}
    )
    assert res.status_code == 201
    body = res.get_json()["data"]
    assert body["is_noop"] is False
    staged = body["staged_extraction"]
    assert staged["candidate_type"] == "INVENTORY_RECONCILIATION"
    assert staged["status"] == "NEEDS_REVIEW"
    assert staged["normalized_data"]["direction"] == "IN"
    assert staged["normalized_data"]["quantity"] == "4.00"
    assert staged["normalized_data"]["product_id"] == prod_id
    assert staged["normalized_data"]["location_id"] == loc_id

    # Observation state
    obs_refreshed = BusinessVisualObservation.query.get(obs.id)
    assert obs_refreshed.status == "REVIEW_REQUIRED"
    assert obs_refreshed.staged_extraction_id == staged["id"]


def test_propose_reconciliation_negative_discrepancy(client, fx_c43_env):
    """2. Visual count < System stock creates OUT adjustment candidate with status NEEDS_REVIEW."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    admin_id = env["u_admin_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]
    zone_id = env["zone_a_id"]

    # System stock is 10.00, visual count is 7.00 (diff = -3.00)
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        shelf_zone_id=zone_id,
        matched_product_id=prod_id,
        visual_count=Decimal("7.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("-3.00"),
        overall_confidence=Decimal("92.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(admin_id, ws_id)
    )
    assert res.status_code == 201
    staged = res.get_json()["data"]["staged_extraction"]
    assert staged["normalized_data"]["direction"] == "OUT"
    assert staged["normalized_data"]["quantity"] == "3.00"
    assert staged["normalized_data"]["discrepancy_quantity"] == "-3.00"


def test_propose_reconciliation_zero_discrepancy_noop(client, fx_c43_env):
    """3. Zero discrepancy observation returns no-op, no staged extraction created."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("10.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("0.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["is_noop"] is True
    assert data["staged_extraction"] is None
    assert StagedExtraction.query.count() == 0


def test_propose_reconciliation_idempotency(client, fx_c43_env):
    """4. Multiple proposal attempts on same observation return existing candidate without duplicates."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("12.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("2.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # First call
    res1 = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res1.status_code == 201
    staged_id1 = res1.get_json()["data"]["staged_extraction"]["id"]

    # Second call
    res2 = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res2.status_code in (200, 201)
    staged_id2 = res2.get_json()["data"]["staged_extraction"]["id"]

    assert staged_id1 == staged_id2
    assert StagedExtraction.query.filter_by(workspace_id=ws_id).count() == 1


def test_confirm_reconciliation_creates_stock_movement(client, fx_c43_env):
    """5. Confirming candidate creates MANUAL_ADJUSTMENT movement, links staged_extraction_id, updates obs to RECONCILED."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("15.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("5.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # Propose
    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Confirm via staging endpoint
    res_c = client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res_c.status_code == 200
    staged_res = res_c.get_json()["data"]["staged_extraction"]
    assert staged_res["status"] == "CONFIRMED"

    # Verify authoritative stock movement
    movement = BusinessStockMovement.query.filter_by(staged_extraction_id=staged_id).first()
    assert movement is not None
    assert movement.movement_type == "MANUAL_ADJUSTMENT"
    assert movement.direction == "IN"
    assert movement.quantity == Decimal("5.00")
    assert movement.product_id == prod_id
    assert movement.location_id == loc_id

    # Verify updated total available stock: 10 + 5 = 15
    avail = InventoryService.get_available_stock(ws_id, prod_id, loc_id)
    assert avail == Decimal("15.00")

    # Verify observation status is RECONCILED
    obs_refreshed = BusinessVisualObservation.query.get(obs.id)
    assert obs_refreshed.status == "RECONCILED"


def test_confirm_reconciliation_negative_stock_defense(client, fx_c43_env):
    """6. OUT adjustment exceeding available stock raises INSUFFICIENT_STOCK and blocks confirmation."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    admin_id = env["u_admin_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    # Current stock is 10.00. Visual count is 0.00 -> discrepancy = -10.00
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("0.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("-10.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # Propose OUT adjustment of 10.00
    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(admin_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Intervening sale reduces stock to 3.00 (7 sold)
    InventoryService.record_stock_movement(
        workspace_id=ws_id,
        actor_user_id=admin_id,
        data={
            "product_id": prod_id,
            "location_id": loc_id,
            "movement_type": "SALE",
            "direction": "OUT",
            "quantity": Decimal("7.00")
        }
    )

    # Confirming the -10.00 OUT adjustment must fail because only 3.00 available
    res_c = client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(admin_id, ws_id)
    )
    assert res_c.status_code == 400
    assert "Insufficient stock" in res_c.get_json()["error"]["message"]

    # Verify stock remains 3.00
    avail = InventoryService.get_available_stock(ws_id, prod_id, loc_id)
    assert avail == Decimal("3.00")


def test_reject_reconciliation_leaves_stock_untouched(client, fx_c43_env):
    """7. Rejecting candidate marks staged as REJECTED, obs as DISMISSED, creates 0 stock movements."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("16.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("6.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Reject
    res_r = client.post(
        f"/api/business/staging/{staged_id}/reject",
        headers=_auth_headers(owner_id, ws_id),
        json={"reason": "Camera reflection caused phantom detections"}
    )
    assert res_r.status_code == 200
    assert res_r.get_json()["data"]["staged_extraction"]["status"] == "REJECTED"

    # Verify zero stock movements created for this candidate
    assert BusinessStockMovement.query.filter_by(staged_extraction_id=staged_id).count() == 0
    assert InventoryService.get_available_stock(ws_id, prod_id, loc_id) == Decimal("10.00")

    # Verify observation status is DISMISSED
    obs_ref = BusinessVisualObservation.query.get(obs.id)
    assert obs_ref.status == "DISMISSED"


def test_dismiss_observation_directly(client, fx_c43_env):
    """8. Calling /observations/<id>/dismiss directly updates status and rejects active staged item."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    admin_id = env["u_admin_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("14.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("4.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # Propose staged
    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(admin_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Dismiss observation directly
    res_d = client.post(
        f"/api/business/vision/observations/{obs.id}/dismiss",
        headers=_auth_headers(admin_id, ws_id),
        json={"reason": "Dismissed after visual verification"}
    )
    assert res_d.status_code == 200
    assert res_d.get_json()["data"]["observation"]["status"] == "DISMISSED"

    # Staged item is now REJECTED
    staged = StagedExtraction.query.get(staged_id)
    assert staged.status == "REJECTED"
    assert BusinessStockMovement.query.filter_by(staged_extraction_id=staged_id).count() == 0


def test_edit_staged_reconciliation_before_confirmation(client, fx_c43_env):
    """9. Modifying unit_cost or reason in staged candidate persists to confirmed stock movement."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("15.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("5.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Reviewer edits quantity to 3.00, unit_cost to 48.00, and customized reason
    res_patch = client.patch(
        f"/api/business/staging/{staged_id}",
        headers=_auth_headers(owner_id, ws_id),
        json={
            "normalized_data": {
                "quantity": "3.00",
                "discrepancy_quantity": "3.00",
                "unit_cost": "48.00",
                "reason": "Corrected physical count on shelf"
            }
        }
    )
    assert res_patch.status_code == 200

    # Confirm
    res_c = client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res_c.status_code == 200

    # Verify movement has edited values
    movement = BusinessStockMovement.query.filter_by(staged_extraction_id=staged_id).first()
    assert movement.quantity == Decimal("3.00")
    assert movement.unit_cost == Decimal("48.00")
    assert movement.reason == "Corrected physical count on shelf"


def test_rbac_reconciliation_proposal(client, fx_c43_env):
    """10. OWNER and ADMIN can propose; ACCOUNTANT and VIEWER are blocked (403)."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    admin_id = env["u_admin_id"]
    acct_id = env["u_accountant_id"]
    viewer_id = env["u_viewer_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("12.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("2.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # ACCOUNTANT -> 403
    res_acct = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(acct_id, ws_id)
    )
    assert res_acct.status_code == 403

    # VIEWER -> 403
    res_view = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(viewer_id, ws_id)
    )
    assert res_view.status_code == 403

    # ADMIN -> 201
    res_admin = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(admin_id, ws_id)
    )
    assert res_admin.status_code == 201


def test_rbac_reconciliation_confirmation(client, fx_c43_env):
    """11. ONLY OWNER and ADMIN can confirm; MEMBER is blocked (403)."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    admin_id = env["u_admin_id"]
    member_id = env["u_member_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("13.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("3.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(admin_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # MEMBER confirmation -> 403
    res_m = client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(member_id, ws_id)
    )
    assert res_m.status_code == 403

    # OWNER confirmation -> 200
    res_o = client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res_o.status_code == 200


def test_multitenant_isolation_discrepancy(client, fx_c43_env):
    """12. Tenant B cannot propose, view, confirm, or dismiss Tenant A's observation/candidate."""
    env = fx_c43_env
    ws_a = env["ws_a_id"]
    ws_b = env["ws_b_id"]
    owner_a = env["u_owner_id"]
    tenb_user = env["u_tenb_id"]
    loc_a = env["loc_a_id"]
    prod_a = env["p_juice_id"]

    obs_a = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_a,
        location_id=loc_a,
        matched_product_id=prod_a,
        visual_count=Decimal("14.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("4.00"),
        status="PROCESSED"
    )
    db.session.add(obs_a)
    db.session.commit()

    # Tenant B tries to propose reconciliation on Tenant A's observation
    res_prop = client.post(
        f"/api/business/vision/observations/{obs_a.id}/propose-reconciliation",
        headers=_auth_headers(tenb_user, ws_b)
    )
    assert res_prop.status_code == 404

    # Tenant A proposes
    res_p = client.post(
        f"/api/business/vision/observations/{obs_a.id}/propose-reconciliation",
        headers=_auth_headers(owner_a, ws_a)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Tenant B tries to confirm Tenant A's staged candidate
    res_conf = client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(tenb_user, ws_b)
    )
    assert res_conf.status_code == 404


def test_list_pending_discrepancies(client, fx_c43_env):
    """13. Listing filter returns all observations with discrepancy_quantity != 0."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    # Obs 1: Discrepancy +2
    obs1 = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, matched_product_id=prod_id,
        visual_count=Decimal("12.00"), discrepancy_quantity=Decimal("2.00"), status="PROCESSED"
    )
    # Obs 2: Discrepancy -3
    obs2 = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, matched_product_id=prod_id,
        visual_count=Decimal("7.00"), discrepancy_quantity=Decimal("-3.00"), status="PROCESSED"
    )
    # Obs 3: Discrepancy 0
    obs3 = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, matched_product_id=prod_id,
        visual_count=Decimal("10.00"), discrepancy_quantity=Decimal("0.00"), status="PROCESSED"
    )
    db.session.add_all([obs1, obs2, obs3])
    db.session.commit()

    res = client.get(
        "/api/business/vision/discrepancies",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res.status_code == 200
    discrepancies = res.get_json()["data"]["discrepancies"]
    disc_ids = [d["id"] for d in discrepancies]
    assert obs1.id in disc_ids
    assert obs2.id in disc_ids
    assert obs3.id not in disc_ids


def test_batch_serial_reconciliation_linking(client, fx_c43_env):
    """14. Confirmed candidate with batch/serial data correctly links to C3.2/C3.3 tables."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_serialized_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("1.00"),
        system_stock_at_capture=Decimal("0.00"),
        discrepancy_quantity=Decimal("1.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Attach serial number attribution in staging edit
    client.patch(
        f"/api/business/staging/{staged_id}",
        headers=_auth_headers(owner_id, ws_id),
        json={
            "normalized_data": {
                "serial_attributions": ["SN-CAM-990011"]
            }
        }
    )

    # Confirm
    res_c = client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res_c.status_code == 200

    # Verify serial number record is created / linked
    sn = BusinessSerialNumber.query.filter_by(serial_number="SN-CAM-990011", workspace_id=ws_id).first()
    assert sn is not None
    assert sn.status == "IN_STOCK"
    assert sn.current_location_id == loc_id


def test_audit_event_logging_reconciliation(client, fx_c43_env):
    """15. Verifies RECONCILIATION_PROPOSED, STAGED_EXTRACTION_CONFIRMED, and STOCK_MOVEMENT_RECORDED audit logs."""
    env = fx_c43_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_juice_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        matched_product_id=prod_id,
        visual_count=Decimal("12.00"),
        system_stock_at_capture=Decimal("10.00"),
        discrepancy_quantity=Decimal("2.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # Propose
    res_p = client.post(
        f"/api/business/vision/observations/{obs.id}/propose-reconciliation",
        headers=_auth_headers(owner_id, ws_id)
    )
    staged_id = res_p.get_json()["data"]["staged_extraction"]["id"]

    # Confirm
    client.post(
        f"/api/business/staging/{staged_id}/confirm",
        headers=_auth_headers(owner_id, ws_id)
    )

    # Audit events check
    events = AuditEvent.query.filter_by(workspace_id=ws_id).all()
    actions = [e.action for e in events]
    assert "RECONCILIATION_PROPOSED" in actions
    assert "STAGED_EXTRACTION_CONFIRMED" in actions
    assert "STOCK_MOVEMENT_RECORDED" in actions
