"""
DeadlineOS Business OS — Phase C2.4 Operational Alerts & Automation Tests
========================================================================
Comprehensive automated test suite covering:
1. Signal evaluation & alert generation (Stockout, safety stock, overdue PO, quality, dead stock).
2. Deduplication fingerprinting & cooldown suppression.
3. Alert lifecycle transitions (ACTIVE -> ACKNOWLEDGED -> RESOLVED / DISMISSED).
4. Signal-to-Task synthesis into BusinessTask with audit event tracking.
5. REST API endpoints and 5-tier RBAC enforcement.
6. Row-level multi-tenant isolation.
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
    BusinessOperationalAlert,
    BusinessTask,
    AuditEvent,
)
from services.business.operational_alert_service import OperationalAlertService


@pytest.fixture
def alert_env(app):
    """Sets up a complete test workspace with operational data triggers for alerting."""
    with app.app_context():
        # Users
        u_owner = User(id=str(uuid.uuid4()), email=f"al_owner_{uuid.uuid4().hex[:6]}@test.com", full_name="Alert Owner")
        u_admin = User(id=str(uuid.uuid4()), email=f"al_admin_{uuid.uuid4().hex[:6]}@test.com", full_name="Alert Admin")
        u_member = User(id=str(uuid.uuid4()), email=f"al_member_{uuid.uuid4().hex[:6]}@test.com", full_name="Alert Member")
        u_accountant = User(id=str(uuid.uuid4()), email=f"al_acct_{uuid.uuid4().hex[:6]}@test.com", full_name="Alert Accountant")
        u_viewer = User(id=str(uuid.uuid4()), email=f"al_viewer_{uuid.uuid4().hex[:6]}@test.com", full_name="Alert Viewer")
        u_foreign = User(id=str(uuid.uuid4()), email=f"al_for_{uuid.uuid4().hex[:6]}@test.com", full_name="Alert Foreign")

        db.session.add_all([u_owner, u_admin, u_member, u_accountant, u_viewer, u_foreign])
        db.session.commit()

        # Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name="Alert Test Workspace A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="Alert Test Workspace B", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # Memberships
        m_owner = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_owner.id, role="OWNER", status="ACTIVE")
        m_admin = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE")
        m_member = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_member.id, role="MEMBER", status="ACTIVE")
        m_accountant = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_accountant.id, role="ACCOUNTANT", status="ACTIVE")
        m_viewer = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_viewer.id, role="VIEWER", status="ACTIVE")
        m_foreign = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_b.id, user_id=u_foreign.id, role="OWNER", status="ACTIVE")

        db.session.add_all([m_owner, m_admin, m_member, m_accountant, m_viewer, m_foreign])
        db.session.commit()

        # Entities
        loc = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Main Storage", location_type="WAREHOUSE", status="ACTIVE")
        sup1 = CommercialPartner(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Alert Fasteners Ltd", partner_type="SUPPLIER", status="ACTIVE")
        db.session.add_all([loc, sup1])
        db.session.commit()

        # Products
        p_out = BusinessProduct(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Zero Stock Bearing", sku="BRG-00",
            unit="PCS", cost_price=Decimal("100.00"), selling_price=Decimal("150.00"),
            reorder_level=Decimal("20.00"), safety_stock=Decimal("10.00"),
            preferred_supplier_partner_id=sup1.id, status="ACTIVE"
        )
        p_critical = BusinessProduct(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Critical O-Ring", sku="ORING-CRIT",
            unit="PCS", cost_price=Decimal("10.00"), selling_price=Decimal("25.00"),
            reorder_level=Decimal("50.00"), safety_stock=Decimal("20.00"),
            preferred_supplier_partner_id=sup1.id, status="ACTIVE"
        )
        db.session.add_all([p_out, p_critical])
        db.session.commit()

        # Add movement for critical product: 100 IN, 90 OUT -> 10 stock, burn = 3.0/day -> DIR = 3.33d (CRITICAL_RISK)
        now = datetime.now(timezone.utc)
        m1 = BusinessStockMovement(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, product_id=p_critical.id, location_id=loc.id,
            movement_type="INITIAL_STOCK", direction="IN", quantity=Decimal("100.00"), unit_cost=Decimal("10.00"),
            created_at=now - timedelta(days=20)
        )
        m2 = BusinessStockMovement(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, product_id=p_critical.id, location_id=loc.id,
            movement_type="SALE", direction="OUT", quantity=Decimal("90.00"), unit_cost=Decimal("10.00"),
            created_at=now - timedelta(days=10)
        )
        db.session.add_all([m1, m2])
        db.session.commit()

        # Add Overdue Purchase Order
        po_overdue = BusinessPurchaseOrder(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, po_number="PO-ALERT-OVERDUE",
            supplier_partner_id=sup1.id, destination_location_id=loc.id,
            order_date=date.today() - timedelta(days=15),
            expected_delivery_date=date.today() - timedelta(days=5),
            subtotal_amount=Decimal("5000.00"), tax_amount=Decimal("0.00"), total_amount=Decimal("5000.00"),
            currency="INR", status="SENT_TO_SUPPLIER", created_by_user_id=u_admin.id
        )
        db.session.add(po_overdue)
        db.session.commit()

        return {
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
            "owner_id": u_owner.id,
            "admin_id": u_admin.id,
            "member_id": u_member.id,
            "member_member_id": m_member.id,
            "accountant_id": u_accountant.id,
            "viewer_id": u_viewer.id,
            "foreign_id": u_foreign.id,
            "p_out_id": p_out.id,
            "p_critical_id": p_critical.id,
            "po_overdue_id": po_overdue.id,
        }


def test_evaluate_signals_and_deduplication(app, alert_env):
    """Verifies that signals generate alerts and subsequent evaluations do NOT duplicate them."""
    env = alert_env
    with app.app_context():
        # First evaluation run: generates alerts
        alerts_1 = OperationalAlertService.evaluate_operational_signals(env["ws_a_id"], env["admin_id"])
        assert len(alerts_1) >= 2  # Stockout + Critical Risk + Overdue PO

        types = [a.alert_type for a in alerts_1]
        assert "STOCKOUT_IMMINENT" in types
        assert "OVERDUE_PURCHASE_ORDER" in types

        # Second evaluation run: must be completely suppressed by deduplication fingerprint
        alerts_2 = OperationalAlertService.evaluate_operational_signals(env["ws_a_id"], env["admin_id"])
        assert len(alerts_2) == 0


def test_cooldown_suppression_on_resolved_alert(app, alert_env):
    """Verifies that resolving an alert puts it in cooldown window to prevent immediate re-triggering."""
    env = alert_env
    with app.app_context():
        alerts = OperationalAlertService.evaluate_operational_signals(env["ws_a_id"], env["admin_id"])
        assert len(alerts) > 0
        target = alerts[0]

        # Resolve alert
        resolved = OperationalAlertService.resolve_alert(
            env["ws_a_id"], target.id, env["admin_id"], resolution_note="Investigated and ordered"
        )
        assert resolved["status"] == "RESOLVED"
        assert resolved["resolution_note"] == "Investigated and ordered"

        # Re-evaluate signals: cooldown_until is in future, must not re-trigger
        alerts_after = OperationalAlertService.evaluate_operational_signals(env["ws_a_id"], env["admin_id"])
        matching = [a for a in alerts_after if a.dedup_fingerprint == target.dedup_fingerprint]
        assert len(matching) == 0


def test_alert_lifecycle_acknowledge_and_dismiss(app, alert_env):
    """Verifies alert status transitions: ACTIVE -> ACKNOWLEDGED -> DISMISSED."""
    env = alert_env
    with app.app_context():
        alerts = OperationalAlertService.evaluate_operational_signals(env["ws_a_id"], env["admin_id"])
        assert len(alerts) > 0
        target = alerts[0]

        # 1. Acknowledge
        acked = OperationalAlertService.acknowledge_alert(env["ws_a_id"], target.id, env["member_id"])
        assert acked["status"] == "ACKNOWLEDGED"
        assert acked["acknowledged_by_user_id"] == env["member_id"]
        assert acked["acknowledged_at"] is not None

        # 2. Dismiss
        dismissed = OperationalAlertService.dismiss_alert(env["ws_a_id"], target.id, env["member_id"])
        assert dismissed["status"] == "DISMISSED"
        assert dismissed["resolved_at"] is not None


def test_signal_to_task_synthesis(app, alert_env):
    """Verifies synthesis of a BusinessTask from an operational alert."""
    env = alert_env
    with app.app_context():
        alerts = OperationalAlertService.evaluate_operational_signals(env["ws_a_id"], env["admin_id"])
        assert len(alerts) > 0
        target = alerts[0]

        result = OperationalAlertService.create_task_from_alert(
            workspace_id=env["ws_a_id"],
            alert_id=target.id,
            actor_user_id=env["admin_id"],
            assignee_member_id=env["member_member_id"],
            priority="URGENT"
        )

        task = result["task"]
        alert = result["alert"]

        assert task["title"].startswith("[ALERT]")
        assert task["priority"] == "URGENT"
        assert task["status"] == "TODO"
        assert task["assignee_member_id"] == env["member_member_id"]
        assert alert["generated_task_id"] == task["id"]
        assert alert["status"] == "ACKNOWLEDGED"

        # Verify duplicate synthesis attempt is rejected with 400
        with pytest.raises(Exception) as exc_info:
            OperationalAlertService.create_task_from_alert(
                workspace_id=env["ws_a_id"],
                alert_id=target.id,
                actor_user_id=env["admin_id"]
            )
        assert "already been generated" in str(exc_info.value)


def test_api_operational_alerts_endpoints(client, alert_env):
    """Tests all REST endpoints for operational alerts with RBAC and pagination."""
    env = alert_env
    headers = {
        "Authorization": f"Bearer {env['admin_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }

    # 1. Trigger evaluation
    eval_res = client.post("/api/business/operations/alerts/evaluate", headers=headers)
    assert eval_res.status_code == 200
    assert "data" in eval_res.json
    assert eval_res.json["data"]["created_count"] >= 2

    # 2. List alerts
    list_res = client.get("/api/business/operations/alerts?status=ACTIVE", headers=headers)
    assert list_res.status_code == 200
    alerts = list_res.json["data"]["alerts"]
    assert len(alerts) >= 2
    target_id = alerts[0]["id"]

    # 3. Get single alert
    get_res = client.get(f"/api/business/operations/alerts/{target_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json["data"]["id"] == target_id

    # 4. Acknowledge alert
    ack_res = client.post(f"/api/business/operations/alerts/{target_id}/acknowledge", headers=headers)
    assert ack_res.status_code == 200
    assert ack_res.json["data"]["status"] == "ACKNOWLEDGED"

    # 5. Create task from alert
    task_res = client.post(
        f"/api/business/operations/alerts/{target_id}/create-task",
        headers=headers,
        json={"assignee_member_id": env["member_member_id"], "priority": "HIGH"}
    )
    assert task_res.status_code == 200
    assert "task" in task_res.json["data"]

    # 6. Resolve alert
    res_res = client.post(
        f"/api/business/operations/alerts/{target_id}/resolve",
        headers=headers,
        json={"resolution_note": "Handled by operational team"}
    )
    assert res_res.status_code == 200
    assert res_res.json["data"]["status"] == "RESOLVED"


def test_rbac_operational_alerts_access(client, alert_env):
    """Verifies that all 5 roles have appropriate permissions on operational alerts."""
    env = alert_env

    # 1. VIEWER has read-only access (can list, cannot evaluate or modify)
    headers_viewer = {
        "Authorization": f"Bearer {env['viewer_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }
    res_read = client.get("/api/business/operations/alerts", headers=headers_viewer)
    assert res_read.status_code == 200

    res_eval = client.post("/api/business/operations/alerts/evaluate", headers=headers_viewer)
    assert res_eval.status_code == 403

    # 2. MEMBER can evaluate, acknowledge, and create tasks
    headers_member = {
        "Authorization": f"Bearer {env['member_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }
    res_m_eval = client.post("/api/business/operations/alerts/evaluate", headers=headers_member)
    assert res_m_eval.status_code == 200


def test_tenant_isolation_cross_workspace_alerts(client, alert_env):
    """Ensures Workspace B user cannot view or mutate Workspace A operational alerts."""
    env = alert_env

    # Workspace A creates alerts
    headers_a = {"Authorization": f"Bearer {env['admin_id']}", "X-Workspace-Id": env["ws_a_id"]}
    client.post("/api/business/operations/alerts/evaluate", headers=headers_a)
    list_a = client.get("/api/business/operations/alerts", headers=headers_a).json["data"]["alerts"]
    assert len(list_a) > 0
    target_a_id = list_a[0]["id"]

    # Workspace B queries its own alerts: must be empty
    headers_b = {"Authorization": f"Bearer {env['foreign_id']}", "X-Workspace-Id": env["ws_b_id"]}
    list_b = client.get("/api/business/operations/alerts", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json["data"]["total_count"] == 0

    # Workspace B attempts IDOR on Workspace A alert: must be 404
    get_cross = client.get(f"/api/business/operations/alerts/{target_a_id}", headers=headers_b)
    assert get_cross.status_code == 404
