"""
DeadlineOS Business OS — C3.4 Landed Cost Allocation Engine Tests
=================================================================
Unit and integration tests for landed cost vouchers, itemized costs,
multi-currency FX intake, proportional value/quantity allocation,
deterministic residual-cent rule, exact reconciliation, immutability,
reversals, 5-tier RBAC, and multi-tenant isolation.
"""

import uuid
import pytest
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    BusinessProduct,
    BusinessLocation,
    CommercialPartner,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessGoodsReceipt,
    BusinessGoodsReceiptLine,
    BusinessStockMovement,
    BusinessBatch,
    BusinessStockMovementBatch,
    BusinessSerialNumber,
    BusinessStockMovementSerial,
    BusinessLandedCostVoucher,
    BusinessLandedCostVoucherItem,
    BusinessLandedCostAllocation,
    AuditEvent
)
from services.business.landed_cost_service import LandedCostService
from services.business.exchange_rate_service import ExchangeRateService
from services.business.goods_receipt_service import GoodsReceiptService
from middleware.business_context import ROLE_PERMISSIONS
from utils.errors import APIError


@pytest.fixture
def fx_landed_cost_env(app):
    """Sets up isolated workspaces, users, procurement and receiving fixtures."""
    with app.app_context():
        # Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name="Global Logistics Corp A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="Global Logistics Corp B", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # Users
        u_owner = User(id=str(uuid.uuid4()), email="owner@landed.test", full_name="Landed Owner")
        u_admin = User(id=str(uuid.uuid4()), email="admin@landed.test", full_name="Landed Admin")
        u_acct = User(id=str(uuid.uuid4()), email="acct@landed.test", full_name="Landed Accountant")
        u_member = User(id=str(uuid.uuid4()), email="member@landed.test", full_name="Landed Member")
        u_viewer = User(id=str(uuid.uuid4()), email="viewer@landed.test", full_name="Landed Viewer")
        db.session.add_all([u_owner, u_admin, u_acct, u_member, u_viewer])
        db.session.commit()

        for u, role in [
            (u_owner, 'OWNER'),
            (u_admin, 'ADMIN'),
            (u_acct, 'ACCOUNTANT'),
            (u_member, 'MEMBER'),
            (u_viewer, 'VIEWER')
        ]:
            db.session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=u.id, role=role, status='ACTIVE'))
        db.session.commit()

        # Location & Supplier in WS A
        loc_a = BusinessLocation(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Port Klang Container Yard",
            location_type="WAREHOUSE"
        )
        supp_a = CommercialPartner(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            partner_type="SUPPLIER",
            name="Pacific Maritime Freight Ltd"
        )
        # Products
        prod_1 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku="TURBINE-A1",
            name="Industrial Gas Turbine",
            unit="UNIT",
            cost_price=Decimal("100000.00"),
            selling_price=Decimal("180000.00")
        )
        prod_2 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku="VALVE-B2",
            name="Cryogenic Relief Valve",
            unit="UNIT",
            cost_price=Decimal("20000.00"),
            selling_price=Decimal("35000.00")
        )
        prod_3 = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku="SEAL-C3",
            name="High Pressure Seal Ring",
            unit="UNIT",
            cost_price=Decimal("5000.00"),
            selling_price=Decimal("9000.00")
        )
        db.session.add_all([loc_a, supp_a, prod_1, prod_2, prod_3])
        db.session.commit()

        # Purchase Order
        po = BusinessPurchaseOrder(
            workspace_id=ws_a.id,
            po_number="PO-IMPORT-2026-01",
            supplier_partner_id=supp_a.id,
            destination_location_id=loc_a.id,
            currency="INR",
            status="APPROVED",
            total_amount=Decimal("350000.00"),
            base_currency_total=Decimal("350000.00")
        )
        db.session.add(po)
        db.session.flush()

        pol_1 = BusinessPurchaseOrderLine(
            purchase_order_id=po.id,
            product_id=prod_1.id,
            ordered_quantity=Decimal("2.00"),
            unit_price=Decimal("100000.00"),
            total_price=Decimal("200000.00"),
            status="ORDERED"
        )
        pol_2 = BusinessPurchaseOrderLine(
            purchase_order_id=po.id,
            product_id=prod_2.id,
            ordered_quantity=Decimal("5.00"),
            unit_price=Decimal("20000.00"),
            total_price=Decimal("100000.00"),
            status="ORDERED"
        )
        pol_3 = BusinessPurchaseOrderLine(
            purchase_order_id=po.id,
            product_id=prod_3.id,
            ordered_quantity=Decimal("10.00"),
            unit_price=Decimal("5000.00"),
            total_price=Decimal("50000.00"),
            status="ORDERED"
        )
        db.session.add_all([pol_1, pol_2, pol_3])
        db.session.commit()

        # Goods Receipt Note (GRN) receiving all lines
        grn = GoodsReceiptService.create_goods_receipt(
            workspace_id=ws_a.id,
            actor_user_id=u_owner.id,
            data={
                'purchase_order_id': po.id,
                'lines': [
                    {'purchase_order_line_id': pol_1.id, 'received_quantity': '2.00', 'accepted_quantity': '2.00', 'rejected_quantity': '0.00'},
                    {'purchase_order_line_id': pol_2.id, 'received_quantity': '5.00', 'accepted_quantity': '5.00', 'rejected_quantity': '0.00'},
                    {'purchase_order_line_id': pol_3.id, 'received_quantity': '10.00', 'accepted_quantity': '10.00', 'rejected_quantity': '0.00'},
                ]
            }
        )
        db.session.commit()

        yield {
            'ws_a': ws_a,
            'ws_b': ws_b,
            'owner': u_owner,
            'admin': u_admin,
            'acct': u_acct,
            'member': u_member,
            'viewer': u_viewer,
            'po': po,
            'grn': grn,
            'prod_1': prod_1,
            'prod_2': prod_2,
            'prod_3': prod_3,
        }


def test_voucher_creation_and_defaults(app, fx_landed_cost_env):
    """Verifies creating a draft voucher with defaults, currency, and audit event."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={
            'goods_receipt_id': env['grn'].id,
            'reference_number': 'BL-2026-KUA-0091',
            'allocation_basis': 'VALUE',
            'notes': 'Import logistics for maritime shipment'
        }
    )
    db.session.commit()

    assert voucher.status == 'DRAFT'
    assert voucher.voucher_number.startswith('LCV-')
    assert voucher.currency == 'INR'
    assert voucher.base_currency == 'INR'
    assert voucher.exchange_rate == Decimal('1.000000')
    assert voucher.total_cost_base_currency == Decimal('0.00')

    # Verify audit event
    audit = AuditEvent.query.filter_by(workspace_id=env['ws_a'].id, entity_id=voucher.id, action='LANDED_COST_VOUCHER_CREATED').first()
    assert audit is not None


def test_cost_item_creation_and_recalculation(app, fx_landed_cost_env):
    """Verifies adding itemized expenditures recalculates voucher totals."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id}
    )

    item1 = LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={
            'cost_category': 'FREIGHT',
            'description': 'Ocean freight shipping',
            'amount': '45000.00'
        }
    )
    item2 = LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={
            'cost_category': 'CUSTOMS',
            'description': 'Port clearance & import duty',
            'amount': '15500.00'
        }
    )

    assert voucher.total_cost_base_currency == Decimal('60500.00')
    assert voucher.total_cost_source_currency == Decimal('60500.00')
    assert len(voucher.items) == 2

    # Remove item1 and verify recalculation
    LandedCostService.remove_cost_item(env['ws_a'].id, voucher.id, item1.id, env['owner'].id)
    assert voucher.total_cost_base_currency == Decimal('15500.00')


def test_zero_or_negative_cost_item_rejection(app, fx_landed_cost_env):
    """Verifies that non-positive cost amounts are strictly rejected."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id}
    )

    with pytest.raises(APIError) as exc:
        LandedCostService.add_cost_item(
            workspace_id=env['ws_a'].id,
            voucher_id=voucher.id,
            actor_user_id=env['owner'].id,
            data={'cost_category': 'INSURANCE', 'description': 'Transit insurance', 'amount': '-500.00'}
        )
    assert exc.value.code == 'INVALID_AMOUNT'

    with pytest.raises(APIError) as exc:
        LandedCostService.add_cost_item(
            workspace_id=env['ws_a'].id,
            voucher_id=voucher.id,
            actor_user_id=env['owner'].id,
            data={'cost_category': 'INSURANCE', 'description': 'Transit insurance', 'amount': '0.00'}
        )
    assert exc.value.code == 'INVALID_AMOUNT'


def test_proportional_value_allocation(app, fx_landed_cost_env):
    """Verifies proportional value allocation across 3 lines."""
    env = fx_landed_cost_env
    # Total PO/GRN value:
    # Line 1: 2 * 100,000 = 200,000 (57.142857%)
    # Line 2: 5 * 20,000 = 100,000  (28.571429%)
    # Line 3: 10 * 5,000 = 50,000   (14.285714%)
    # Total basis = 350,000.00
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id, 'allocation_basis': 'VALUE'}
    )
    LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={'cost_category': 'FREIGHT', 'description': 'Ocean freight', 'amount': '35000.00'}
    )

    allocated_voucher = LandedCostService.execute_allocation(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        allocation_basis='VALUE'
    )

    assert allocated_voucher.status == 'ALLOCATED'
    allocations = allocated_voucher.allocations
    assert len(allocations) == 3

    # Exact expected shares for 35,000 total:
    # Line 1: 35,000 * 200,000 / 350,000 = 20,000.00
    # Line 2: 35,000 * 100,000 / 350,000 = 10,000.00
    # Line 3: 35,000 * 50,000 / 350,000 = 5,000.00
    alloc_map = {a.product_id: a for a in allocations}
    assert alloc_map[env['prod_1'].id].allocated_cost_base_currency == Decimal('20000.00')
    assert alloc_map[env['prod_2'].id].allocated_cost_base_currency == Decimal('10000.00')
    assert alloc_map[env['prod_3'].id].allocated_cost_base_currency == Decimal('5000.00')

    # Landed cost per unit
    assert alloc_map[env['prod_1'].id].landed_cost_per_unit == Decimal('10000.0000')  # 20,000 / 2
    assert alloc_map[env['prod_2'].id].landed_cost_per_unit == Decimal('2000.0000')   # 10,000 / 5
    assert alloc_map[env['prod_3'].id].landed_cost_per_unit == Decimal('500.0000')    # 5,000 / 10


def test_proportional_quantity_allocation(app, fx_landed_cost_env):
    """Verifies proportional quantity allocation across 3 lines."""
    env = fx_landed_cost_env
    # Quantities: Line 1 = 2, Line 2 = 5, Line 3 = 10. Total Qty = 17.
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id, 'allocation_basis': 'QUANTITY'}
    )
    # Cost = 17,000.00 (exactly 1,000 per unit)
    LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={'cost_category': 'HANDLING', 'description': 'Container handling', 'amount': '17000.00'}
    )

    allocated_voucher = LandedCostService.execute_allocation(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        allocation_basis='QUANTITY'
    )

    alloc_map = {a.product_id: a for a in allocated_voucher.allocations}
    assert alloc_map[env['prod_1'].id].allocated_cost_base_currency == Decimal('2000.00')
    assert alloc_map[env['prod_2'].id].allocated_cost_base_currency == Decimal('5000.00')
    assert alloc_map[env['prod_3'].id].allocated_cost_base_currency == Decimal('10000.00')


def test_deterministic_residual_cent_rule(app, fx_landed_cost_env):
    """Verifies that residual cents are assigned deterministically to the largest-weight line."""
    env = fx_landed_cost_env
    # Total value = 350,000.
    # Line 1: 200,000 (weight ~57.14%)
    # Line 2: 100,000 (weight ~28.57%)
    # Line 3: 50,000 (weight ~14.29%)
    # Let total cost = 100.00
    # Exact shares:
    # Line 1: 100 * 200/350 = 57.142857... -> rounded = 57.14
    # Line 2: 100 * 100/350 = 28.571428... -> rounded = 28.57
    # Line 3: 100 * 50/350 = 14.285714...  -> rounded = 14.29
    # Sum of rounded = 57.14 + 28.57 + 14.29 = 100.00 (residual 0.00)
    # Let's use cost = 100.01:
    # Line 1: 100.01 * 200/350 = 57.14857... -> rounded = 57.15
    # Line 2: 100.01 * 100/350 = 28.57428... -> rounded = 28.57
    # Line 3: 100.01 * 50/350 = 14.28714...  -> rounded = 14.29
    # Sum of rounded = 57.15 + 28.57 + 14.29 = 100.01.
    # Let's test an amount producing a non-zero residual: e.g. cost = 10.00
    # Line 1: 10 * 200/350 = 5.71428... -> 5.71
    # Line 2: 10 * 100/350 = 2.85714... -> 2.86
    # Line 3: 10 * 50/350 = 1.42857...  -> 1.43
    # Sum = 5.71 + 2.86 + 1.43 = 10.00.
    # Let's test cost = 0.01:
    # Line 1: 0.01 * 200/350 = 0.00571 -> 0.01
    # Line 2: 0.01 * 100/350 = 0.00285 -> 0.00
    # Line 3: 0.01 * 50/350 = 0.00142 -> 0.00
    # Sum = 0.01.
    # What about cost = 0.02?
    # Line 1: 0.02 * 200/350 = 0.0114 -> 0.01
    # Line 2: 0.02 * 100/350 = 0.0057 -> 0.01
    # Line 3: 0.02 * 50/350 = 0.0028 -> 0.00
    # Sum = 0.02.
    # What about cost = 0.05?
    # Line 1: 0.05 * 200/350 = 0.02857 -> 0.03
    # Line 2: 0.05 * 100/350 = 0.01428 -> 0.01
    # Line 3: 0.05 * 50/350 = 0.00714 -> 0.01
    # Sum = 0.03 + 0.01 + 0.01 = 0.05.
    # Let's test lines with tied weights: 2 lines of 50 each, total cost 0.01:
    lines_tied = [
        {'id': 'line-A', 'product_id': 'prod-A', 'accepted_quantity': Decimal('1.00'), 'line_base_value': Decimal('50.00')},
        {'id': 'line-B', 'product_id': 'prod-B', 'accepted_quantity': Decimal('1.00'), 'line_base_value': Decimal('50.00')},
    ]
    # Total cost 0.01:
    # Line A: 0.01 * 50/100 = 0.005 -> 0.01
    # Line B: 0.01 * 50/100 = 0.005 -> 0.01
    # Sum rounded = 0.02. Residual = 0.01 - 0.02 = -0.01.
    # Residual must be applied to largest weight, lowest index -> line-A (index 0).
    # Line A becomes 0.01 + (-0.01) = 0.00. Line B remains 0.01.
    # Total = 0.01.
    res = LandedCostService.calculate_allocation(Decimal('0.01'), lines_tied, 'VALUE')
    assert sum(r['allocated_cost_base_currency'] for r in res) == Decimal('0.01')
    assert res[0]['allocated_cost_base_currency'] == Decimal('0.00')
    assert res[1]['allocated_cost_base_currency'] == Decimal('0.01')


def test_exact_total_reconciliation(app, fx_landed_cost_env):
    """Verifies that across arbitrary fractional allocations, sum equals total cost exactly."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id, 'allocation_basis': 'VALUE'}
    )
    # Prime number cost amount to induce recurring decimals: 33333.33
    LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={'cost_category': 'FREIGHT', 'description': 'Shipping', 'amount': '33333.33'}
    )

    allocated_voucher = LandedCostService.execute_allocation(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id
    )

    total_allocated = sum(a.allocated_cost_base_currency for a in allocated_voucher.allocations)
    assert total_allocated == Decimal('33333.33')


def test_foreign_currency_cost_conversion(app, fx_landed_cost_env):
    """Verifies itemized cost in USD converts to INR base currency via exchange rate."""
    env = fx_landed_cost_env
    # Record exchange rate: 1 USD = 85.500000 INR
    ExchangeRateService.record_exchange_rate(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={
            'from_currency': 'USD',
            'to_currency': 'INR',
            'rate': '85.500000',
            'effective_date': date.today().isoformat(),
            'rate_source': 'CENTRAL_BANK'
        }
    )

    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id, 'currency': 'INR'}
    )
    # Add $1,000 USD international brokerage
    item = LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={
            'cost_category': 'BROKERAGE',
            'description': 'US Customs broker fee',
            'amount': '1000.00',
            'currency': 'USD'
        }
    )

    assert item.currency == 'USD'
    assert item.amount == Decimal('1000.00')
    assert item.exchange_rate == Decimal('85.500000')
    assert item.base_currency_amount == Decimal('85500.00')
    assert voucher.total_cost_base_currency == Decimal('85500.00')


def test_missing_exchange_rate_rejection(app, fx_landed_cost_env):
    """Verifies that adding a foreign currency cost with no exchange rate fails safely."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id}
    )

    # EUR rate has not been recorded
    with pytest.raises(APIError) as exc:
        LandedCostService.add_cost_item(
            workspace_id=env['ws_a'].id,
            voucher_id=voucher.id,
            actor_user_id=env['owner'].id,
            data={
                'cost_category': 'FREIGHT',
                'description': 'Rotterdam port handling',
                'amount': '500.00',
                'currency': 'EUR'
            }
        )
    assert exc.value.code == 'MISSING_EXCHANGE_RATE'


def test_voucher_immutability_after_approval(app, fx_landed_cost_env):
    """Verifies that approved vouchers cannot be edited, re-allocated, or approved again."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id}
    )
    LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={'cost_category': 'FREIGHT', 'description': 'Freight', 'amount': '10000.00'}
    )
    LandedCostService.execute_allocation(env['ws_a'].id, voucher.id, env['owner'].id)

    # Approve voucher
    approved_voucher = LandedCostService.approve_voucher(env['ws_a'].id, voucher.id, env['owner'].id)
    assert approved_voucher.status == 'APPROVED'
    assert approved_voucher.approved_at is not None

    # Attempting to add an item to approved voucher must fail
    with pytest.raises(APIError) as exc:
        LandedCostService.add_cost_item(
            env['ws_a'].id, voucher.id, env['owner'].id,
            data={'cost_category': 'STORAGE', 'description': 'Late fee', 'amount': '200.00'}
        )
    assert exc.value.code == 'VOUCHER_IMMUTABLE'

    # Attempting to re-allocate approved voucher must fail
    with pytest.raises(APIError) as exc:
        LandedCostService.execute_allocation(env['ws_a'].id, voucher.id, env['owner'].id)
    assert exc.value.code == 'VOUCHER_IMMUTABLE'

    # Attempting double approval must fail
    with pytest.raises(APIError) as exc:
        LandedCostService.approve_voucher(env['ws_a'].id, voucher.id, env['owner'].id)
    assert exc.value.code == 'VOUCHER_ALREADY_APPROVED'


def test_reversal_lifecycle(app, fx_landed_cost_env):
    """Verifies reversing an approved voucher marks status REVERSED and audits."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id}
    )
    LandedCostService.add_cost_item(
        workspace_id=env['ws_a'].id,
        voucher_id=voucher.id,
        actor_user_id=env['owner'].id,
        data={'cost_category': 'FREIGHT', 'description': 'Freight', 'amount': '5000.00'}
    )
    LandedCostService.execute_allocation(env['ws_a'].id, voucher.id, env['owner'].id)
    LandedCostService.approve_voucher(env['ws_a'].id, voucher.id, env['owner'].id)

    # Reverse
    reversed_v = LandedCostService.reverse_voucher(
        env['ws_a'].id, voucher.id, env['owner'].id,
        reason="Carrier issued revised shipping invoice"
    )
    assert reversed_v.status == 'REVERSED'
    assert reversed_v.reversal_reason == "Carrier issued revised shipping invoice"

    # Audit event verified
    audit = AuditEvent.query.filter_by(workspace_id=env['ws_a'].id, entity_id=voucher.id, action='LANDED_COST_REVERSED').first()
    assert audit is not None


def test_tenant_isolation_landed_cost(app, fx_landed_cost_env):
    """Verifies that Workspace B cannot access or mutate Workspace A landed cost vouchers."""
    env = fx_landed_cost_env
    voucher = LandedCostService.create_voucher(
        workspace_id=env['ws_a'].id,
        actor_user_id=env['owner'].id,
        data={'goods_receipt_id': env['grn'].id}
    )

    # Workspace B attempts lookup
    with pytest.raises(APIError) as exc:
        LandedCostService.get_voucher(env['ws_b'].id, voucher.id)
    assert exc.value.code == 'VOUCHER_NOT_FOUND'

    # Workspace B attempts mutation
    with pytest.raises(APIError) as exc:
        LandedCostService.add_cost_item(
            env['ws_b'].id, voucher.id, env['owner'].id,
            data={'cost_category': 'OTHER', 'description': 'Hack', 'amount': '10.00'}
        )
    assert exc.value.code == 'VOUCHER_NOT_FOUND'


def test_rbac_landed_cost_matrix(app, fx_landed_cost_env):
    """Verifies 5-tier RBAC matrix permissions for landed cost."""
    # landed_cost:read across all 5 tiers
    assert 'landed_cost:read' in ROLE_PERMISSIONS['OWNER']
    assert 'landed_cost:read' in ROLE_PERMISSIONS['ADMIN']
    assert 'landed_cost:read' in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'landed_cost:read' in ROLE_PERMISSIONS['MEMBER']
    assert 'landed_cost:read' in ROLE_PERMISSIONS['VIEWER']

    # landed_cost:write and allocate for OWNER, ADMIN, ACCOUNTANT
    for role in ['OWNER', 'ADMIN', 'ACCOUNTANT']:
        assert 'landed_cost:write' in ROLE_PERMISSIONS[role]
        assert 'landed_cost:allocate' in ROLE_PERMISSIONS[role]

    # MEMBER and VIEWER denied write and allocate
    for role in ['MEMBER', 'VIEWER']:
        assert 'landed_cost:write' not in ROLE_PERMISSIONS[role]
        assert 'landed_cost:allocate' not in ROLE_PERMISSIONS[role]

    # landed_cost:approve and reverse restricted to OWNER, ADMIN
    assert 'landed_cost:approve' in ROLE_PERMISSIONS['OWNER']
    assert 'landed_cost:approve' in ROLE_PERMISSIONS['ADMIN']
    assert 'landed_cost:reverse' in ROLE_PERMISSIONS['OWNER']
    assert 'landed_cost:reverse' in ROLE_PERMISSIONS['ADMIN']

    assert 'landed_cost:approve' not in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'landed_cost:reverse' not in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'landed_cost:approve' not in ROLE_PERMISSIONS['MEMBER']
    assert 'landed_cost:approve' not in ROLE_PERMISSIONS['VIEWER']
