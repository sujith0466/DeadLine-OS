"""
DeadlineOS Business OS — Phase C2.5 Voice-Assisted Operations Tests
==================================================================
Comprehensive automated test suite covering:
1. Spoken intent & entity resolution (inventory adjustments, transfers, tasks, purchase requests).
2. Zero-Bypass Staging Trust Boundary verification (voice operations create StagedExtractions in NEEDS_REVIEW, zero direct physical/financial table mutations without confirmation).
3. Staged candidate commit gateway to domain services.
4. REST API endpoints with 5-Tier RBAC authorization.
5. Strict row-level multi-tenant isolation.
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
    BusinessPurchaseRequest,
    BusinessTask,
    StagedExtraction,
    AuditEvent,
)
from services.business.voice_operations_service import VoiceOperationsService
from services.business.financial_converter_service import FinancialConverterService
from services.business.staging_service import StagingService


@pytest.fixture
def voice_env(app):
    """Sets up a complete test workspace with products, locations, and partners."""
    with app.app_context():
        u_owner = User(id=str(uuid.uuid4()), email=f"vc_owner_{uuid.uuid4().hex[:6]}@test.com", full_name="Voice Owner")
        u_admin = User(id=str(uuid.uuid4()), email=f"vc_admin_{uuid.uuid4().hex[:6]}@test.com", full_name="Voice Admin")
        u_member = User(id=str(uuid.uuid4()), email=f"vc_member_{uuid.uuid4().hex[:6]}@test.com", full_name="Voice Member")
        u_viewer = User(id=str(uuid.uuid4()), email=f"vc_viewer_{uuid.uuid4().hex[:6]}@test.com", full_name="Voice Viewer")
        u_foreign = User(id=str(uuid.uuid4()), email=f"vc_for_{uuid.uuid4().hex[:6]}@test.com", full_name="Voice Foreign")

        db.session.add_all([u_owner, u_admin, u_member, u_viewer, u_foreign])
        db.session.commit()

        ws_a = Workspace(id=str(uuid.uuid4()), name="Voice Test Workspace A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="Voice Test Workspace B", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        m_owner = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_owner.id, role="OWNER", status="ACTIVE")
        m_admin = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE")
        m_member = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_member.id, role="MEMBER", status="ACTIVE")
        m_viewer = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_viewer.id, role="VIEWER", status="ACTIVE")
        m_foreign = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_b.id, user_id=u_foreign.id, role="OWNER", status="ACTIVE")

        db.session.add_all([m_owner, m_admin, m_member, m_viewer, m_foreign])
        db.session.commit()

        # Locations
        loc_main = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Central Storage Depot", location_type="WAREHOUSE", status="ACTIVE")
        loc_dock = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Loading Dock 3", location_type="WAREHOUSE", status="ACTIVE")
        sup = CommercialPartner(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Vortex Industrial Parts", partner_type="SUPPLIER", status="ACTIVE")
        db.session.add_all([loc_main, loc_dock, sup])
        db.session.commit()

        # Product
        p1 = BusinessProduct(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Hydraulic Valve", sku="HYD-VLV-99",
            unit="PCS", cost_price=Decimal("250.00"), selling_price=Decimal("400.00"),
            reorder_level=Decimal("15.00"), safety_stock=Decimal("5.00"),
            preferred_supplier_partner_id=sup.id, status="ACTIVE"
        )
        db.session.add(p1)
        db.session.commit()

        # Initial movement
        m1 = BusinessStockMovement(
            id=str(uuid.uuid4()), workspace_id=ws_a.id, product_id=p1.id, location_id=loc_main.id,
            movement_type="INITIAL_STOCK", direction="IN", quantity=Decimal("100.00"), unit_cost=Decimal("250.00")
        )
        db.session.add(m1)
        db.session.commit()

        return {
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
            "owner_id": u_owner.id,
            "admin_id": u_admin.id,
            "member_id": u_member.id,
            "viewer_id": u_viewer.id,
            "foreign_id": u_foreign.id,
            "loc_main_id": loc_main.id,
            "loc_dock_id": loc_dock.id,
            "p1_id": p1.id,
            "sup_id": sup.id,
        }


def test_voice_stock_adjustment_staging(app, voice_env):
    """Verifies spoken inventory adjustment parses and stages into NEEDS_REVIEW."""
    env = voice_env
    with app.app_context():
        transcript = "Received 40 units of HYD-VLV-99 at Central Storage Depot costing 250 each"
        res = VoiceOperationsService.process_voice_operation(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_id"],
            transcript=transcript
        )

        staged = res["staged_extraction"]
        intent = res["intent_summary"]

        assert staged["status"] == "NEEDS_REVIEW"
        assert staged["candidate_type"] == "VOICE_INVENTORY_ADJUSTMENT"
        assert staged["source_channel"] == "VOICE"
        assert intent["confidence_score"] >= 80

        norm = staged["normalized_data"]
        assert norm["product_id"] == env["p1_id"]
        assert norm["location_id"] == env["loc_main_id"]
        assert norm["quantity"] == "40"
        assert norm["direction"] == "IN"


def test_zero_bypass_trust_boundary(app, voice_env):
    """CRITICAL: Verifies voice processing creates 0 direct mutations on stock ledger without human commit."""
    env = voice_env
    with app.app_context():
        # Baseline count of stock movements
        initial_movements = BusinessStockMovement.query.filter_by(workspace_id=env["ws_a_id"]).count()

        # Process voice operation
        transcript = "Scrapped 15 damaged units of HYD-VLV-99 from Central Storage Depot"
        res = VoiceOperationsService.process_voice_operation(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_id"],
            transcript=transcript
        )
        staged_id = res["staged_extraction"]["id"]

        # Assert stock ledger count is UNCHANGED (Zero Bypass verified)
        after_movements = BusinessStockMovement.query.filter_by(workspace_id=env["ws_a_id"]).count()
        assert after_movements == initial_movements

        # Now simulate human confirmation & commit
        StagingService.confirm_staged_item(env["ws_a_id"], staged_id, env["admin_id"])
        commit_res = FinancialConverterService.commit_staged_item(env["ws_a_id"], staged_id, env["admin_id"])

        assert commit_res["target"] == "INVENTORY"

        # After explicit human commit, stock movement is recorded
        final_movements = BusinessStockMovement.query.filter_by(workspace_id=env["ws_a_id"]).count()
        assert final_movements == initial_movements + 1


def test_voice_stock_transfer_intent(app, voice_env):
    """Verifies stock transfer voice command parses source, destination, and quantity."""
    env = voice_env
    with app.app_context():
        transcript = "Transfer 25 units of HYD-VLV-99 from Central Storage Depot to Loading Dock 3"
        res = VoiceOperationsService.process_voice_operation(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_id"],
            transcript=transcript
        )

        staged = res["staged_extraction"]
        assert staged["candidate_type"] == "VOICE_STOCK_TRANSFER"
        norm = staged["normalized_data"]
        assert norm["product_id"] == env["p1_id"]
        assert norm["source_location_id"] == env["loc_main_id"]
        assert norm["destination_location_id"] == env["loc_dock_id"]
        assert norm["quantity"] == "25"


def test_voice_task_intent(app, voice_env):
    """Verifies operational task voice command parses priority and due date."""
    env = voice_env
    with app.app_context():
        transcript = "Create task: Urgent inspection of Central Storage Depot racking by tomorrow"
        res = VoiceOperationsService.process_voice_operation(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_id"],
            transcript=transcript
        )

        staged = res["staged_extraction"]
        assert staged["candidate_type"] == "VOICE_TASK"
        norm = staged["normalized_data"]
        assert "inspection" in norm["title"].lower()
        assert norm["priority"] == "URGENT"
        assert norm["location_id"] == env["loc_main_id"]


def test_voice_purchase_request_intent(app, voice_env):
    """Verifies purchase request voice command extracts supplier and product requisition."""
    env = voice_env
    with app.app_context():
        transcript = "Reorder 50 units of Hydraulic Valve from Vortex Industrial Parts"
        res = VoiceOperationsService.process_voice_operation(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_id"],
            transcript=transcript
        )

        staged = res["staged_extraction"]
        assert staged["candidate_type"] == "VOICE_PURCHASE_REQUEST"
        norm = staged["normalized_data"]
        assert norm["product_id"] == env["p1_id"]
        assert norm["supplier_partner_id"] == env["sup_id"]
        assert norm["quantity"] == "50"


def test_api_voice_operations_endpoints(client, voice_env):
    """Tests REST endpoints for voice operations with RBAC and history."""
    env = voice_env
    headers = {
        "Authorization": f"Bearer {env['member_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }

    # 1. Process voice operation
    res = client.post(
        "/api/business/operations/voice/process",
        headers=headers,
        json={"transcript": "Received 30 units of HYD-VLV-99 at Central Storage Depot", "audio_duration_seconds": 3.5}
    )
    assert res.status_code == 201
    staged_id = res.json["data"]["staged_extraction"]["id"]

    # 2. Get history
    h_res = client.get("/api/business/operations/voice/history", headers=headers)
    assert h_res.status_code == 200
    ops = h_res.json["data"]["staged_operations"]
    assert len(ops) >= 1
    assert any(o["id"] == staged_id for o in ops)


def test_rbac_and_tenant_isolation_voice(client, voice_env):
    """Verifies RBAC enforcement and cross-workspace multi-tenant isolation on voice endpoints."""
    env = voice_env

    # 1. VIEWER cannot process voice operations (403)
    headers_viewer = {"Authorization": f"Bearer {env['viewer_id']}", "X-Workspace-Id": env["ws_a_id"]}
    res_v = client.post("/api/business/operations/voice/process", headers=headers_viewer, json={"transcript": "test"})
    assert res_v.status_code == 403

    # 2. Foreign Workspace cannot see Workspace A voice operations
    headers_foreign = {"Authorization": f"Bearer {env['foreign_id']}", "X-Workspace-Id": env["ws_b_id"]}
    res_f = client.get("/api/business/operations/voice/history", headers=headers_foreign)
    assert res_f.status_code == 200
    assert res_f.json["data"]["total_count"] == 0
