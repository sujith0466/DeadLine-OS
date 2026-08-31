"""
Tests for DeadlineOS Business OS — Phase B6 Intelligence, Planning & Decision Support
"""

import uuid
from decimal import Decimal
from datetime import date, timedelta
from database.db import db
from models.business import Workspace, WorkspaceMember, BusinessTransaction, Invoice, CommercialPartner, RecurringObligation, StagedExtraction
from services.business.intelligence_service import BusinessIntelligenceService


def setup_intelligence_test_data(app):
    with app.app_context():
        user_id = str(uuid.uuid4())
        today = date.today()

        ws = Workspace(
            name="Intelligence Corp",
            legal_name="Intelligence Corp Pvt Ltd",
            base_currency="INR",
            timezone="Asia/Kolkata"
        )
        db.session.add(ws)
        db.session.commit()

        member = WorkspaceMember(
            workspace_id=ws.id,
            user_id=user_id,
            role="OWNER",
            status="ACTIVE"
        )
        db.session.add(member)

        # 1. Transactions for historical trends & confirmed cash
        t1 = BusinessTransaction(
            workspace_id=ws.id,
            transaction_type="INCOME",
            amount=Decimal("150000.00"),
            currency="INR",
            status="CONFIRMED",
            transaction_date=today - timedelta(days=45),
            created_by_user_id=user_id
        )
        t2 = BusinessTransaction(
            workspace_id=ws.id,
            transaction_type="EXPENSE",
            amount=Decimal("50000.00"),
            currency="INR",
            status="CONFIRMED",
            transaction_date=today - timedelta(days=40),
            created_by_user_id=user_id
        )
        t3 = BusinessTransaction(
            workspace_id=ws.id,
            transaction_type="INCOME",
            amount=Decimal("100000.00"),
            currency="INR",
            status="CONFIRMED",
            transaction_date=today - timedelta(days=10),
            created_by_user_id=user_id
        )
        t4 = BusinessTransaction(
            workspace_id=ws.id,
            transaction_type="EXPENSE",
            amount=Decimal("40000.00"),
            currency="INR",
            status="CONFIRMED",
            transaction_date=today - timedelta(days=5),
            created_by_user_id=user_id
        )
        db.session.add_all([t1, t2, t3, t4])

        # 2. Partner & Receivables
        partner = CommercialPartner(
            workspace_id=ws.id,
            name="Key Client",
            partner_type="CUSTOMER"
        )
        db.session.add(partner)
        db.session.commit()

        inv1 = Invoice(
            workspace_id=ws.id,
            partner_id=partner.id,
            invoice_number="INV-2026-001",
            invoice_type="RECEIVABLE",
            total_amount=Decimal("80000.00"),
            balance_due=Decimal("80000.00"),
            issue_date=today - timedelta(days=15),
            due_date=today + timedelta(days=14),
            status="ISSUED",
            currency="INR",
            created_by_user_id=user_id
        )
        inv2 = Invoice(
            workspace_id=ws.id,
            partner_id=partner.id,
            invoice_number="INV-2026-002",
            invoice_type="RECEIVABLE",
            total_amount=Decimal("30000.00"),
            balance_due=Decimal("30000.00"),
            issue_date=today - timedelta(days=40),
            due_date=today - timedelta(days=10),
            status="OVERDUE",
            currency="INR",
            created_by_user_id=user_id
        )
        inv3 = Invoice(
            workspace_id=ws.id,
            partner_id=partner.id,
            invoice_number="BILL-2026-001",
            invoice_type="PAYABLE",
            total_amount=Decimal("25000.00"),
            balance_due=Decimal("25000.00"),
            issue_date=today - timedelta(days=5),
            due_date=today + timedelta(days=20),
            status="ISSUED",
            currency="INR",
            created_by_user_id=user_id
        )
        db.session.add_all([inv1, inv2, inv3])

        # 3. Recurring Obligation
        ro = RecurringObligation(
            workspace_id=ws.id,
            title="Cloud Infrastructure",
            obligation_type="PAYABLE",
            amount=Decimal("12000.00"),
            currency="INR",
            frequency="MONTHLY",
            start_date=today - timedelta(days=60),
            next_due_date=today + timedelta(days=15),
            status="ACTIVE"
        )
        db.session.add(ro)

        # 4. Staged Record
        staged = StagedExtraction(
            workspace_id=ws.id,
            created_by_user_id=user_id,
            source_channel="DOCUMENT_UPLOAD",
            candidate_type="EXPENSE",
            status="NEEDS_REVIEW",
            raw_extracted_data={"amount": 4500.0}
        )
        db.session.add(staged)
        db.session.commit()

        return user_id, ws.id


def test_historical_trends_service(app):
    user_id, ws_id = setup_intelligence_test_data(app)
    with app.app_context():
        trends = BusinessIntelligenceService.get_historical_trends(ws_id, months=6)
        assert trends['workspace_id'] == ws_id
        assert len(trends['trends']) == 6
        assert Decimal(trends['current_confirmed_cash']) == Decimal("160000.00")
        assert trends['insufficient_history'] is False


def test_cash_flow_forecast_service(app):
    user_id, ws_id = setup_intelligence_test_data(app)
    with app.app_context():
        forecast = BusinessIntelligenceService.calculate_cash_forecast(ws_id, horizon_days=90)
        assert forecast['workspace_id'] == ws_id
        assert forecast['methodology'] == 'DETERMINISTIC_CASH_SCHEDULE'
        assert Decimal(forecast['starting_confirmed_cash']) == Decimal("160000.00")
        assert len(forecast['weekly_trajectory']) > 0
        assert Decimal(forecast['total_projected_inflows']) > Decimal("0.00")
        assert Decimal(forecast['total_projected_outflows']) > Decimal("0.00")


def test_scenario_planning_service(app):
    user_id, ws_id = setup_intelligence_test_data(app)
    with app.app_context():
        scenarios = BusinessIntelligenceService.simulate_scenarios(
            ws_id,
            custom_params={'realization_rate': 75, 'expense_inflation': 110, 'delay_days': 15},
            horizon_days=90
        )
        sc = scenarios['scenarios']
        assert 'baseline' in sc
        assert 'conservative' in sc
        assert 'stress' in sc
        assert 'custom' in sc
        assert Decimal(sc['conservative']['projected_ending_cash']) < Decimal(sc['baseline']['projected_ending_cash'])
        assert Decimal(sc['stress']['projected_ending_cash']) < Decimal(sc['conservative']['projected_ending_cash'])


def test_executive_decision_brief_service(app):
    user_id, ws_id = setup_intelligence_test_data(app)
    with app.app_context():
        brief = BusinessIntelligenceService.get_executive_decision_brief(ws_id)
        assert brief['workspace_id'] == ws_id
        assert brief['overdue_receivables_count'] == 1
        assert Decimal(brief['total_overdue_receivables']) == Decimal("30000.00")
        assert brief['staged_records_pending'] == 1
        assert len(brief['recommendations']) > 0
        for r in brief['recommendations']:
            assert 'grounding_fact' in r
            assert 'action_route' in r


def test_intelligence_api_endpoints(client):
    user_id, ws_id = setup_intelligence_test_data(client.application)
    headers = {
        'Authorization': f"Bearer {user_id}",
        'Content-Type': 'application/json',
        'X-Workspace-Id': ws_id
    }

    # 1. Trends
    r_trends = client.get('/api/business/intelligence/trends?months=6', headers=headers)
    assert r_trends.status_code == 200
    assert 'trends' in r_trends.get_json()['data']

    # 2. Forecast
    r_fc = client.get('/api/business/intelligence/forecast?horizon_days=60', headers=headers)
    assert r_fc.status_code == 200
    assert 'forecast' in r_fc.get_json()['data']

    # 3. Scenarios
    r_sc = client.post('/api/business/intelligence/scenarios', json={'horizon_days': 90}, headers=headers)
    assert r_sc.status_code == 200
    assert 'scenarios' in r_sc.get_json()['data']

    # 4. Decision Brief
    r_br = client.get('/api/business/intelligence/brief', headers=headers)
    assert r_br.status_code == 200
    assert 'brief' in r_br.get_json()['data']


def test_intelligence_tenant_isolation(client):
    user_id, ws_id = setup_intelligence_test_data(client.application)
    with client.application.app_context():
        ws_other = Workspace(name="Other WS", base_currency="INR", timezone="UTC")
        db.session.add(ws_other)
        db.session.commit()
        other_id = ws_other.id

    headers = {
        'Authorization': f"Bearer {user_id}",
        'Content-Type': 'application/json',
        'X-Workspace-Id': other_id
    }
    r = client.get('/api/business/intelligence/brief', headers=headers)
    assert r.status_code == 403
