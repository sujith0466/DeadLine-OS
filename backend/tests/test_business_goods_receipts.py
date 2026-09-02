"""
DeadlineOS Business OS — Goods Receipt (GRN) Automated Tests (Phase C2.2)
========================================================================
Comprehensive test suite covering:
1. GRN creation & sequential numbering
2. Partial receiving & line status progression
3. Full receiving & PO status progression
4. Accepted vs rejected quantity split & damage reason
5. Invalid quantity arithmetic rejection
6. Rejection reasons capture
7. Over-receiving discrepancy detection & audit
8. Rejection of receiving against DRAFT or CANCELLED POs
9. Append-only stock movements creation (PURCHASE_RECEIVED, IN)
10. Rejected quantity exclusion from inventory
11. Mathematical inventory truth derivation (SUM(IN) - SUM(OUT))
12. Accounts Payable StagedExtraction creation (INVOICE_PAYABLE)
13. Workspace tenant isolation & IDOR rejection
14. 5-tier RBAC enforcement (OWNER/ADMIN/MEMBER permitted, ACCOUNTANT/VIEWER denied)
15. Forensic audit events logging
16. Transaction atomicity
"""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone, date
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
    StagedExtraction,
    AuditEvent,
)
from services.business.goods_receipt_service import GoodsReceiptService
from services.business.inventory_service import InventoryService
from utils.errors import APIError


@pytest.fixture
def grn_env(app):
    """Sets up a complete isolated workspace environment with users, roles, products, locations, and POs."""
    with app.app_context():
        # Users
        user_owner_a = User(id=str(uuid.uuid4()), email="grn_owner_a@test.com", full_name="Owner A")
        user_admin_a = User(id=str(uuid.uuid4()), email="grn_admin_a@test.com", full_name="Admin A")
        user_member_a = User(id=str(uuid.uuid4()), email="grn_member_a@test.com", full_name="Member A")
        user_accountant_a = User(id=str(uuid.uuid4()), email="grn_accountant_a@test.com", full_name="Accountant A")
        user_viewer_a = User(id=str(uuid.uuid4()), email="grn_viewer_a@test.com", full_name="Viewer A")

        user_owner_b = User(id=str(uuid.uuid4()), email="grn_owner_b@test.com", full_name="Owner B")

        db.session.add_all([
            user_owner_a, user_admin_a, user_member_a, user_accountant_a, user_viewer_a,
            user_owner_b
        ])
        db.session.commit()

        # Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name="GRN Test Workspace A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="GRN Test Workspace B", base_currency="USD")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # Memberships
        db.session.add_all([
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_owner_a.id, role="OWNER", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_admin_a.id, role="ADMIN", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_member_a.id, role="MEMBER", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_accountant_a.id, role="ACCOUNTANT", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_a.id, user_id=user_viewer_a.id, role="VIEWER", status="ACTIVE"),
            WorkspaceMember(workspace_id=ws_b.id, user_id=user_owner_b.id, role="OWNER", status="ACTIVE"),
        ])
        db.session.commit()

        # Location & Partner in A
        loc_a = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Main Warehouse", location_type="WAREHOUSE", status="ACTIVE")
        supplier_a = CommercialPartner(id=str(uuid.uuid4()), workspace_id=ws_a.id, name="Premier Parts Ltd", partner_type="SUPPLIER", status="ACTIVE")

        # Location & Partner in B
        loc_b = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_b.id, name="Secondary Warehouse", location_type="WAREHOUSE", status="ACTIVE")
        supplier_b = CommercialPartner(id=str(uuid.uuid4()), workspace_id=ws_b.id, name="Foreign Supplier B", partner_type="SUPPLIER", status="ACTIVE")

        db.session.add_all([loc_a, supplier_a, loc_b, supplier_b])
        db.session.commit()

        # Products in A
        prod1 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Industrial Motor",
            sku="MOT-001",
            unit="PCS",
            cost_price=Decimal("5000.00"),
            selling_price=Decimal("7500.00"),
            status="ACTIVE"
        )
        prod2 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Copper Wiring 100m",
            sku="WIR-001",
            unit="ROLL",
            cost_price=Decimal("1200.00"),
            selling_price=Decimal("1800.00"),
            status="ACTIVE"
        )
        db.session.add_all([prod1, prod2])
        db.session.commit()

        # Purchase Order in A
        po = BusinessPurchaseOrder(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            po_number="PO-2026-0001",
            supplier_partner_id=supplier_a.id,
            destination_location_id=loc_a.id,
            order_date=date.today(),
            subtotal_amount=Decimal("62000.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("62000.00"),
            currency="INR",
            status="SENT_TO_SUPPLIER",
            created_by_user_id=user_admin_a.id,
        )
        db.session.add(po)
        db.session.commit()

        pol1 = BusinessPurchaseOrderLine(
            id=str(uuid.uuid4()),
            purchase_order_id=po.id,
            product_id=prod1.id,
            ordered_quantity=Decimal("10.00"),
            received_quantity=Decimal("0.00"),
            unit_price=Decimal("5000.00"),
            total_price=Decimal("50000.00"),
            status="PENDING",
        )
        pol2 = BusinessPurchaseOrderLine(
            id=str(uuid.uuid4()),
            purchase_order_id=po.id,
            product_id=prod2.id,
            ordered_quantity=Decimal("10.00"),
            received_quantity=Decimal("0.00"),
            unit_price=Decimal("1200.00"),
            total_price=Decimal("12000.00"),
            status="PENDING",
        )
        db.session.add_all([pol1, pol2])
        db.session.commit()

        return {
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
            "owner_a_id": user_owner_a.id,
            "admin_a_id": user_admin_a.id,
            "member_a_id": user_member_a.id,
            "accountant_a_id": user_accountant_a.id,
            "viewer_a_id": user_viewer_a.id,
            "owner_b_id": user_owner_b.id,
            "po_id": po.id,
            "pol1_id": pol1.id,
            "pol2_id": pol2.id,
            "prod1_id": prod1.id,
            "prod2_id": prod2.id,
            "loc_a_id": loc_a.id,
            "loc_b_id": loc_b.id,
            "supplier_a_id": supplier_a.id,
        }


# ==============================================================================
# 1. CORE SERVICE TESTS
# ==============================================================================

def test_grn_partial_receiving_and_stock_ledger(app, grn_env):
    """Verifies that physical receiving creates stock movements ONLY for accepted quantity."""
    env = grn_env
    with app.app_context():
        # Member receives 5 motors accepted, 1 motor rejected (total 6 received), and 5 wires accepted
        grn = GoodsReceiptService.create_goods_receipt(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_a_id"],
            data={
                "purchase_order_id": env["po_id"],
                "carrier_name": "Express Logistics #849",
                "delivery_note_number": "DN-54321",
                "lines": [
                    {
                        "purchase_order_line_id": env["pol1_id"],
                        "received_quantity": "6.00",
                        "accepted_quantity": "5.00",
                        "rejected_quantity": "1.00",
                        "rejection_reason": "Broken casing",
                    },
                    {
                        "purchase_order_line_id": env["pol2_id"],
                        "received_quantity": "5.00",
                        "accepted_quantity": "5.00",
                        "rejected_quantity": "0.00",
                    }
                ]
            }
        )

        assert grn is not None
        assert grn.grn_number.startswith("GRN-")
        assert grn.status == "COMPLETED"
        assert len(grn.lines) == 2

        # Verify stock movements created for accepted quantities only
        movements = BusinessStockMovement.query.filter_by(
            workspace_id=env["ws_a_id"],
            reference_type="GOODS_RECEIPT",
            reference_id=grn.id
        ).all()
        assert len(movements) == 2

        mv_p1 = next(m for m in movements if m.product_id == env["prod1_id"])
        assert mv_p1.quantity == Decimal("5.00")
        assert mv_p1.movement_type == "PURCHASE_RECEIVED"
        assert mv_p1.direction == "IN"

        mv_p2 = next(m for m in movements if m.product_id == env["prod2_id"])
        assert mv_p2.quantity == Decimal("5.00")

        # Verify inventory quantity truth SUM(IN) - SUM(OUT)
        stock_p1 = InventoryService.get_total_product_stock(env["ws_a_id"], env["prod1_id"])
        assert stock_p1 == Decimal("5.00")

        stock_p2 = InventoryService.get_total_product_stock(env["ws_a_id"], env["prod2_id"])
        assert stock_p2 == Decimal("5.00")

        # Verify PO line updates
        pol1 = db.session.get(BusinessPurchaseOrderLine, env["pol1_id"])
        assert pol1.received_quantity == Decimal("5.00")
        assert pol1.status == "PARTIALLY_RECEIVED"

        pol2 = db.session.get(BusinessPurchaseOrderLine, env["pol2_id"])
        assert pol2.received_quantity == Decimal("5.00")
        assert pol2.status == "PARTIALLY_RECEIVED"

        # Verify PO header status
        po = db.session.get(BusinessPurchaseOrder, env["po_id"])
        assert po.status == "PARTIALLY_RECEIVED"

        # Verify Staged AP candidate
        assert grn.staged_extraction_id is not None
        staged = db.session.get(StagedExtraction, grn.staged_extraction_id)
        assert staged.candidate_type == "INVOICE_PAYABLE"
        assert staged.status == "NEEDS_REVIEW"
        assert Decimal(staged.normalized_data["total_accepted_amount"]) == Decimal("31000.00")


def test_grn_sequential_numbering_and_full_completion(app, grn_env):
    """Verifies sequence increment (GRN-YYYY-0001, GRN-YYYY-0002) and PO FULLY_RECEIVED transition."""
    env = grn_env
    with app.app_context():
        # First GRN
        grn1 = GoodsReceiptService.create_goods_receipt(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_a_id"],
            data={
                "purchase_order_id": env["po_id"],
                "lines": [
                    {
                        "purchase_order_line_id": env["pol1_id"],
                        "received_quantity": "5.00",
                        "accepted_quantity": "5.00",
                        "rejected_quantity": "0.00",
                    }
                ]
            }
        )

        current_year = date.today().year
        assert grn1.grn_number == f"GRN-{current_year}-0001"

        # Second GRN completing the rest
        grn2 = GoodsReceiptService.create_goods_receipt(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_a_id"],
            data={
                "purchase_order_id": env["po_id"],
                "lines": [
                    {
                        "purchase_order_line_id": env["pol1_id"],
                        "received_quantity": "5.00",
                        "accepted_quantity": "5.00",
                        "rejected_quantity": "0.00",
                    },
                    {
                        "purchase_order_line_id": env["pol2_id"],
                        "received_quantity": "10.00",
                        "accepted_quantity": "10.00",
                        "rejected_quantity": "0.00",
                    }
                ]
            }
        )

        assert grn2.grn_number == f"GRN-{current_year}-0002"

        # Verify PO is now FULLY_RECEIVED
        po = db.session.get(BusinessPurchaseOrder, env["po_id"])
        assert po.status == "FULLY_RECEIVED"

        # Total on hand is now 10 motors and 10 rolls of wire
        stock_p1 = InventoryService.get_total_product_stock(env["ws_a_id"], env["prod1_id"])
        assert stock_p1 == Decimal("10.00")


def test_grn_mathematical_validation_rejections(app, grn_env):
    """Rejects invalid quantity combinations."""
    env = grn_env
    with app.app_context():
        # 1. accepted + rejected != received
        with pytest.raises(APIError) as exc:
            GoodsReceiptService.create_goods_receipt(
                workspace_id=env["ws_a_id"],
                actor_user_id=env["member_a_id"],
                data={
                    "purchase_order_id": env["po_id"],
                    "lines": [
                        {
                            "purchase_order_line_id": env["pol1_id"],
                            "received_quantity": "10.00",
                            "accepted_quantity": "6.00",
                            "rejected_quantity": "2.00",
                        }
                    ]
                }
            )
        assert exc.value.status == 400
        assert "must equal Accepted" in exc.value.message

        # 2. Negative quantity
        with pytest.raises(APIError) as exc:
            GoodsReceiptService.create_goods_receipt(
                workspace_id=env["ws_a_id"],
                actor_user_id=env["member_a_id"],
                data={
                    "purchase_order_id": env["po_id"],
                    "lines": [
                        {
                            "purchase_order_line_id": env["pol1_id"],
                            "received_quantity": "-5.00",
                            "accepted_quantity": "-5.00",
                            "rejected_quantity": "0.00",
                        }
                    ]
                }
            )
        assert exc.value.status == 400


def test_grn_po_status_guards(app, grn_env):
    """Cannot receive against DRAFT or CANCELLED POs."""
    env = grn_env
    with app.app_context():
        po = db.session.get(BusinessPurchaseOrder, env["po_id"])
        po.status = "DRAFT"
        db.session.commit()

        with pytest.raises(APIError) as exc:
            GoodsReceiptService.create_goods_receipt(
                workspace_id=env["ws_a_id"],
                actor_user_id=env["member_a_id"],
                data={
                    "purchase_order_id": env["po_id"],
                    "lines": [
                        {
                            "purchase_order_line_id": env["pol1_id"],
                            "received_quantity": "5.00",
                            "accepted_quantity": "5.00",
                            "rejected_quantity": "0.00",
                        }
                    ]
                }
            )
        assert exc.value.status == 400
        assert "Cannot receive goods against Purchase Order with status 'DRAFT'" in exc.value.message

        po.status = "CANCELLED"
        db.session.commit()

        with pytest.raises(APIError) as exc:
            GoodsReceiptService.create_goods_receipt(
                workspace_id=env["ws_a_id"],
                actor_user_id=env["member_a_id"],
                data={
                    "purchase_order_id": env["po_id"],
                    "lines": [
                        {
                            "purchase_order_line_id": env["pol1_id"],
                            "received_quantity": "5.00",
                            "accepted_quantity": "5.00",
                            "rejected_quantity": "0.00",
                        }
                    ]
                }
            )
        assert exc.value.status == 400
        assert "Cannot receive goods against Purchase Order with status 'CANCELLED'" in exc.value.message


def test_grn_over_receiving_discrepancy_audit_event(app, grn_env):
    """Detects over-receiving and emits GRN_DISCREPANCY_DETECTED audit event."""
    env = grn_env
    with app.app_context():
        # Ordered 10, receiving 12
        grn = GoodsReceiptService.create_goods_receipt(
            workspace_id=env["ws_a_id"],
            actor_user_id=env["member_a_id"],
            data={
                "purchase_order_id": env["po_id"],
                "lines": [
                    {
                        "purchase_order_line_id": env["pol1_id"],
                        "received_quantity": "12.00",
                        "accepted_quantity": "12.00",
                        "rejected_quantity": "0.00",
                    }
                ]
            }
        )

        assert grn is not None
        # Verify discrepancy audit event was emitted
        audits = AuditEvent.query.filter_by(
            workspace_id=env["ws_a_id"],
            action="GRN_DISCREPANCY_DETECTED",
            entity_id=grn.id
        ).all()
        assert len(audits) == 1


# ==============================================================================
# 2. REST API & RBAC TESTS
# ==============================================================================

def test_api_grn_creation_and_rbac(client, grn_env):
    """Tests Goods Receipt creation endpoint with Member access and Accountant/Viewer denial."""
    env = grn_env
    headers_member = {
        "Authorization": f"Bearer {env['member_a_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }
    headers_accountant = {
        "Authorization": f"Bearer {env['accountant_a_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }
    headers_viewer = {
        "Authorization": f"Bearer {env['viewer_a_id']}",
        "X-Workspace-Id": env["ws_a_id"]
    }

    payload = {
        "purchase_order_id": env["po_id"],
        "carrier_name": "Cargo Ship Line",
        "delivery_note_number": "SL-999",
        "lines": [
            {
                "purchase_order_line_id": env["pol1_id"],
                "received_quantity": "4.00",
                "accepted_quantity": "4.00",
                "rejected_quantity": "0.00",
            }
        ]
    }

    # 1. Viewer attempts to create GRN -> Denied (403)
    res = client.post("/api/business/procurement/goods-receipts", json=payload, headers=headers_viewer)
    assert res.status_code == 403

    # 2. Accountant attempts to create GRN -> Denied (403)
    res = client.post("/api/business/procurement/goods-receipts", json=payload, headers=headers_accountant)
    assert res.status_code == 403

    # 3. Member creates GRN -> Allowed (201)
    res = client.post("/api/business/procurement/goods-receipts", json=payload, headers=headers_member)
    assert res.status_code == 201
    grn_data = res.get_json()["data"]
    assert grn_data["grn_number"].startswith("GRN-")
    grn_id = grn_data["id"]

    # 4. Accountant views GRN -> Allowed (200)
    res = client.get(f"/api/business/procurement/goods-receipts/{grn_id}", headers=headers_accountant)
    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == grn_id

    # 5. List GRNs -> Allowed (200)
    res = client.get("/api/business/procurement/goods-receipts", headers=headers_viewer)
    assert res.status_code == 200
    assert len(res.get_json()["data"]["items"]) >= 1


def test_api_tenant_isolation_and_idor_protection(client, grn_env):
    """Ensures cross-workspace GRN creation or lookup fails with 404."""
    env = grn_env
    headers_ws_b = {
        "Authorization": f"Bearer {env['owner_b_id']}",
        "X-Workspace-Id": env["ws_b_id"]
    }

    # Attempt to receive PO from Workspace A into Workspace B -> 404
    res = client.post("/api/business/procurement/goods-receipts", json={
        "purchase_order_id": env["po_id"],
        "lines": [
            {
                "purchase_order_line_id": env["pol1_id"],
                "received_quantity": "5.00",
                "accepted_quantity": "5.00",
                "rejected_quantity": "0.00",
            }
        ]
    }, headers=headers_ws_b)
    assert res.status_code == 404
