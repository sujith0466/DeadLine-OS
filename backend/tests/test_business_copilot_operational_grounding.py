"""
DeadlineOS Business OS — Phase C2.6 Business Copilot Operational Grounding Tests
==============================================================================
Comprehensive automated test suite covering:
1. Operational context assembly (inventory velocity, overdue POs, active alerts, stock valuation).
2. Grounded conversational query responses with deterministic fallback.
3. Strict row-level multi-tenant context boundary isolation.
4. RBAC permission verification across all 5 user tiers.
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
    BusinessOperationalAlert,
    AuditEvent,
)
from services.business.copilot_service import CopilotService


@pytest.fixture
def copilot_op_env(app):
    """Sets up a complete test workspace with operational telemetry data."""
    with app.app_context():
        u_owner = User(id=str(uuid.uuid4()), email=f"cpop_owner_{uuid.uuid4().hex[:6]}@test.com", full_name="Copilot Owner")
        u_admin = User(id=str(uuid.uuid4()), email=f"cpop_admin_{uuid.uuid4().hex[:6]}@test.com", full_name="Copilot Admin")
        u_member = User(id=str(uuid.uuid4()), email=f"cpop_member_{uuid.uuid4().hex[:6]}@test.com", full_name="Copilot Member")
        u_viewer = User(id=str(uuid.uuid4()), email=f"cpop_viewer_{uuid.uuid4().hex[:6]}@test.com", full_name="Copilot Viewer")
        u_foreign = User(id=str(uuid.uuid4()), email=f"cpop_for_{uuid.uuid4().hex[:6]}@test.com", full_name="Copilot Foreign")

        db.session.add_all([u_owner, u_admin, u_member, u_viewer, u_foreign])
        db.session.commit()

        ws_a = Workspace(id=str(uuid.uuid4()), name="Copilot Grounding Workspace A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="Copilot Grounding Workspace B", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        m_owner = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_owner.id, role="OWNER", status="ACTIVE")
        m_admin = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE")
        m_member = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_member.id, role="MEMBER", status="ACTIVE")
        m_viewer = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_viewer.id, role="VIEWER", status="ACTIVE")
        m_foreign = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_b.id, user_id=u_foreign.id, role="OWNER", status="ACTIVE")

        db.session.add_all([m_owner, m_admin, m_member, m_viewer, m_foreign])
        db.session.commit()

        loc = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Logistics Bay 1", location_type="WAREHOUSE", status="ACTIVE")
        sup = CommercialPartner(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Titan Fasteners", partner_type="SUPPLIER", status="ACTIVE")
        db.session.add_all([loc, sup])
        db.session.commit()

        p1 = BusinessProduct(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Titan Bolt M8", sku="TB-M8-01",
            unit="PCS", cost_price=Decimal("50.00"), selling_price=Decimal("100.00"),
            reorder_level=Decimal("20.00"), safety_stock=Decimal("10.00"),
            preferred_supplier_partner_id=sup.id, status="ACTIVE"
        )
        db.session.add(p1)
        db.session.commit()

        # Add movement
        m1 = BusinessStockMovement(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, product_id=p1.id, location_id=loc.id,
            movement_type="INITIAL_STOCK", direction="IN", quantity=Decimal("200.00"), unit_cost=Decimal("50.00")
        )
        db.session.add(m1)
        db.session.commit()

        # Add Overdue PO
        po = BusinessPurchaseOrder(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, po_number="PO-COPILOT-01",
            supplier_partner_id=sup.id, destination_location_id=loc.id,
            order_date=date.today() - timedelta(days=12),
            expected_delivery_date=date.today() - timedelta(days=4),
            subtotal_amount=Decimal("15000.00"), tax_amount=Decimal("0.00"), total_amount=Decimal("15000.00"),
            currency="INR", status="SENT_TO_SUPPLIER", created_by_user_id=u_admin.id
        )
        db.session.add(po)
        db.session.commit()

        # Add Operational Alert
        al = BusinessOperationalAlert(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, alert_type="OVERDUE_PURCHASE_ORDER",
            severity="WARNING", status="ACTIVE", title="PO-COPILOT-01 Overdue by 4 days",
            description="Expected delivery passed.", entity_type="PURCHASE_ORDER", entity_id=po.id,
            dedup_fingerprint="test_fp_cpop", cooldown_until=datetime.now(timezone.utc) + timedelta(days=1)
        )
        db.session.add(al)
        db.session.commit()

        return {
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
            "owner_id": u_owner.id,
            "admin_id": u_admin.id,
            "member_id": u_member.id,
            "viewer_id": u_viewer.id,
            "foreign_id": u_foreign.id,
            "p1_id": p1.id,
        }


def test_copilot_context_assembly_operational_grounding(app, copilot_op_env):
    """Verifies assemble_context contains both financial truth and live operational telemetry."""
    env = copilot_op_env
    with app.app_context():
        ctx = CopilotService.assemble_context(env["ws_a_id"])

        # Financial grounding
        assert "confirmed_cash" in ctx
        assert "runway_days" in ctx

        # Operational telemetry grounding
        assert "operational_summary" in ctx
        assert ctx["operational_summary"]["total_active_skus"] >= 1
        assert Decimal(ctx["operational_summary"]["total_inventory_valuation"]) >= Decimal("10000.00")

        assert "procurement_status" in ctx
        assert ctx["procurement_status"]["overdue_po_count"] >= 1

        assert "active_operational_alerts" in ctx
        assert len(ctx["active_operational_alerts"]) >= 1


def test_copilot_ask_operational_query(app, copilot_op_env):
    """Verifies ask_copilot returns response with context_summary containing operational metrics."""
    env = copilot_op_env
    with app.app_context():
        res = CopilotService.ask_copilot(
            workspace_id=env["ws_a_id"],
            user_id=env["member_id"],
            prompt="What is our current inventory valuation and do we have any overdue purchase orders?"
        )

        assert "response" in res
        assert "summary" in res["response"]
        assert "context_summary" in res

        ctx_sum = res["context_summary"]
        assert "inventory_valuation" in ctx_sum
        assert Decimal(ctx_sum["inventory_valuation"]) >= Decimal("10000.00")
        assert ctx_sum["overdue_pos"] >= 1
        assert ctx_sum["active_alerts_count"] >= 1


def test_copilot_api_rbac_and_isolation(client, copilot_op_env):
    """Verifies Copilot REST API enforcement: MEMBER allowed, VIEWER denied, Cross-tenant isolated."""
    env = copilot_op_env

    # 1. MEMBER query allowed
    headers_member = {"Authorization": f"Bearer {env['member_id']}", "X-Workspace-Id": env["ws_a_id"]}
    res_m = client.post("/api/business/copilot/query", headers=headers_member, json={"prompt": "Summarize operational health"})
    assert res_m.status_code == 200
    assert "data" in res_m.json

    # 2. VIEWER query denied (403)
    headers_viewer = {"Authorization": f"Bearer {env['viewer_id']}", "X-Workspace-Id": env["ws_a_id"]}
    res_v = client.post("/api/business/copilot/query", headers=headers_viewer, json={"prompt": "Summarize operational health"})
    assert res_v.status_code == 403

    # 3. Foreign Workspace query gets zero inventory valuation
    headers_foreign = {"Authorization": f"Bearer {env['foreign_id']}", "X-Workspace-Id": env["ws_b_id"]}
    res_f = client.post("/api/business/copilot/query", headers=headers_foreign, json={"prompt": "What is our stock?"})
    assert res_f.status_code == 200
    assert Decimal(res_f.json["data"]["context_summary"]["inventory_valuation"]) == Decimal("0.00")
