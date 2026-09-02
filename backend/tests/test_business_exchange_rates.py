"""
DeadlineOS Business OS — Phase C3.1 Exchange Rates & Multi-Currency Tests
========================================================================
Tests exact Decimal precision, 7-day historical lookback, provenance tracking,
multi-currency purchase order integration, RBAC enforcement, and tenant isolation.
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
    BusinessExchangeRate,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    CommercialPartner,
    BusinessLocation,
    BusinessProduct,
    AuditEvent
)
from services.business.exchange_rate_service import ExchangeRateService
from services.business.purchase_order_service import PurchaseOrderService
from utils.errors import APIError


@pytest.fixture
def fx_env(app):
    """Sets up two multi-tenant workspaces, users with different roles, products, and locations."""
    with app.app_context():
        # Create Users
        owner = User(id=str(uuid.uuid4()), email=f"owner_{uuid.uuid4().hex[:6]}@test.com", full_name="Test User")
        admin = User(id=str(uuid.uuid4()), email=f"admin_{uuid.uuid4().hex[:6]}@test.com", full_name="Test User")
        accountant = User(id=str(uuid.uuid4()), email=f"acct_{uuid.uuid4().hex[:6]}@test.com", full_name="Test User")
        member = User(id=str(uuid.uuid4()), email=f"mem_{uuid.uuid4().hex[:6]}@test.com", full_name="Test User")
        viewer = User(id=str(uuid.uuid4()), email=f"view_{uuid.uuid4().hex[:6]}@test.com", full_name="Test User")
        db.session.add_all([owner, admin, accountant, member, viewer])
        db.session.commit()

        # Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name="Global Logistics Corp A", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name="Foreign Enterprise B", base_currency="USD")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # Memberships for Workspace A
        m_owner = WorkspaceMember(workspace_id=ws_a.id, user_id=owner.id, role="OWNER", status="ACTIVE")
        m_admin = WorkspaceMember(workspace_id=ws_a.id, user_id=admin.id, role="ADMIN", status="ACTIVE")
        m_acct = WorkspaceMember(workspace_id=ws_a.id, user_id=accountant.id, role="ACCOUNTANT", status="ACTIVE")
        m_mem = WorkspaceMember(workspace_id=ws_a.id, user_id=member.id, role="MEMBER", status="ACTIVE")
        m_view = WorkspaceMember(workspace_id=ws_a.id, user_id=viewer.id, role="VIEWER", status="ACTIVE")

        # Membership for Workspace B (Owner only)
        m_owner_b = WorkspaceMember(workspace_id=ws_b.id, user_id=owner.id, role="OWNER", status="ACTIVE")
        db.session.add_all([m_owner, m_admin, m_acct, m_mem, m_view, m_owner_b])
        db.session.commit()

        # Supplier in Workspace A with USD currency
        supplier = CommercialPartner(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            partner_type="SUPPLIER",
            name="Shenzhen Electronics Ltd",
            default_currency="USD"
        )
        # Location and Product in Workspace A
        loc = BusinessLocation(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name="Main Import Warehouse",
            location_type="WAREHOUSE"
        )
        prod = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku=f"CHIP-{uuid.uuid4().hex[:4].upper()}",
            name="Microcontroller IC 990",
            cost_price=Decimal("45.00"),
            currency="USD"
        )
        db.session.add_all([supplier, loc, prod])
        db.session.commit()

        yield {
            'ws_a': ws_a,
            'ws_b': ws_b,
            'owner': owner,
            'admin': admin,
            'accountant': accountant,
            'member': member,
            'viewer': viewer,
            'supplier': supplier,
            'location': loc,
            'product': prod
        }


def test_record_and_get_exchange_rate(app, fx_env):
    """Verifies recording an exchange rate with exact Decimal precision and provenance."""
    with app.app_context():
        ws = fx_env['ws_a']
        user = fx_env['admin']

        # Record USD to INR rate
        fx = ExchangeRateService.record_exchange_rate(
            workspace_id=ws.id,
            actor_user_id=user.id,
            data={
                'from_currency': 'USD',
                'to_currency': 'INR',
                'rate': '84.500000',
                'rate_source': 'CENTRAL_BANK',
                'notes': 'Official RBI customs notification'
            }
        )

        assert fx.id is not None
        assert fx.from_currency == 'USD'
        assert fx.to_currency == 'INR'
        assert fx.rate == Decimal('84.500000')
        assert fx.rate_source == 'CENTRAL_BANK'

        # Retrieve rate
        retrieved_rate = ExchangeRateService.get_exchange_rate(ws.id, 'USD', 'INR')
        assert retrieved_rate == Decimal('84.500000')

        # Convert amount
        conv = ExchangeRateService.convert_amount(ws.id, Decimal('1000.00'), 'USD', 'INR')
        assert conv['converted_amount'] == '84500.00'
        assert conv['exchange_rate'] == '84.500000'


def test_7_day_lookback_window(app, fx_env):
    """Verifies that the exchange rate service falls back within a 7-day window when exact date is missing."""
    with app.app_context():
        ws = fx_env['ws_a']
        user = fx_env['admin']
        base_date = date(2026, 8, 10)

        # Record rate on 2026-08-10
        ExchangeRateService.record_exchange_rate(
            workspace_id=ws.id,
            actor_user_id=user.id,
            data={
                'from_currency': 'EUR',
                'to_currency': 'INR',
                'rate': '92.250000',
                'effective_date': '2026-08-10',
                'rate_source': 'CUSTOMS_RATE'
            }
        )

        # Lookup on 2026-08-14 (4 days later) -> should return 92.250000 via lookback
        rate_lookback = ExchangeRateService.get_exchange_rate(ws.id, 'EUR', 'INR', effective_date=date(2026, 8, 14))
        assert rate_lookback == Decimal('92.250000')

        # Lookup on 2026-08-25 (15 days later) -> exceeds 7 days, should raise APIError
        with pytest.raises(APIError) as exc_info:
            ExchangeRateService.get_exchange_rate(ws.id, 'EUR', 'INR', effective_date=date(2026, 8, 25))
        assert exc_info.value.code == 'MISSING_EXCHANGE_RATE'


def test_inverted_pair_resolution(app, fx_env):
    """Verifies that an inverted rate is deterministically calculated if only the direct pair exists."""
    with app.app_context():
        ws = fx_env['ws_a']
        user = fx_env['admin']

        # Record USD to INR = 80.000000
        ExchangeRateService.record_exchange_rate(
            workspace_id=ws.id,
            actor_user_id=user.id,
            data={
                'from_currency': 'USD',
                'to_currency': 'INR',
                'rate': '80.000000',
                'rate_source': 'MANUAL_OVERRIDE'
            }
        )

        # Request INR to USD
        inv_rate = ExchangeRateService.get_exchange_rate(ws.id, 'INR', 'USD')
        # 1 / 80 = 0.012500
        assert inv_rate == Decimal('0.012500')


def test_foreign_currency_purchase_order_creation(app, fx_env):
    """Verifies that a PO created in a foreign currency locks the exchange rate and base_currency_total."""
    with app.app_context():
        ws = fx_env['ws_a']
        user = fx_env['owner']
        supplier = fx_env['supplier']
        loc = fx_env['location']
        prod = fx_env['product']

        # Record exchange rate: 1 USD = 84.000000 INR
        ExchangeRateService.record_exchange_rate(
            workspace_id=ws.id,
            actor_user_id=user.id,
            data={'from_currency': 'USD', 'to_currency': 'INR', 'rate': '84.000000'}
        )

        # Create PO in USD: 10 units at $45.00 = $450.00 USD
        po = PurchaseOrderService.create_purchase_order(
            workspace_id=ws.id,
            actor_user_id=user.id,
            data={
                'supplier_partner_id': supplier.id,
                'destination_location_id': loc.id,
                'currency': 'USD',
                'lines': [
                    {'product_id': prod.id, 'ordered_quantity': '10.00', 'unit_price': '45.00'}
                ]
            }
        )

        assert po.currency == 'USD'
        assert po.total_amount == Decimal('450.00')
        assert po.exchange_rate == Decimal('84.000000')
        # base_currency_total = 450.00 * 84.000000 = 37,800.00 INR
        assert po.base_currency_total == Decimal('37800.00')

        # Update current FX rate to 88.000000
        ExchangeRateService.record_exchange_rate(
            workspace_id=ws.id,
            actor_user_id=user.id,
            data={'from_currency': 'USD', 'to_currency': 'INR', 'rate': '88.000000'}
        )

        # Reload PO from DB -> verify locked rate and base total did NOT mutate
        db.session.refresh(po)
        assert po.exchange_rate == Decimal('84.000000')
        assert po.base_currency_total == Decimal('37800.00')


def test_tenant_isolation_exchange_rates(app, fx_env):
    """Verifies that exchange rates recorded in Workspace A are completely isolated from Workspace B."""
    with app.app_context():
        ws_a = fx_env['ws_a']
        ws_b = fx_env['ws_b']
        user = fx_env['owner']

        # Record rate in Workspace A
        ExchangeRateService.record_exchange_rate(
            workspace_id=ws_a.id,
            actor_user_id=user.id,
            data={'from_currency': 'GBP', 'to_currency': 'INR', 'rate': '110.500000'}
        )

        # Lookup in Workspace A -> succeeds
        rate_a = ExchangeRateService.get_exchange_rate(ws_a.id, 'GBP', 'INR')
        assert rate_a == Decimal('110.500000')

        # Lookup in Workspace B -> fails (isolated)
        with pytest.raises(APIError) as exc_info:
            ExchangeRateService.get_exchange_rate(ws_b.id, 'GBP', 'INR')
        assert exc_info.value.code == 'MISSING_EXCHANGE_RATE'

        # List rates in Workspace B -> returns empty
        rates_b = ExchangeRateService.list_exchange_rates(ws_b.id)
        assert len(rates_b) == 0


def test_rbac_exchange_rates_matrix(app, fx_env):
    """Verifies that OWNER, ADMIN, ACCOUNTANT can record rates, while MEMBER and VIEWER are forbidden."""
    from middleware.business_context import ROLE_PERMISSIONS

    # Check 5-tier RBAC matrix
    assert 'currency:write' in ROLE_PERMISSIONS['OWNER']
    assert 'currency:write' in ROLE_PERMISSIONS['ADMIN']
    assert 'currency:write' in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'currency:write' not in ROLE_PERMISSIONS['MEMBER']
    assert 'currency:write' not in ROLE_PERMISSIONS['VIEWER']

    assert 'currency:read' in ROLE_PERMISSIONS['OWNER']
    assert 'currency:read' in ROLE_PERMISSIONS['ADMIN']
    assert 'currency:read' in ROLE_PERMISSIONS['ACCOUNTANT']
    assert 'currency:read' in ROLE_PERMISSIONS['MEMBER']
    assert 'currency:read' in ROLE_PERMISSIONS['VIEWER']


def test_api_supported_currencies(app, fx_env):
    """Verifies the supported currencies listing API."""
    with app.app_context():
        currencies = ExchangeRateService.SUPPORTED_CURRENCIES
        assert 'USD' in currencies
        assert 'INR' in currencies
        assert 'EUR' in currencies
        assert 'GBP' in currencies
        assert 'JPY' in currencies
        assert 'CNY' in currencies
