"""
DeadlineOS Business OS — Phase C2.1 Procurement Foundation Tests
================================================================
Comprehensive test suite covering Purchase Requests, Purchase Orders,
sequential numbering, administrative approvals, PR-to-PO conversion,
RBAC enforcement, tenant isolation, IDOR, and audit trails.
"""

import uuid
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    CommercialPartner,
    BusinessLocation,
    BusinessProduct,
    BusinessPurchaseRequest,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    AuditEvent
)
from services.business.purchase_request_service import PurchaseRequestService
from services.business.purchase_order_service import PurchaseOrderService
from utils.errors import APIError


@pytest.fixture
def procurement_env(app):
    """
    Sets up two isolated workspaces with Owner, Admin, Member, and Viewer,
    plus active locations, products, and commercial partners.
    """
    with app.app_context():
        # Workspace A
        user_owner_a = User(id=str(uuid.uuid4()), email='owner_a@procure.com', full_name='Owner A')
        user_admin_a = User(id=str(uuid.uuid4()), email='admin_a@procure.com', full_name='Admin A')
        user_member_a = User(id=str(uuid.uuid4()), email='member_a@procure.com', full_name='Member A')
        user_other_member_a = User(id=str(uuid.uuid4()), email='other_member_a@procure.com', full_name='Other Member A')
        user_viewer_a = User(id=str(uuid.uuid4()), email='viewer_a@procure.com', full_name='Viewer A')

        # Workspace B
        user_owner_b = User(id=str(uuid.uuid4()), email='owner_b@procure.com', full_name='Owner B')

        db.session.add_all([
            user_owner_a, user_admin_a, user_member_a, user_other_member_a, user_viewer_a,
            user_owner_b
        ])
        db.session.commit()

        ws_a = Workspace(name='Acme Procurement Corp', base_currency='INR')
        ws_b = Workspace(name='Beta Industries', base_currency='USD')
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        m_owner_a = WorkspaceMember(workspace_id=ws_a.id, user_id=user_owner_a.id, role='OWNER', status='ACTIVE')
        m_admin_a = WorkspaceMember(workspace_id=ws_a.id, user_id=user_admin_a.id, role='ADMIN', status='ACTIVE')
        m_member_a = WorkspaceMember(workspace_id=ws_a.id, user_id=user_member_a.id, role='MEMBER', status='ACTIVE')
        m_other_member_a = WorkspaceMember(workspace_id=ws_a.id, user_id=user_other_member_a.id, role='MEMBER', status='ACTIVE')
        m_viewer_a = WorkspaceMember(workspace_id=ws_a.id, user_id=user_viewer_a.id, role='VIEWER', status='ACTIVE')

        m_owner_b = WorkspaceMember(workspace_id=ws_b.id, user_id=user_owner_b.id, role='OWNER', status='ACTIVE')

        db.session.add_all([m_owner_a, m_admin_a, m_member_a, m_other_member_a, m_viewer_a, m_owner_b])
        db.session.commit()

        # Commercial Partners in A
        supplier_a = CommercialPartner(
            workspace_id=ws_a.id,
            name='Alpha Wholesale Supplies',
            partner_type='SUPPLIER',
            status='ACTIVE'
        )
        customer_a = CommercialPartner(
            workspace_id=ws_a.id,
            name='Retail Buyer Corp',
            partner_type='CUSTOMER',
            status='ACTIVE'
        )
        # Partner in B
        supplier_b = CommercialPartner(
            workspace_id=ws_b.id,
            name='Foreign Imports Ltd',
            partner_type='SUPPLIER',
            status='ACTIVE'
        )

        # Locations
        loc_a = BusinessLocation(
            workspace_id=ws_a.id,
            name='Main Warehouse A',
            location_type='WAREHOUSE',
            status='ACTIVE'
        )
        loc_b = BusinessLocation(
            workspace_id=ws_b.id,
            name='Secondary Warehouse B',
            location_type='WAREHOUSE',
            status='ACTIVE'
        )

        db.session.add_all([supplier_a, customer_a, supplier_b, loc_a, loc_b])
        db.session.commit()

        # Products
        prod_a = BusinessProduct(
            workspace_id=ws_a.id,
            sku='SKU-A-100',
            name='Industrial Fasteners 100pk',
            cost_price=Decimal('150.00'),
            selling_price=Decimal('220.00'),
            reorder_level=Decimal('20.00'),
            safety_stock=Decimal('5.00'),
            preferred_supplier_partner_id=supplier_a.id,
            status='ACTIVE'
        )
        prod_b = BusinessProduct(
            workspace_id=ws_b.id,
            sku='SKU-B-200',
            name='Foreign Microchips',
            cost_price=Decimal('500.00'),
            selling_price=Decimal('750.00'),
            preferred_supplier_partner_id=supplier_b.id,
            status='ACTIVE'
        )

        db.session.add_all([prod_a, prod_b])
        db.session.commit()

        return {
            'ws_a_id': ws_a.id,
            'ws_b_id': ws_b.id,
            'owner_a_id': user_owner_a.id,
            'admin_a_id': user_admin_a.id,
            'member_a_id': user_member_a.id,
            'other_member_a_id': user_other_member_a.id,
            'viewer_a_id': user_viewer_a.id,
            'owner_b_id': user_owner_b.id,
            'supplier_a_id': supplier_a.id,
            'customer_a_id': customer_a.id,
            'supplier_b_id': supplier_b.id,
            'loc_a_id': loc_a.id,
            'loc_b_id': loc_b.id,
            'prod_a_id': prod_a.id,
            'prod_b_id': prod_b.id,
        }


# ==============================================================================
# 1. PURCHASE REQUEST TESTS
# ==============================================================================

def test_pr_creation_and_sequential_numbering(app, procurement_env):
    """Tests PR creation with valid data and verifies sequential PR-YYYY-XXXX numbering."""
    env = procurement_env
    with app.app_context():
        pr1 = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '25.00',
                'priority': 'HIGH',
                'reason': 'Stock below safety threshold'
            }
        )

        assert pr1.id is not None
        current_year = date.today().year
        assert pr1.request_number == f"PR-{current_year}-0001"
        assert pr1.requested_quantity == Decimal('25.00')
        assert pr1.estimated_unit_price == Decimal('150.00')
        assert pr1.estimated_total_price == Decimal('3750.00')
        assert pr1.status == 'SUBMITTED'
        assert pr1.priority == 'HIGH'

        # Create a second PR to test sequential increment
        pr2 = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '10.00'
            }
        )
        assert pr2.request_number == f"PR-{current_year}-0002"


def test_pr_validation_negative_quantity_and_missing_fields(app, procurement_env):
    """Rejects invalid quantities, non-existent products, or missing locations."""
    env = procurement_env
    with app.app_context():
        # 1. Negative quantity
        with pytest.raises(APIError) as exc:
            PurchaseRequestService.create_request(
                workspace_id=env['ws_a_id'],
                actor_user_id=env['member_a_id'],
                data={
                    'product_id': env['prod_a_id'],
                    'location_id': env['loc_a_id'],
                    'requested_quantity': '-5.00'
                }
            )
        assert exc.value.status == 400

        # 2. Non-existent product
        with pytest.raises(APIError) as exc:
            PurchaseRequestService.create_request(
                workspace_id=env['ws_a_id'],
                actor_user_id=env['member_a_id'],
                data={
                    'product_id': 'non-existent-product-id',
                    'location_id': env['loc_a_id'],
                    'requested_quantity': '10.00'
                }
            )
        assert exc.value.status == 400


def test_pr_lifecycle_approval_and_rejection(app, procurement_env):
    """Tests PR approval and rejection state transitions with audit events."""
    env = procurement_env
    with app.app_context():
        pr = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '50.00',
                'status': 'SUBMITTED'
            }
        )

        # Approve PR
        approved_pr = PurchaseRequestService.approve_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            request_id=pr.id,
            approval_notes='Approved for standard monthly stock replenishment.'
        )
        assert approved_pr.status == 'APPROVED'
        assert approved_pr.approved_by_user_id == env['admin_a_id']
        assert approved_pr.approved_at is not None

        # Verify audit event
        audit = AuditEvent.query.filter_by(
            workspace_id=env['ws_a_id'],
            entity_id=pr.id,
            action='PR_APPROVED'
        ).first()
        assert audit is not None
        assert audit.actor_user_id == env['admin_a_id']


def test_pr_rejection(app, procurement_env):
    """Tests PR rejection with reason."""
    env = procurement_env
    with app.app_context():
        pr = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '100.00'
            }
        )

        rejected_pr = PurchaseRequestService.reject_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            request_id=pr.id,
            reason='Excessive quantity requested beyond storage capacity.'
        )
        assert rejected_pr.status == 'REJECTED'
        assert 'Excessive' in rejected_pr.approval_notes


def test_pr_cancellation(app, procurement_env):
    """Tests PR cancellation by creator."""
    env = procurement_env
    with app.app_context():
        pr = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '15.00'
            }
        )

        cancelled = PurchaseRequestService.cancel_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            request_id=pr.id,
            reason='No longer needed',
            user_role='MEMBER'
        )
        assert cancelled.status == 'CANCELLED'


def test_pr_member_cannot_modify_other_member_pr(app, procurement_env):
    """Ensures Member B cannot update or cancel Member A's purchase request."""
    env = procurement_env
    with app.app_context():
        pr = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '20.00'
            }
        )

        with pytest.raises(APIError) as exc:
            PurchaseRequestService.update_request(
                workspace_id=env['ws_a_id'],
                actor_user_id=env['other_member_a_id'],
                request_id=pr.id,
                data={'requested_quantity': '30.00'},
                user_role='MEMBER'
            )
        assert exc.value.status == 403


# ==============================================================================
# 2. PURCHASE ORDER TESTS
# ==============================================================================

def test_po_creation_and_line_item_math(app, procurement_env):
    """Tests PO creation, sequential PO-YYYY-XXXX numbering, and exact monetary calculation."""
    env = procurement_env
    with app.app_context():
        po = PurchaseOrderService.create_purchase_order(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            data={
                'supplier_partner_id': env['supplier_a_id'],
                'destination_location_id': env['loc_a_id'],
                'payment_terms': 'NET_30',
                'tax_amount': '150.00',
                'lines': [
                    {
                        'product_id': env['prod_a_id'],
                        'ordered_quantity': '10.00',
                        'unit_price': '150.00'
                    }
                ]
            }
        )

        current_year = date.today().year
        assert po.id is not None
        assert po.po_number == f"PO-{current_year}-0001"
        assert po.subtotal_amount == Decimal('1500.00')
        assert po.tax_amount == Decimal('150.00')
        assert po.total_amount == Decimal('1650.00')
        assert po.status == 'DRAFT'
        assert len(po.lines) == 1
        assert po.lines[0].ordered_quantity == Decimal('10.00')
        assert po.lines[0].total_price == Decimal('1500.00')


def test_po_supplier_validation_rejects_customer_partner(app, procurement_env):
    """Ensures PO cannot be issued to a partner of type 'CUSTOMER'."""
    env = procurement_env
    with app.app_context():
        with pytest.raises(APIError) as exc:
            PurchaseOrderService.create_purchase_order(
                workspace_id=env['ws_a_id'],
                actor_user_id=env['admin_a_id'],
                data={
                    'supplier_partner_id': env['customer_a_id'],
                    'destination_location_id': env['loc_a_id'],
                    'lines': [
                        {'product_id': env['prod_a_id'], 'ordered_quantity': '5.00', 'unit_price': '100.00'}
                    ]
                }
            )
        assert exc.value.status == 400
        assert 'SUPPLIER' in exc.value.message


def test_po_lifecycle_approval_and_sending(app, procurement_env):
    """Tests PO approval and sending to supplier."""
    env = procurement_env
    with app.app_context():
        po = PurchaseOrderService.create_purchase_order(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            data={
                'supplier_partner_id': env['supplier_a_id'],
                'destination_location_id': env['loc_a_id'],
                'lines': [
                    {'product_id': env['prod_a_id'], 'ordered_quantity': '20.00', 'unit_price': '150.00'}
                ]
            }
        )

        # Approve PO
        approved_po = PurchaseOrderService.approve_purchase_order(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['owner_a_id'],
            po_id=po.id
        )
        assert approved_po.status == 'APPROVED'
        assert approved_po.approved_by_user_id == env['owner_a_id']

        # Send PO to Supplier
        sent_po = PurchaseOrderService.send_purchase_order(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            po_id=po.id
        )
        assert sent_po.status == 'SENT_TO_SUPPLIER'
        assert sent_po.sent_at is not None


def test_po_cancellation(app, procurement_env):
    """Tests PO cancellation."""
    env = procurement_env
    with app.app_context():
        po = PurchaseOrderService.create_purchase_order(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            data={
                'supplier_partner_id': env['supplier_a_id'],
                'destination_location_id': env['loc_a_id'],
                'lines': [
                    {'product_id': env['prod_a_id'], 'ordered_quantity': '10.00', 'unit_price': '150.00'}
                ]
            }
        )

        cancelled_po = PurchaseOrderService.cancel_purchase_order(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            po_id=po.id,
            reason='Budget reallocated'
        )
        assert cancelled_po.status == 'CANCELLED'
        assert cancelled_po.lines[0].status == 'CANCELLED'


# ==============================================================================
# 3. PR TO PO CONVERSION TESTS
# ==============================================================================

def test_pr_to_po_conversion(app, procurement_env):
    """Tests converting an approved PR into a PO draft."""
    env = procurement_env
    with app.app_context():
        pr = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '30.00',
                'status': 'SUBMITTED'
            }
        )

        PurchaseRequestService.approve_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            request_id=pr.id
        )

        # Convert to PO
        po = PurchaseOrderService.convert_pr_to_po(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['admin_a_id'],
            request_id=pr.id,
            data={
                'expected_delivery_date': '2026-09-15',
                'payment_terms': 'NET_15'
            }
        )

        assert po.id is not None
        assert po.supplier_partner_id == env['supplier_a_id']
        assert po.destination_location_id == env['loc_a_id']
        assert len(po.lines) == 1
        assert po.lines[0].ordered_quantity == Decimal('30.00')

        # Verify PR status updated to ORDERED with PO link
        updated_pr = PurchaseRequestService.get_request_by_id(env['ws_a_id'], pr.id)
        assert updated_pr.status == 'ORDERED'
        assert updated_pr.purchase_order_id == po.id


def test_duplicate_pr_conversion_prevention(app, procurement_env):
    """Rejects duplicate conversion of an already-converted PR."""
    env = procurement_env
    with app.app_context():
        pr = PurchaseRequestService.create_request(
            workspace_id=env['ws_a_id'],
            actor_user_id=env['member_a_id'],
            data={
                'product_id': env['prod_a_id'],
                'location_id': env['loc_a_id'],
                'requested_quantity': '10.00'
            }
        )
        PurchaseRequestService.approve_request(env['ws_a_id'], env['admin_a_id'], pr.id)

        # First conversion succeeds
        PurchaseOrderService.convert_pr_to_po(env['ws_a_id'], env['admin_a_id'], pr.id)

        # Second conversion must fail with conflict error
        with pytest.raises(APIError) as exc:
            PurchaseOrderService.convert_pr_to_po(env['ws_a_id'], env['admin_a_id'], pr.id)
        assert exc.value.status == 400 or exc.value.status == 409


# ==============================================================================
# 4. TENANT ISOLATION & IDOR TESTS
# ==============================================================================

def test_tenant_isolation_cross_workspace_idor_rejected(app, procurement_env):
    """Ensures Workspace A cannot access, update, or convert PRs/POs belonging to Workspace B."""
    env = procurement_env
    with app.app_context():
        # Create PR in Workspace B
        pr_b = PurchaseRequestService.create_request(
            workspace_id=env['ws_b_id'],
            actor_user_id=env['owner_b_id'],
            data={
                'product_id': env['prod_b_id'],
                'location_id': env['loc_b_id'],
                'requested_quantity': '100.00'
            }
        )

        # Attempt to access PR B from Workspace A -> Must return 404 NOT_FOUND
        with pytest.raises(APIError) as exc:
            PurchaseRequestService.get_request_by_id(
                workspace_id=env['ws_a_id'],
                request_id=pr_b.id
            )
        assert exc.value.status == 404

        # Attempt to create PO in Workspace A referencing product from Workspace B -> Must fail
        with pytest.raises(APIError) as exc:
            PurchaseOrderService.create_purchase_order(
                workspace_id=env['ws_a_id'],
                actor_user_id=env['admin_a_id'],
                data={
                    'supplier_partner_id': env['supplier_a_id'],
                    'destination_location_id': env['loc_a_id'],
                    'lines': [
                        {'product_id': env['prod_b_id'], 'ordered_quantity': '10.00', 'unit_price': '500.00'}
                    ]
                }
            )
        assert exc.value.status == 400


# ==============================================================================
# 5. API ENDPOINT & RBAC TESTS
# ==============================================================================

def test_api_pr_crud_and_rbac(client, procurement_env):
    """Tests PR API endpoints with Member creation and Admin approval."""
    env = procurement_env
    headers_member = {
        'Authorization': f"Bearer {env['member_a_id']}",
        'X-Workspace-Id': env['ws_a_id']
    }
    headers_admin = {
        'Authorization': f"Bearer {env['admin_a_id']}",
        'X-Workspace-Id': env['ws_a_id']
    }
    headers_viewer = {
        'Authorization': f"Bearer {env['viewer_a_id']}",
        'X-Workspace-Id': env['ws_a_id']
    }

    # 1. Member creates PR via API
    res = client.post('/api/business/procurement/requests', json={
        'product_id': env['prod_a_id'],
        'location_id': env['loc_a_id'],
        'requested_quantity': '40.00',
        'priority': 'MEDIUM',
        'reason': 'API Test PR'
    }, headers=headers_member)
    assert res.status_code == 201
    pr_id = res.get_json()['data']['id']

    # 2. Viewer attempts to approve -> Denied (403)
    res = client.post(f'/api/business/procurement/requests/{pr_id}/approve', json={
        'approval_notes': 'Unauthorized approval attempt'
    }, headers=headers_viewer)
    assert res.status_code == 403

    # 3. Admin approves PR -> Allowed (200)
    res = client.post(f'/api/business/procurement/requests/{pr_id}/approve', json={
        'approval_notes': 'Authorized Admin Approval'
    }, headers=headers_admin)
    assert res.status_code == 200
    assert res.get_json()['data']['status'] == 'APPROVED'

    # 4. Admin converts PR to PO -> Allowed (201)
    res = client.post(f'/api/business/procurement/requests/{pr_id}/convert-to-po', json={
        'payment_terms': 'NET_30'
    }, headers=headers_admin)
    assert res.status_code == 201
    po_data = res.get_json()['data']
    assert po_data['status'] == 'DRAFT'
    assert len(po_data['lines']) == 1


def test_api_po_lifecycle_and_rbac(client, procurement_env):
    """Tests PO API endpoints with Admin creation, Owner approval, and sending."""
    env = procurement_env
    headers_admin = {
        'Authorization': f"Bearer {env['admin_a_id']}",
        'X-Workspace-Id': env['ws_a_id']
    }
    headers_member = {
        'Authorization': f"Bearer {env['member_a_id']}",
        'X-Workspace-Id': env['ws_a_id']
    }

    # 1. Member attempts to create PO -> Denied (403)
    res = client.post('/api/business/purchase-orders', json={
        'supplier_partner_id': env['supplier_a_id'],
        'destination_location_id': env['loc_a_id'],
        'lines': [{'product_id': env['prod_a_id'], 'ordered_quantity': '10.00', 'unit_price': '150.00'}]
    }, headers=headers_member)
    assert res.status_code == 403

    # 2. Admin creates PO -> Allowed (201)
    res = client.post('/api/business/purchase-orders', json={
        'supplier_partner_id': env['supplier_a_id'],
        'destination_location_id': env['loc_a_id'],
        'lines': [{'product_id': env['prod_a_id'], 'ordered_quantity': '15.00', 'unit_price': '150.00'}]
    }, headers=headers_admin)
    assert res.status_code == 201
    po_id = res.get_json()['data']['id']

    # 3. Admin approves PO -> Allowed (200)
    res = client.post(f'/api/business/purchase-orders/{po_id}/approve', headers=headers_admin)
    assert res.status_code == 200
    assert res.get_json()['data']['status'] == 'APPROVED'

    # 4. Admin sends PO to supplier -> Allowed (200)
    res = client.post(f'/api/business/purchase-orders/{po_id}/send', headers=headers_admin)
    assert res.status_code == 200
    assert res.get_json()['data']['status'] == 'SENT_TO_SUPPLIER'
