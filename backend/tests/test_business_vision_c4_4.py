"""
DeadlineOS Business OS — C4.4 Visual Restock Triggers & Cross-Border Freight Unit Tests
=======================================================================================
Covers visual par level depletion analysis, in-transit freight aggregation, duplicate
PR suppression, draft PR synthesis, operational alert generation, RBAC, multi-tenant
isolation, inventory ledger immutability, and Copilot telemetry grounding.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
import pytest

from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    BusinessLocation,
    BusinessProduct,
    CommercialPartner,
    BusinessShelfZone,
    BusinessVisualObservation,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessCrossBorderShipment,
    BusinessPurchaseRequest,
    BusinessStockMovement,
    BusinessOperationalAlert,
    AuditEvent
)
from services.business.visual_restock_service import VisualRestockService
from services.business.copilot_service import CopilotService


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def fx_c44_env(app):
    """Sets up dual-tenant workspaces with RBAC members, locations, suppliers, products, shelf zones, and freight."""
    with app.app_context():
        sfx = uuid.uuid4().hex[:6]

        # 1. Users
        u_owner = User(id=str(uuid.uuid4()), email=f"c44_owner_{sfx}@test.com", full_name="C4.4 Owner")
        u_admin = User(id=str(uuid.uuid4()), email=f"c44_admin_{sfx}@test.com", full_name="C4.4 Admin")
        u_member = User(id=str(uuid.uuid4()), email=f"c44_member_{sfx}@test.com", full_name="C4.4 Member")
        u_accountant = User(id=str(uuid.uuid4()), email=f"c44_acct_{sfx}@test.com", full_name="C4.4 Accountant")
        u_viewer = User(id=str(uuid.uuid4()), email=f"c44_viewer_{sfx}@test.com", full_name="C4.4 Viewer")
        u_tenb = User(id=str(uuid.uuid4()), email=f"c44_tenb_{sfx}@test.com", full_name="C4.4 Tenant B")
        db.session.add_all([u_owner, u_admin, u_member, u_accountant, u_viewer, u_tenb])
        db.session.commit()

        # 2. Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name=f"C4.4-WS-A-{sfx}", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name=f"C4.4-WS-B-{sfx}", base_currency="INR")
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
        loc_a = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name=f"Main Store {sfx}", location_type="STORE", status="ACTIVE")
        loc_b = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_b.id, name=f"Tenant B Store {sfx}", location_type="STORE", status="ACTIVE")
        db.session.add_all([loc_a, loc_b])
        db.session.commit()

        # 5. Suppliers
        supp_a = CommercialPartner(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            partner_type="SUPPLIER",
            name=f"Global Organics Ltd {sfx}",
            default_currency="INR",
            status="ACTIVE"
        )
        db.session.add(supp_a)
        db.session.commit()

        # 6. Products
        p_cereal = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku=f"SKU-OATS-{sfx}",
            name="Organic Rolled Oats 1kg",
            unit="UNIT",
            cost_price=Decimal("120.00"),
            selling_price=Decimal("200.00"),
            reorder_level=Decimal("10.00"),
            preferred_supplier_partner_id=supp_a.id,
            status="ACTIVE"
        )
        db.session.add(p_cereal)
        db.session.commit()

        # 7. Shelf Zone
        zone_a = BusinessShelfZone(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            location_id=loc_a.id,
            zone_code=f"SZ-CEREAL-{sfx}",
            name="Aisle 3 Breakfast Cereals",
            assigned_product_id=p_cereal.id,
            target_facings=4,
            expected_capacity=Decimal("30.00"),
            reorder_threshold=Decimal("10.00"),
            status="ACTIVE"
        )
        db.session.add(zone_a)
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
            "supp_a_id": supp_a.id,
            "p_cereal_id": p_cereal.id,
            "zone_a_id": zone_a.id,
        }


def _auth_headers(user_id: str, workspace_id: str) -> dict:
    return {
        "Authorization": f"Bearer {user_id}",
        "X-Workspace-Id": workspace_id,
        "Content-Type": "application/json"
    }


# ── Test Suite ─────────────────────────────────────────────────────────────────

def test_evaluate_restock_depleted_shelf_no_freight(client, fx_c44_env):
    """1. Depleted shelf with 0 in-transit freight generates draft PR for full shortfall + OperationalAlert."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    # Visual count is 4.00 on a capacity of 30.00 (Gross shortfall: 26.00)
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        shelf_zone_id=zone_id,
        matched_product_id=prod_id,
        visual_count=Decimal("4.00"),
        system_stock_at_capture=Decimal("4.00"),
        discrepancy_quantity=Decimal("0.00"),
        anomaly_type="FACING_DEFICIT",
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = VisualRestockService.evaluate_and_trigger_restock(
        workspace_id=ws_id,
        observation_id=obs.id,
        actor_user_id=owner_id
    )

    assert res["is_depleted"] is True
    assert res["gross_demand"] == "26.00"
    assert res["in_transit_quantity"] == "0.00"
    assert res["net_shortfall"] == "26.00"
    assert res["purchase_request"] is not None
    assert res["purchase_request"]["status"] == "DRAFT"
    assert res["purchase_request"]["requested_quantity"] == "26.00"
    assert res["purchase_request"]["priority"] == "HIGH"
    assert res["operational_alert"]["alert_type"] == "VISUAL_RESTOCK_REQUIRED"


def test_evaluate_restock_covered_by_in_transit_freight(client, fx_c44_env):
    """2. Depleted shelf with in-transit freight >= shortfall generates INFO alert and suppresses draft PR."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    supp_id = env["supp_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    # 1. Create open PO with 50.00 units and an IN_TRANSIT cross-border shipment
    po = BusinessPurchaseOrder(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        po_number="PO-2026-9901",
        supplier_partner_id=supp_id,
        destination_location_id=loc_id,
        status="ISSUED",
        total_amount=Decimal("6000.00"),
        currency="INR"
    )
    po_line = BusinessPurchaseOrderLine(
        id=str(uuid.uuid4()),
        purchase_order_id=po.id,
        product_id=prod_id,
        ordered_quantity=Decimal("50.00"),
        unit_price=Decimal("120.00"),
        total_price=Decimal("6000.00"),
        received_quantity=Decimal("0.00")
    )
    shipment = BusinessCrossBorderShipment(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        shipment_number="SHP-202609-001",
        purchase_order_id=po.id,
        supplier_partner_id=supp_id,
        origin_country="IND",
        destination_country="IND",
        carrier_name="DHL Freight Line",
        transport_mode="ROAD",
        status="IN_TRANSIT",
        customs_status="CLEARED",
        estimated_arrival_date=date.today() + timedelta(days=2)
    )
    db.session.add_all([po, po_line, shipment])
    db.session.commit()

    # 2. Observation indicates 5.00 units on shelf (Shortfall is 25.00)
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()),
        workspace_id=ws_id,
        location_id=loc_id,
        shelf_zone_id=zone_id,
        matched_product_id=prod_id,
        visual_count=Decimal("5.00"),
        system_stock_at_capture=Decimal("5.00"),
        status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = VisualRestockService.evaluate_and_trigger_restock(
        workspace_id=ws_id,
        observation_id=obs.id,
        actor_user_id=owner_id
    )

    assert res["is_depleted"] is True
    assert res["gross_demand"] == "25.00"
    assert res["in_transit_quantity"] == "50.00"
    assert res["net_shortfall"] == "0.00"
    assert res["purchase_request"] is None  # Suppressed!
    assert res["operational_alert"]["alert_type"] == "RESTOCK_EN_ROUTE"
    assert res["operational_alert"]["severity"] == "INFO"


def test_evaluate_restock_partial_freight_coverage(client, fx_c44_env):
    """3. In-transit freight covers partial demand; generates draft PR for remaining net shortfall."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    supp_id = env["supp_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    # Open PO with 10.00 units in transit
    po = BusinessPurchaseOrder(
        id=str(uuid.uuid4()), workspace_id=ws_id, po_number="PO-2026-9902",
        supplier_partner_id=supp_id, destination_location_id=loc_id, status="ISSUED",
        total_amount=Decimal("1200.00"), currency="INR"
    )
    po_line = BusinessPurchaseOrderLine(
        id=str(uuid.uuid4()), purchase_order_id=po.id, product_id=prod_id,
        ordered_quantity=Decimal("10.00"), unit_price=Decimal("120.00"),
        total_price=Decimal("1200.00"), received_quantity=Decimal("0.00")
    )
    db.session.add_all([po, po_line])
    db.session.commit()

    # Visual count is 5.00 on capacity of 30.00 (Gross demand: 25.00, Net shortfall: 25 - 10 = 15.00)
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("5.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = VisualRestockService.evaluate_and_trigger_restock(
        workspace_id=ws_id,
        observation_id=obs.id,
        actor_user_id=owner_id
    )

    assert res["gross_demand"] == "25.00"
    assert res["in_transit_quantity"] == "10.00"
    assert res["net_shortfall"] == "15.00"
    assert res["purchase_request"]["requested_quantity"] == "15.00"


def test_evaluate_restock_non_depleted_shelf_noop(client, fx_c44_env):
    """4. Shelf count above reorder threshold returns no-op, no PR or alert created."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    # Visual count 25.00 / 30.00 (well above threshold of 10.00)
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("25.00"), anomaly_type="NONE", status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = VisualRestockService.evaluate_and_trigger_restock(
        workspace_id=ws_id,
        observation_id=obs.id,
        actor_user_id=owner_id
    )

    assert res["is_depleted"] is False
    assert res["purchase_request"] is None
    assert res["operational_alert"] is None
    assert BusinessPurchaseRequest.query.count() == 0


def test_draft_purchase_request_deduplication(client, fx_c44_env):
    """5. Multiple restock triggers for same product/location update existing draft PR instead of creating duplicates."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    obs1 = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("6.00"), status="PROCESSED"
    )
    db.session.add(obs1)
    db.session.commit()

    # Trigger 1: Shortfall 24.00
    res1 = VisualRestockService.evaluate_and_trigger_restock(ws_id, obs1.id, owner_id)
    pr1_id = res1["purchase_request"]["id"]
    assert res1["purchase_request"]["requested_quantity"] == "24.00"

    # Trigger 2 with new observation: Shortfall 28.00 (count is 2.00)
    obs2 = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("2.00"), status="PROCESSED"
    )
    db.session.add(obs2)
    db.session.commit()

    res2 = VisualRestockService.evaluate_and_trigger_restock(ws_id, obs2.id, owner_id)
    pr2_id = res2["purchase_request"]["id"]
    assert pr1_id == pr2_id  # Updated existing draft!
    assert res2["purchase_request"]["requested_quantity"] == "28.00"
    assert BusinessPurchaseRequest.query.filter_by(workspace_id=ws_id).count() == 1


def test_restock_priority_assignment(client, fx_c44_env):
    """6. Empty shelf (count=0) assigns URGENT priority; partial deficit assigns HIGH priority."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    # Empty shelf
    obs_empty = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("0.00"), anomaly_type="EMPTY_SHELF", status="PROCESSED"
    )
    db.session.add(obs_empty)
    db.session.commit()

    res = VisualRestockService.evaluate_and_trigger_restock(ws_id, obs_empty.id, owner_id)
    assert res["purchase_request"]["priority"] == "URGENT"
    assert res["operational_alert"]["severity"] == "CRITICAL"


def test_preferred_supplier_and_cost_resolution(client, fx_c44_env):
    """7. Generated draft PR correctly inherits product's cost_price and calculates total estimation."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("5.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = VisualRestockService.evaluate_and_trigger_restock(ws_id, obs.id, owner_id)
    pr = res["purchase_request"]
    assert pr["estimated_unit_price"] == "120.00"
    assert pr["estimated_total_price"] == "3000.00"  # 25 * 120 = 3000.00


def test_cross_border_shipment_in_transit_query(client, fx_c44_env):
    """8. Endpoint /zones/<id>/in-transit returns carrier, shipment number, ETA, and customs status."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    supp_id = env["supp_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    po = BusinessPurchaseOrder(
        id=str(uuid.uuid4()), workspace_id=ws_id, po_number="PO-2026-9903",
        supplier_partner_id=supp_id, destination_location_id=loc_id, status="ISSUED",
        total_amount=Decimal("2400.00"), currency="INR"
    )
    po_line = BusinessPurchaseOrderLine(
        id=str(uuid.uuid4()), purchase_order_id=po.id, product_id=prod_id,
        ordered_quantity=Decimal("20.00"), unit_price=Decimal("120.00"),
        total_price=Decimal("2400.00"), received_quantity=Decimal("0.00")
    )
    shipment = BusinessCrossBorderShipment(
        id=str(uuid.uuid4()), workspace_id=ws_id, shipment_number="SHP-202609-003",
        purchase_order_id=po.id, supplier_partner_id=supp_id, origin_country="IND",
        destination_country="IND", carrier_name="FedEx Express", transport_mode="AIR",
        status="IN_TRANSIT", customs_status="CLEARED", estimated_arrival_date=date.today() + timedelta(days=3)
    )
    db.session.add_all([po, po_line, shipment])
    db.session.commit()

    res = client.get(
        f"/api/business/vision/zones/{zone_id}/in-transit",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["in_transit_quantity"] == "20.00"
    assert data["active_shipments_count"] == 1
    assert data["shipments"][0]["shipment_number"] == "SHP-202609-003"
    assert data["shipments"][0]["carrier_name"] == "FedEx Express"


def test_list_active_restock_triggers_endpoint(client, fx_c44_env):
    """9. Endpoint /restock-triggers returns all depleted zones with net shortfall metrics."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    # Ingest depleted observation
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("2.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = client.get(
        "/api/business/vision/restock-triggers",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res.status_code == 200
    triggers = res.get_json()["data"]["restock_triggers"]
    assert len(triggers) >= 1
    t = triggers[0]
    assert t["shelf_zone_id"] == zone_id
    assert t["gross_demand"] == "28.00"


def test_trigger_restock_api_endpoint(client, fx_c44_env):
    """10. POST /observations/<id>/trigger-restock successfully executes evaluation and returns PR/alert payload."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    admin_id = env["u_admin_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("3.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    res = client.post(
        f"/api/business/vision/observations/{obs.id}/trigger-restock",
        headers=_auth_headers(admin_id, ws_id)
    )
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["is_depleted"] is True
    assert data["purchase_request"] is not None


def test_rbac_restock_trigger_permissions(client, fx_c44_env):
    """11. OWNER and ADMIN can trigger restock; MEMBER, ACCOUNTANT, VIEWER receive 403 Forbidden."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    member_id = env["u_member_id"]
    acct_id = env["u_accountant_id"]
    viewer_id = env["u_viewer_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("2.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # MEMBER -> 403
    res_m = client.post(
        f"/api/business/vision/observations/{obs.id}/trigger-restock",
        headers=_auth_headers(member_id, ws_id)
    )
    assert res_m.status_code == 403

    # ACCOUNTANT -> 403
    res_acct = client.post(
        f"/api/business/vision/observations/{obs.id}/trigger-restock",
        headers=_auth_headers(acct_id, ws_id)
    )
    assert res_acct.status_code == 403

    # VIEWER -> 403
    res_v = client.post(
        f"/api/business/vision/observations/{obs.id}/trigger-restock",
        headers=_auth_headers(viewer_id, ws_id)
    )
    assert res_v.status_code == 403

    # OWNER -> 201
    res_o = client.post(
        f"/api/business/vision/observations/{obs.id}/trigger-restock",
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res_o.status_code == 201


def test_multitenant_isolation_restock(client, fx_c44_env):
    """12. Tenant B cannot trigger restock or query in-transit freight for Tenant A's shelf zones."""
    env = fx_c44_env
    ws_a = env["ws_a_id"]
    ws_b = env["ws_b_id"]
    tenb_user = env["u_tenb_id"]
    loc_a = env["loc_a_id"]
    prod_a = env["p_cereal_id"]
    zone_a = env["zone_a_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_a, location_id=loc_a, shelf_zone_id=zone_a,
        matched_product_id=prod_a, visual_count=Decimal("2.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    # Tenant B tries to trigger restock on Tenant A observation -> 404
    res_trig = client.post(
        f"/api/business/vision/observations/{obs.id}/trigger-restock",
        headers=_auth_headers(tenb_user, ws_b)
    )
    assert res_trig.status_code == 404

    # Tenant B tries to query Tenant A in-transit freight -> 404
    res_in_t = client.get(
        f"/api/business/vision/zones/{zone_a}/in-transit",
        headers=_auth_headers(tenb_user, ws_b)
    )
    assert res_in_t.status_code == 404


def test_inventory_ledger_untouched_by_restock_trigger(client, fx_c44_env):
    """13. Asserts ZERO rows added to business_stock_movements during restock trigger execution."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    initial_movement_count = BusinessStockMovement.query.filter_by(workspace_id=ws_id).count()

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("0.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    VisualRestockService.evaluate_and_trigger_restock(ws_id, obs.id, owner_id)

    final_movement_count = BusinessStockMovement.query.filter_by(workspace_id=ws_id).count()
    assert initial_movement_count == final_movement_count, "Restock trigger must NEVER directly insert stock movements!"


def test_copilot_restock_telemetry_grounding(client, fx_c44_env):
    """14. Verifies visual restock alerts and in-transit freight are formatted in Copilot telemetry context."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    # Ingest depleted observation
    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("2.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    context = CopilotService.assemble_context(ws_id)
    assert "visual_restock_intelligence" in context
    assert context["visual_restock_intelligence"]["active_depleted_zones_count"] >= 1


def test_audit_event_logging_restock_trigger(client, fx_c44_env):
    """15. Verifies RESTOCK_TRIGGERED audit log event recording."""
    env = fx_c44_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    prod_id = env["p_cereal_id"]
    zone_id = env["zone_a_id"]

    obs = BusinessVisualObservation(
        id=str(uuid.uuid4()), workspace_id=ws_id, location_id=loc_id, shelf_zone_id=zone_id,
        matched_product_id=prod_id, visual_count=Decimal("3.00"), status="PROCESSED"
    )
    db.session.add(obs)
    db.session.commit()

    VisualRestockService.evaluate_and_trigger_restock(ws_id, obs.id, owner_id)

    events = AuditEvent.query.filter_by(workspace_id=ws_id).all()
    actions = [e.action for e in events]
    assert "RESTOCK_TRIGGERED" in actions
