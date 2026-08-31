"""
DeadlineOS Business OS — Business Intelligence Service
======================================================
Deterministic financial intelligence, cash flow forecasting,
scenario simulation, and explainable decision recommendations.
"""

from database.db import db
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
import calendar
from models.business import (
    BusinessTransaction,
    Invoice,
    CommercialPartner,
    RecurringObligation,
    StagedExtraction,
    BusinessEntity
)
from services.business.financial_truth_service import FinancialTruthService
from services.business.cash_risk_service import CashRiskService
from services.business.rescue_service import RescueService
from utils.errors import APIError


class BusinessIntelligenceService:
    @staticmethod
    def get_historical_trends(workspace_id: str, months: int = 6) -> dict:
        """
        Calculates monthly historical income, expense, and net flow trends
        using authoritative database transactions.
        """
        today = date.today()
        # Cap months between 3 and 12
        months = max(3, min(months, 12))

        # Determine start of first month
        start_year = today.year
        start_month = today.month - months + 1
        while start_month <= 0:
            start_month += 12
            start_year -= 1

        start_date = date(start_year, start_month, 1)

        # Query all confirmed transactions since start_date
        txs = BusinessTransaction.query.filter(
            BusinessTransaction.workspace_id == workspace_id,
            BusinessTransaction.status == 'CONFIRMED',
            BusinessTransaction.transaction_date >= start_date
        ).order_by(BusinessTransaction.transaction_date.asc()).all()

        # Query confirmed cash as of today
        cash_pos = FinancialTruthService.get_cash_position(workspace_id)
        current_confirmed_cash = Decimal(cash_pos['confirmed_cash'])

        # Group by Year-Month
        monthly_data = {}
        for m_offset in range(months):
            curr_m = start_month + m_offset
            curr_y = start_year
            while curr_m > 12:
                curr_m -= 12
                curr_y += 1
            key = f"{curr_y}-{curr_m:02d}"
            month_name = calendar.month_abbr[curr_m]
            monthly_data[key] = {
                'period': key,
                'label': f"{month_name} {curr_y}",
                'income': Decimal('0.00'),
                'expense': Decimal('0.00'),
                'net_flow': Decimal('0.00'),
                'transaction_count': 0
            }

        for t in txs:
            t_key = f"{t.transaction_date.year}-{t.transaction_date.month:02d}"
            if t_key in monthly_data:
                amt = Decimal(str(t.amount))
                monthly_data[t_key]['transaction_count'] += 1
                if t.transaction_type in ('INCOME', 'ADJUSTMENT'):
                    monthly_data[t_key]['income'] += amt
                elif t.transaction_type == 'EXPENSE':
                    monthly_data[t_key]['expense'] += amt

        # Compute net flow and check data density
        total_tx_count = len(txs)
        active_periods = sum(1 for d in monthly_data.values() if d['transaction_count'] > 0)
        insufficient_history = active_periods < 2

        trend_points = []
        for key in sorted(monthly_data.keys()):
            d = monthly_data[key]
            d['net_flow'] = d['income'] - d['expense']
            trend_points.append({
                'period': d['period'],
                'label': d['label'],
                'income': str(d['income']),
                'expense': str(d['expense']),
                'net_flow': str(d['net_flow']),
                'transaction_count': d['transaction_count']
            })

        # Calculate average monthly burn & revenue over active months
        total_income = sum((Decimal(p['income']) for p in trend_points), Decimal('0.00'))
        total_expense = sum((Decimal(p['expense']) for p in trend_points), Decimal('0.00'))
        avg_monthly_income = (total_income / Decimal(str(months))).quantize(Decimal('0.01'))
        avg_monthly_expense = (total_expense / Decimal(str(months))).quantize(Decimal('0.01'))
        avg_monthly_net = avg_monthly_income - avg_monthly_expense

        return {
            'workspace_id': workspace_id,
            'months_analyzed': months,
            'insufficient_history': insufficient_history,
            'total_transactions_analyzed': total_tx_count,
            'current_confirmed_cash': str(current_confirmed_cash),
            'avg_monthly_income': str(avg_monthly_income),
            'avg_monthly_expense': str(avg_monthly_expense),
            'avg_monthly_net_flow': str(avg_monthly_net),
            'trends': trend_points
        }

    @staticmethod
    def calculate_cash_forecast(workspace_id: str, horizon_days: int = 90) -> dict:
        """
        Generates a deterministic forward-looking cash flow forecast by combining:
        - Confirmed Cash starting balance
        - Committed Receivables (scheduled by due_date)
        - Committed Payables (scheduled by due_date)
        - Active Recurring Obligations (amortized weekly)
        """
        today = date.today()
        horizon_days = max(14, min(horizon_days, 180))
        end_date = today + timedelta(days=horizon_days)

        # 1. Starting Balance
        cash_pos = FinancialTruthService.get_cash_position(workspace_id, window_days=horizon_days)
        starting_cash = Decimal(cash_pos['confirmed_cash'])

        # 2. Receivables due within horizon
        receivables = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'RECEIVABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date <= end_date
        ).all()

        # 3. Payables due within horizon
        payables = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'PAYABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date <= end_date
        ).all()

        # 4. Recurring Obligations
        recurring_items = RecurringObligation.query.filter(
            RecurringObligation.workspace_id == workspace_id,
            RecurringObligation.status == 'ACTIVE'
        ).all()

        # Weekly Bucketing (7-day intervals)
        num_weeks = (horizon_days + 6) // 7
        weekly_forecast = []
        running_cash = starting_cash
        min_cash = starting_cash
        min_cash_date = today
        deficit_date = None
        total_projected_inflows = Decimal('0.00')
        total_projected_outflows = Decimal('0.00')

        for w in range(num_weeks):
            week_start = today + timedelta(days=w * 7)
            week_end = min(today + timedelta(days=(w + 1) * 7 - 1), end_date)

            week_inflows = Decimal('0.00')
            week_outflows = Decimal('0.00')
            inflow_items = []
            outflow_items = []

            # Ingest Receivables due in this week
            for r in receivables:
                r_effective_due = max(r.due_date, today) if r.due_date < today else r.due_date
                if week_start <= r_effective_due <= week_end:
                    amt = Decimal(str(r.balance_due))
                    week_inflows += amt
                    inflow_items.append({
                        'type': 'RECEIVABLE',
                        'invoice_number': r.invoice_number,
                        'amount': str(amt),
                        'partner': r.partner.name if r.partner else 'Client',
                        'due_date': r.due_date.isoformat()
                    })

            # Ingest Payables due in this week
            for p in payables:
                p_effective_due = max(p.due_date, today) if p.due_date < today else p.due_date
                if week_start <= p_effective_due <= week_end:
                    amt = Decimal(str(p.balance_due))
                    week_outflows += amt
                    outflow_items.append({
                        'type': 'PAYABLE',
                        'invoice_number': p.invoice_number,
                        'amount': str(amt),
                        'partner': p.partner.name if p.partner else 'Vendor',
                        'due_date': p.due_date.isoformat()
                    })

            # Ingest Recurring Obligations matching this week
            for ro in recurring_items:
                amt = Decimal(str(ro.amount))
                weekly_amt = Decimal('0.00')
                if ro.frequency == 'MONTHLY':
                    weekly_amt = (amt * Decimal('12.00') / Decimal('52.00')).quantize(Decimal('0.01'))
                elif ro.frequency == 'WEEKLY':
                    weekly_amt = amt
                elif ro.frequency == 'BIWEEKLY':
                    weekly_amt = (amt / Decimal('2.00')).quantize(Decimal('0.01'))
                elif ro.frequency == 'QUARTERLY':
                    weekly_amt = (amt * Decimal('4.00') / Decimal('52.00')).quantize(Decimal('0.01'))
                elif ro.frequency in ('ANNUALLY', 'ANNUAL'):
                    weekly_amt = (amt / Decimal('52.00')).quantize(Decimal('0.01'))

                if ro.obligation_type in ('PAYABLE', 'EXPENSE', 'TAX_COMPLIANCE', 'PAYROLL'):
                    week_outflows += weekly_amt
                elif ro.obligation_type in ('RECEIVABLE', 'INCOME'):
                    week_inflows += weekly_amt

            running_cash = running_cash + week_inflows - week_outflows
            total_projected_inflows += week_inflows
            total_projected_outflows += week_outflows

            if running_cash < min_cash:
                min_cash = running_cash
                min_cash_date = week_end

            if running_cash < Decimal('0.00') and deficit_date is None:
                deficit_date = week_end.isoformat()

            weekly_forecast.append({
                'week_number': w + 1,
                'start_date': week_start.isoformat(),
                'end_date': week_end.isoformat(),
                'label': f"W{w + 1} ({week_start.strftime('%b %d')})",
                'projected_inflows': str(week_inflows),
                'projected_outflows': str(week_outflows),
                'net_flow': str(week_inflows - week_outflows),
                'projected_ending_cash': str(running_cash),
                'is_deficit': running_cash < Decimal('0.00'),
                'inflow_count': len(inflow_items),
                'outflow_count': len(outflow_items)
            })

        return {
            'workspace_id': workspace_id,
            'forecast_horizon_days': horizon_days,
            'methodology': 'DETERMINISTIC_CASH_SCHEDULE',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'starting_confirmed_cash': str(starting_cash),
            'total_projected_inflows': str(total_projected_inflows),
            'total_projected_outflows': str(total_projected_outflows),
            'final_projected_cash': str(running_cash),
            'minimum_projected_cash': str(min_cash),
            'minimum_cash_date': min_cash_date.isoformat(),
            'has_projected_deficit': deficit_date is not None,
            'first_deficit_date': deficit_date,
            'weekly_trajectory': weekly_forecast
        }

    @staticmethod
    def simulate_scenarios(
        workspace_id: str,
        custom_params: dict = None,
        horizon_days: int = 90
    ) -> dict:
        """
        Executes deterministic multi-scenario cash simulations:
        - BASELINE: Scheduled cash flows
        - CONSERVATIVE: 85% receivable collection, 10% expense inflation, 30d collection delay
        - STRESS_TEST: 70% receivable collection, 20% expense inflation, 60d collection delay
        - CUSTOM: User-defined levers
        """
        horizon_days = max(30, min(horizon_days, 180))

        cash_pos = FinancialTruthService.get_cash_position(workspace_id, window_days=horizon_days)
        starting_cash = Decimal(cash_pos['confirmed_cash'])
        committed_inflows = Decimal(cash_pos['committed_inflows'])
        committed_outflows = Decimal(cash_pos['committed_outflows'])

        recurring_items = RecurringObligation.query.filter(
            RecurringObligation.workspace_id == workspace_id,
            RecurringObligation.status == 'ACTIVE'
        ).all()

        recurring_monthly_outflow = Decimal('0.00')
        for ro in recurring_items:
            amt = Decimal(str(ro.amount))
            if ro.obligation_type in ('PAYABLE', 'EXPENSE', 'TAX_COMPLIANCE', 'PAYROLL'):
                if ro.frequency == 'MONTHLY':
                    recurring_monthly_outflow += amt
                elif ro.frequency == 'WEEKLY':
                    recurring_monthly_outflow += (amt * Decimal('52.00') / Decimal('12.00'))
                elif ro.frequency == 'BIWEEKLY':
                    recurring_monthly_outflow += (amt * Decimal('26.00') / Decimal('12.00'))
                elif ro.frequency == 'QUARTERLY':
                    recurring_monthly_outflow += (amt / Decimal('3.00'))
                elif ro.frequency in ('ANNUALLY', 'ANNUAL'):
                    recurring_monthly_outflow += (amt / Decimal('12.00'))

        recurring_horizon_outflow = (recurring_monthly_outflow * (Decimal(str(horizon_days)) / Decimal('30.00'))).quantize(Decimal('0.01'))
        total_base_outflow = committed_outflows + recurring_horizon_outflow

        def run_sim(realization_rate: Decimal, delay_days: int, expense_mult: Decimal) -> dict:
            sim_inflow = (committed_inflows * realization_rate).quantize(Decimal('0.01'))
            sim_outflow = (total_base_outflow * expense_mult).quantize(Decimal('0.01'))
            sim_ending_cash = starting_cash + sim_inflow - sim_outflow

            sim_monthly_burn = (sim_outflow / (Decimal(str(horizon_days)) / Decimal('30.00'))).quantize(Decimal('0.01'))
            sim_runway_days = None
            if sim_monthly_burn > Decimal('0.00'):
                sim_runway_days = max(0, int((starting_cash / (sim_monthly_burn / Decimal('30.00')))))

            deficit = sim_ending_cash < Decimal('0.00')

            return {
                'scenario_type': 'SIMULATION',
                'realization_rate_pct': float(realization_rate * 100),
                'collection_delay_days': delay_days,
                'expense_multiplier': float(expense_mult),
                'starting_cash': str(starting_cash),
                'projected_inflows': str(sim_inflow),
                'projected_outflows': str(sim_outflow),
                'projected_ending_cash': str(sim_ending_cash),
                'variance_from_starting': str(sim_ending_cash - starting_cash),
                'has_deficit': deficit,
                'projected_runway_days': sim_runway_days
            }

        # 1. Baseline Scenario
        baseline = run_sim(realization_rate=Decimal('1.00'), delay_days=0, expense_mult=Decimal('1.00'))
        baseline['name'] = 'Baseline Model'
        baseline['description'] = 'Full collection of committed invoices with standard budgeted operating expenses.'

        # 2. Conservative Scenario
        conservative = run_sim(realization_rate=Decimal('0.85'), delay_days=30, expense_mult=Decimal('1.10'))
        conservative['name'] = 'Conservative Model'
        conservative['description'] = '15% receivable slippage and a 10% contingency buffer on operational outflows.'

        # 3. Severe Stress Test
        stress = run_sim(realization_rate=Decimal('0.70'), delay_days=60, expense_mult=Decimal('1.25'))
        stress['name'] = 'Stress Test (Downside)'
        stress['description'] = '30% default / delay on receivables combined with a 25% inflation shock on operating burn.'

        # 4. Optional Custom Scenario
        custom = None
        if custom_params:
            try:
                c_realization = Decimal(str(custom_params.get('realization_rate', 100))) / Decimal('100.00')
                c_delay = int(custom_params.get('delay_days', 0))
                c_expense_mult = Decimal(str(custom_params.get('expense_inflation', 100))) / Decimal('100.00')
                custom = run_sim(realization_rate=c_realization, delay_days=c_delay, expense_mult=c_expense_mult)
                custom['name'] = 'Custom Executive Simulation'
                custom['description'] = f"Custom scenario with {float(c_realization*100):.0f}% collection and {float(c_expense_mult*100):.0f}% expense factor."
            except Exception:
                custom = None

        return {
            'workspace_id': workspace_id,
            'horizon_days': horizon_days,
            'currency': 'INR',
            'scenarios': {
                'baseline': baseline,
                'conservative': conservative,
                'stress': stress,
                'custom': custom
            }
        }

    @staticmethod
    def get_executive_decision_brief(workspace_id: str) -> dict:
        """
        Synthesizes deterministic financial truth, risk signals, overdue queues,
        staging backlog, and generates prioritized, explainable executive recommendations.
        """
        cash_pos = FinancialTruthService.get_cash_position(workspace_id, window_days=30)
        runway_data = FinancialTruthService.calculate_runway_days(workspace_id)
        risks_data = CashRiskService.evaluate_risks(workspace_id)

        staged_count = StagedExtraction.query.filter(
            StagedExtraction.workspace_id == workspace_id,
            StagedExtraction.status.in_(['NEEDS_REVIEW', 'EXTRACTED', 'RECEIVED'])
        ).count()

        overdue_invoices = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'RECEIVABLE',
            Invoice.status == 'OVERDUE'
        ).all()
        total_overdue_amt = sum((Decimal(str(i.balance_due)) for i in overdue_invoices), Decimal('0.00'))

        recommendations = []

        if len(overdue_invoices) > 0 and total_overdue_amt > Decimal('0.00'):
            recommendations.append({
                'id': 'REC-RESCUE-OVERDUE',
                'priority': 'CRITICAL' if total_overdue_amt > Decimal('50000.00') else 'HIGH',
                'title': f'Accelerate Collection of ₹{total_overdue_amt:.2f} Overdue Receivables',
                'category': 'CASH_ACCELERATION',
                'reason': f'{len(overdue_invoices)} client invoices are currently overdue, locking operating liquidity.',
                'grounding_fact': f'Confirmed overdue balance: ₹{total_overdue_amt:.2f} across {len(overdue_invoices)} invoices.',
                'suggested_action': 'Dispatch automated payment reminders or execute rescue workflow.',
                'action_route': '/business/rescue'
            })

        runway_days = runway_data.get('runway_days')
        if runway_days is not None and runway_days < 45:
            recommendations.append({
                'id': 'REC-RUNWAY-PRESERVATION',
                'priority': 'CRITICAL',
                'title': f'Execute Runway Extension Plan ({runway_days} Days Remaining)',
                'category': 'CAPITAL_PRESERVATION',
                'reason': f'Current confirmed cash supports {runway_days} days of operational burn at ADBR-30.',
                'grounding_fact': f'Confirmed cash is ₹{cash_pos["confirmed_cash"]} with runway state {runway_data["state"]}.',
                'suggested_action': 'Review discretionary payables and delay uncommitted capital expenditures.',
                'action_route': '/business/recurring'
            })

        if staged_count > 0:
            recommendations.append({
                'id': 'REC-STAGING-INGESTION',
                'priority': 'MEDIUM',
                'title': f'Process {staged_count} Pending Ingestion Documents in Staging',
                'category': 'DATA_HYGIENE',
                'reason': 'Unconfirmed receipts or invoices in the staging barrier prevent ledger precision.',
                'grounding_fact': f'{staged_count} staged records are awaiting human-in-the-loop confirmation.',
                'suggested_action': 'Inspect and commit verified documents to update ledger truth.',
                'action_route': '/business/staging'
            })

        for r in risks_data.get('risks', []):
            if r.get('code') == 'RECEIVABLE_CONCENTRATION':
                recommendations.append({
                    'id': 'REC-RISK-CONCENTRATION',
                    'priority': 'HIGH',
                    'title': 'Mitigate High Single-Customer Concentration',
                    'category': 'RISK_MITIGATION',
                    'reason': r.get('message', 'High revenue concentration in a single client.'),
                    'grounding_fact': f"Customer concentration metric: {r.get('metric')}",
                    'suggested_action': 'Structure milestone-based billing and request upfront retainers.',
                    'action_route': '/business/invoices'
                })

        return {
            'workspace_id': workspace_id,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'financial_health': risks_data.get('overall_status', 'HEALTHY'),
            'confirmed_cash': cash_pos['confirmed_cash'],
            'committed_inflows_30d': cash_pos['committed_inflows'],
            'committed_outflows_30d': cash_pos['committed_outflows'],
            'projected_position_30d': cash_pos['projected_position'],
            'runway_days': runway_data.get('runway_days'),
            'runway_state': runway_data.get('state'),
            'overdue_receivables_count': len(overdue_invoices),
            'total_overdue_receivables': str(total_overdue_amt),
            'staged_records_pending': staged_count,
            'active_risks': risks_data.get('risks', []),
            'recommendations': recommendations
        }
