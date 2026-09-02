"""
DeadlineOS Business OS — Operational Intelligence Automated Tests (Phase C2.3)
==============================================================================
"""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    CommercialPartner,
    BusinessLocation,
    BusinessProduct,
    BusinessStockMovement,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessGoodsReceipt,
    BusinessGoodsReceiptLine,
)
from services.business.operational_intelligence_service import OperationalIntelligenceService
from services.business.inventory_service import InventoryService
from utils.errors import APIError


@pytest.fixture
def intel_env(app):
    """Sets up a complete isolated workspace environment with historical movements, POs, and GRNs."""
    with app.app_context():
        # Users
        user_owner = User(id=str(uuid.uuid4()), email="intel_owner@test.com", full_name="Intel Owner")
        user_admin = User(id=str(uuid.uuid4()), email="intel_admin@test.com", full_name="Intel Admin")
        user_member = User(id=str(uuid.uuid4()), email="intel_member@test.com", full_name="Intel Member")
        user_accountant = User(id=str(uuid.uuid4()), email="intel_acct@test.com", full_name="Intel Accountant")
        user_viewer = User(id=str(uuid.uuid4()), email="intel_viewer@test.com", full_name="Intel Viewer")

        user_foreign = User(id=str(uuid.uuid4()), email="intel_foreign@test.com", full_name="Foreign Owner")

        db.session.add_all([
            user_owner, user_admin, user_member, user_accountant, user_viewer, user_foreign
        ])
        db.session.commit()

        # Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name="Intel Workspace A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="Foreign Workspace B", base_currency="USD")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # Memberships
        db.session.add_all([
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_owner.id, role="OWNER", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_admin.id, role="ADMIN", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_member.id, role="MEMBER", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_accountant.id, role="ACCOUNTANT", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_viewer.id, role="VIEWER", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_b.id, user_id=user_foreign.id, role="OWNER", status="ACTIVE"),
        ])
        db.session.commit()

        # Locations
        loc_a = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Central Warehouse", location_type="WAREHOUSE", status="ACTIVE")
        loc_b = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_b.id, name="Foreign Bay", location_type="WAREHOUSE", status="ACTIVE")
        db.session.add_all([loc_a, loc_b])
        db.session.commit()

        # Suppliers
        sup1 = CommercialPartner(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Alpha Supply Corp", partner_type="SUPPLIER", status="ACTIVE")
        sup2 = CommercialPartner(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Beta Precision Ltd", partner_type="SUPPLIER", status="ACTIVE")
        db.session.add_all([sup1, sup2])
        db.session.commit()

        # Products in Workspace A
        # P1: Fast-moving product (burns 2/day, currently 10 in stock -> DIR = 5 days -> CRITICAL_RISK)
        p1 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Fast Mover Valve",
            sku="VALVE-01",
            unit="PCS",
            cost_price=Decimal("100.00"),
            selling_price=Decimal("200.00"),
            reorder_level=Decimal("20.00"),
            safety_stock=Decimal("10.00"),
            preferred_supplier_partner_id=sup1.id,
            status="ACTIVE"
        )
        # P2: Dead stock product (15 in stock, zero OUT movements in >60 days)
        p2 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Dead Stock Bearing",
            sku="BEAR-99",
            unit="PCS",
            cost_price=Decimal("50.00"),
            selling_price=Decimal("90.00"),
            reorder_level=Decimal("5.00"),
            safety_stock=Decimal("2.00"),
            preferred_supplier_partner_id=sup2.id,
            status="ACTIVE"
        )
        # P3: Out of stock product (0 in stock, reorder level 15)
        p3 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Depleted Gasket",
            sku="GASK-00",
            unit="PCS",
            cost_price=Decimal("20.00"),
            selling_price=Decimal("40.00"),
            reorder_level=Decimal("15.00"),
            safety_stock=Decimal("5.00"),
            preferred_supplier_partner_id=sup1.id,
            status="ACTIVE"
        )
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        # Initial Stock Movements for P1: 70 IN, 60 OUT across last 30 days -> 10 remaining on hand, burn rate = 60/30 = 2.00/day
        now = datetime.now(timezone.utc)
        m_in_p1 = BusinessStockMovement(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, product_id=p1.id, location_id=loc_a.id,
            movement_type="INITIAL_STOCK", direction="IN", quantity=Decimal("70.00"), unit_cost=Decimal("100.00"),
            created_at=now - timedelta(days=25)
        )
        m_out_p1 = BusinessStockMovement(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, product_id=p1.id, location_id=loc_a.id,
            movement_type="SALE", direction="OUT", quantity=Decimal("60.00"), unit_cost=Decimal("100.00"),
            created_at=now - timedelta(days=10)
        )

        # Initial Stock Movements for P2: 15 IN 90 days ago, no OUT movements -> Dead Stock
        m_in_p2 = BusinessStockMovement(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, product_id=p2.id, location_id=loc_a.id,
            movement_type="INITIAL_STOCK", direction="IN", quantity=Decimal("15.00"), unit_cost=Decimal("50.00"),
            created_at=now - timedelta(days=90)
        )

        db.session.add_all([m_in_p1, m_out_p1, m_in_p2])
        db.session.commit()

        # Setup Deliveries for Supplier 1 (3 completed POs & GRNs -> RATED status)
        for i in range(3):
            po = BusinessPurchaseOrder(
                id=str(uuid.uuid4()), workspace_id=ws_a.id, po_number=f"PO-TEST-{i+1}",
                supplier_partner_id=sup1.id, destination_location_id=loc_a.id,
                order_date=date.today() - timedelta(days=20 - i*5),
                expected_delivery_date=date.today() - timedelta(days=15 - i*5),
                subtotal_amount=Decimal("1000.00"), tax_amount=Decimal("0.00"), total_amount=Decimal("1000.00"),
                currency="INR", status="FULLY_RECEIVED", created_by_user_id=user_admin.id
            )
            db.session.add(po)
            db.session.commit()

            pol = BusinessPurchaseOrderLine(
                id=str(uuid.uuid4()), purchase_order_id=po.id, product_id=p1.id,
                ordered_quantity=Decimal("10.00"), received_quantity=Decimal("10.00"),
                unit_price=Decimal("100.00"), total_price=Decimal("1000.00"), status="FULLY_RECEIVED"
            )
            db.session.add(pol)
            db.session.commit()

            grn = BusinessGoodsReceipt(
                id=str(uuid.uuid4()), workspace_id=ws_a.id, purchase_order_id=po.id,
                supplier_partner_id=sup1.id, destination_location_id=loc_a.id,
                grn_number=f"GRN-TEST-{i+1}", status="COMPLETED", received_by_user_id=user_member.id,
                receipt_date=date.today() - timedelta(days=16 - i*5)
            )
            db.session.add(grn)
            db.session.commit()

            grnl = BusinessGoodsReceiptLine(
                id=str(uuid.uuid4()), goods_receipt_id=grn.id, purchase_order_line_id=pol.id, product_id=p1.id, unit_cost=Decimal("100.00"),
                received_quantity=Decimal("10.00"), accepted_quantity=Decimal("10.00"), rejected_quantity=Decimal("0.00")
            )
            db.session.add(grnl)
            db.session.commit()

        # Setup Supplier 2 with only 1 completed delivery (< 3 -> INSUFFICIENT_HISTORY)
        po_sup2 = BusinessPurchaseOrder(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, po_number="PO-SUP2-1",
            supplier_partner_id=sup2.id, destination_location_id=loc_a.id,
            order_date=date.today() - timedelta(days=10), status="FULLY_RECEIVED",
            subtotal_amount=Decimal("500.00"), tax_amount=Decimal("0.00"), total_amount=Decimal("500.00"),
            currency="INR", created_by_user_id=user_admin.id
        )
        db.session.add(po_sup2)
        db.session.commit()

        return {
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
            "owner_id": user_owner.id,
            "admin_id": user_admin.id,
            "member_id": user_member.id,
            "accountant_id": user_accountant.id,
            "viewer_id": user_viewer.id,
            "foreign_id": user_foreign.id,
            "p1_id": p1.id,
            "p2_id": p2.id,
            "p3_id": p3.id,
            "sup1_id": sup1.id,
            "sup2_id": sup2.id,
            "loc_a_id": loc_a.id,
        }


# ==============================================================================
# 1. CORE OPERATIONAL INTELLIGENCE TESTS
# ==============================================================================

def test_operational_summary_metrics(app, intel_env):
    """Verifies operational summary KPIs: total SKUs, stock valuation, critical count, and dead stock."""
    env = intel_env
    with app.app_context():
        summary = OperationalIntelligenceService.get_operational_summary(env["ws_a_id"])

        assert summary["total_active_skus"] == 3
        assert Decimal(summary["total_inventory_valuation"]) == Decimal("1750.00")
        assert summary["critical_stockout_count"] == 2
        assert summary["dead_stock_count"] == 1
        assert summary["rated_suppliers_count"] == 1


def test_inventory_forecast_burn_rate_and_dir(app, intel_env):
    """Tests daily burn rate calculation and Days of Inventory Remaining (DIR) forecast."""
    env = intel_env
    with app.app_context():
        forecasts = OperationalIntelligenceService.get_inventory_forecast(env["ws_a_id"], window_days=30)
        assert len(forecasts) == 3

        # Find P1
        f_p1 = next(f for f in forecasts if f["product_id"] == env["p1_id"])
        assert Decimal(f_p1["daily_burn_rate"]) == Decimal("2.00")
        assert Decimal(f_p1["factual_stock"]) == Decimal("10.00")
        assert f_p1["days_of_inventory_remaining"] == 5.0
        assert f_p1["stock_health"] == "CRITICAL_RISK"
        assert f_p1["projected_stockout_date"] is not None

        # Find P2 (Dead stock)
        f_p2 = next(f for f in forecasts if f["product_id"] == env["p2_id"])
        assert Decimal(f_p2["daily_burn_rate"]) == Decimal("0.00")
        assert f_p2["stock_health"] == "DEAD_STOCK"

        # Find P3 (Out of stock)
        f_p3 = next(f for f in forecasts if f["product_id"] == env["p3_id"])
        assert Decimal(f_p3["factual_stock"]) == Decimal("0.00")
        assert f_p3["stock_health"] == "OUT_OF_STOCK"


def test_supplier_performance_and_insufficient_history_fallback(app, intel_env):
    """Ensures supplier scoring is deterministic and falls back to INSUFFICIENT_HISTORY when < 3 deliveries."""
    env = intel_env
    with app.app_context():
        suppliers = OperationalIntelligenceService.get_supplier_performance_summary(env["ws_a_id"])

        # Supplier 1 (3 deliveries -> RATED)
        sup1 = next(s for s in suppliers if s["supplier_id"] == env["sup1_id"])
        assert sup1["status"] == "RATED"
        assert sup1["completed_deliveries_count"] == 3
        assert Decimal(sup1["otif_rate"]) == Decimal("100.0")
        assert Decimal(sup1["quality_acceptance_rate"]) == Decimal("100.0")

        # Supplier 2 (1 delivery -> INSUFFICIENT_HISTORY)
        sup2 = next(s for s in suppliers if s["supplier_id"] == env["sup2_id"])
        assert sup2["status"] == "INSUFFICIENT_HISTORY"
        assert sup2["completed_deliveries_count"] == 1


def test_reorder_suggestions_generation(app, intel_env):
    """Verifies actionable replenishment proposals for low-stock and out-of-stock products."""
    env = intel_env
    with app.app_context():
        suggestions = OperationalIntelligenceService.get_reorder_suggestions(env["ws_a_id"])
        assert len(suggestions) >= 2

        p_ids = [s["product_id"] for s in suggestions]
        assert env["p1_id"] in p_ids
        assert env["p3_id"] in p_ids

        s_p1 = next(s for s in suggestions if s["product_id"] == env["p1_id"])
        assert s_p1["urgency"] in ("HIGH", "MEDIUM")
        assert Decimal(s_p1["suggested_quantity"]) > Decimal("0.00")
        assert s_p1["preferred_supplier_partner_id"] == env["sup1_id"]


# ==============================================================================
# 2. REST API & RBAC TESTS
# ==============================================================================

def test_api_operational_intelligence_endpoints(client, intel_env):
    """Tests all 4 operational intelligence endpoints with valid member authentication."""
    env = intel_env
    headers = {
        "Authorization": f"Bearer {env['member_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }

    # 1. Summary
    res = client.get("/api/business/intelligence/operations/summary", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["total_active_skus"] == 3

    # 2. Inventory Forecast
    res = client.get("/api/business/intelligence/operations/inventory-forecast?window_days=30", headers=headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]["items"]) == 3

    # 3. Suppliers
    res = client.get("/api/business/intelligence/operations/suppliers", headers=headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]["suppliers"]) == 2

    # 4. Reorder Suggestions
    res = client.get("/api/business/intelligence/operations/reorder-suggestions", headers=headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]["suggestions"]) >= 2


def test_api_tenant_isolation(client, intel_env):
    """Ensures Workspace B user cannot see Workspace A operational data."""
    env = intel_env
    headers_b = {
        "Authorization": f"Bearer {env['foreign_id']}",
        "X-Workspace-Id": env["ws_b_id"]
    }

    res = client.get("/api/business/intelligence/operations/summary", headers=headers_b)
    assert res.status_code == 200
    assert res.get_json()["data"]["total_active_skus"] == 0

def test_rbac_all_5_tiers_access(client, intel_env):
    """Verifies that all 5 valid roles (OWNER, ADMIN, MEMBER, ACCOUNTANT, VIEWER) can read intelligence."""
    env = intel_env
    roles = [
        ("OWNER", env["owner_id"]),
        ("ADMIN", env["admin_id"]),
        ("MEMBER", env["member_id"]),
        ("ACCOUNTANT", env["accountant_id"]),
        ("VIEWER", env["viewer_id"]),
    ]

    for role_name, uid in roles:
        headers = {
            "Authorization": f"Bearer {uid}",
            "X-Workspace-Id": env["ws_a_id"]
        }
        res = client.get("/api/business/intelligence/operations/summary", headers=headers)
        assert res.status_code == 200, f"Role {role_name} failed with {res.status_code}"


def test_non_member_access_denied(client, intel_env):
    """Ensures unassociated user cannot access operational intelligence."""
    env = intel_env
    headers = {
        "Authorization": f"Bearer {env['foreign_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }
    res = client.get("/api/business/intelligence/operations/summary", headers=headers)
    assert res.status_code in (403, 404)


def test_inventory_forecast_custom_window(app, intel_env):
    """Verifies inventory forecast with custom analysis window (e.g., 60 days)."""
    env = intel_env
    with app.app_context():
        forecasts = OperationalIntelligenceService.get_inventory_forecast(env["ws_a_id"], window_days=60)
        assert len(forecasts) == 3
        f_p1 = next(f for f in forecasts if f["product_id"] == env["p1_id"])
        assert f_p1["analysis_window_days"] == 60
        # 60 units consumed over 60 days -> 1.00 / day
        assert Decimal(f_p1["daily_burn_rate"]) == Decimal("1.00")
        assert f_p1["days_of_inventory_remaining"] == 10.0


def test_supplier_quality_rejection_metrics(app, intel_env):
    """Tests supplier quality metrics calculation with partial rejections."""
    env = intel_env
    with app.app_context():
        now = datetime.now(timezone.utc)
        # Create PO and GRN with 2 accepted, 8 rejected
        po = BusinessPurchaseOrder(
            id=str(uuid.uuid4()), workspace_id=env["ws_a_id"], po_number="PO-QUAL-1",
            supplier_partner_id=env["sup2_id"], destination_location_id=env["loc_a_id"],
            order_date=date.today() - timedelta(days=5), status="FULLY_RECEIVED",
            subtotal_amount=Decimal("1000.00"), tax_amount=Decimal("0.00"), total_amount=Decimal("1000.00"),
            currency="INR", created_by_user_id=env["admin_id"]
        )
        db.session.add(po)
        db.session.commit()

        pol = BusinessPurchaseOrderLine(
            id=str(uuid.uuid4()), purchase_order_id=po.id, product_id=env["p1_id"],
            ordered_quantity=Decimal("10.00"), received_quantity=Decimal("10.00"),
            unit_price=Decimal("100.00"), total_price=Decimal("1000.00"), status="FULLY_RECEIVED"
        )
        db.session.add(pol)
        db.session.commit()

        grn = BusinessGoodsReceipt(
            id=str(uuid.uuid4()), workspace_id=env["ws_a_id"], purchase_order_id=po.id,
            supplier_partner_id=env["sup2_id"], destination_location_id=env["loc_a_id"],
            grn_number="GRN-QUAL-1", status="COMPLETED", received_by_user_id=env["member_id"],
            receipt_date=date.today()
        )
        db.session.add(grn)
        db.session.commit()

        grnl = BusinessGoodsReceiptLine(
            id=str(uuid.uuid4()), goods_receipt_id=grn.id, purchase_order_line_id=pol.id,
            product_id=env["p1_id"], unit_cost=Decimal("100.00"),
            received_quantity=Decimal("10.00"), accepted_quantity=Decimal("2.00"), rejected_quantity=Decimal("8.00"),
            rejection_reason="DAMAGED"
        )
        db.session.add(grnl)
        db.session.commit()

        suppliers = OperationalIntelligenceService.get_supplier_performance_summary(env["ws_a_id"])
        sup2 = next(s for s in suppliers if s["supplier_id"] == env["sup2_id"])
        # Total received = 10, accepted = 2 -> quality = 20.0%
        assert Decimal(sup2["quality_acceptance_rate"]) == Decimal("20.0")
        assert Decimal(sup2["total_rejected_quantity"]) == Decimal("8.00")
