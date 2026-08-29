"""
DeadlineOS Business OS — Cash Risk Engine
=========================================
Evaluates deterministic cash risk rules across committed receivables,
payables, and burn velocity.
"""

from database.db import db
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from models.business import Invoice, BusinessTransaction
from services.business.financial_truth_service import FinancialTruthService


class CashRiskService:
    @staticmethod
    def evaluate_risks(workspace_id: str) -> dict:
        today = date.today()
        risks = []

        # 1. Cash Position & Runway Evaluation
        cash_data = FinancialTruthService.get_cash_position(workspace_id, window_days=30)
        runway_data = FinancialTruthService.calculate_runway_days(workspace_id)

        confirmed_cash = Decimal(cash_data['confirmed_cash'])
        projected_position = Decimal(cash_data['projected_position'])

        # Rule 1: DEFICIT_WARNING (Projected position < 0 within 30 days)
        if projected_position < Decimal('0.00'):
            risks.append({
                'code': 'DEFICIT_WARNING',
                'severity': 'CRITICAL',
                'title': 'Projected Cash Deficit Detected',
                'message': f'Committed outflows exceed inflows by ₹{abs(projected_position):.2f} within 30 days.',
                'metric': str(projected_position)
            })

        # Rule 2: CRITICAL_RUNWAY (Runway Days < 30)
        runway_days = runway_data.get('runway_days')
        if runway_days is not None and runway_days < 30:
            risks.append({
                'code': 'CRITICAL_RUNWAY',
                'severity': 'CRITICAL',
                'title': 'Critical Runway Shortfall',
                'message': f'Current confirmed cash supports only {runway_days} days of operational burn.',
                'metric': str(runway_days)
            })

        # Rule 3: RECEIVABLE_CONCENTRATION (Single client > 40% of total receivables)
        receivables = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'RECEIVABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE'])
        ).all()

        total_receivables = sum((Decimal(str(r.balance_due)) for r in receivables), Decimal('0.00'))
        if total_receivables > Decimal('0.00'):
            partner_balances = {}
            for r in receivables:
                pid = r.partner_id or 'unknown'
                partner_balances[pid] = partner_balances.get(pid, Decimal('0.00')) + Decimal(str(r.balance_due))

            for pid, pbal in partner_balances.items():
                ratio = (pbal / total_receivables) * Decimal('100.00')
                if ratio >= Decimal('40.00'):
                    pname = receivables[0].partner.name if receivables[0].partner else 'Top Client'
                    risks.append({
                        'code': 'RECEIVABLE_CONCENTRATION',
                        'severity': 'WARNING',
                        'title': 'High Customer Concentration Risk',
                        'message': f'A single client represents {ratio:.1f}% of total outstanding receivables (₹{pbal:.2f}).',
                        'metric': f"{ratio:.1f}%"
                    })
                    break

        # Rule 4: BURN_ACCELERATION (Recent 14d burn > 1.5x 30d average)
        past_14 = today - timedelta(days=14)
        past_30 = today - timedelta(days=30)

        recent_14_expenses = BusinessTransaction.query.filter(
            BusinessTransaction.workspace_id == workspace_id,
            BusinessTransaction.status == 'CONFIRMED',
            BusinessTransaction.transaction_type == 'EXPENSE',
            BusinessTransaction.transaction_date >= past_14
        ).all()
        recent_14_sum = sum((Decimal(str(e.amount)) for e in recent_14_expenses), Decimal('0.00'))
        recent_daily_burn = recent_14_sum / Decimal('14.00')

        adbr_30 = Decimal(runway_data.get('adbr_30', '0.00'))
        if adbr_30 > Decimal('0.00') and recent_daily_burn > (adbr_30 * Decimal('1.5')):
            risks.append({
                'code': 'BURN_ACCELERATION',
                'severity': 'WARNING',
                'title': 'Burn Velocity Acceleration',
                'message': f'Recent 14-day daily burn rate (₹{recent_daily_burn:.2f}/day) is {recent_daily_burn / adbr_30:.1f}x higher than the 30-day baseline.',
                'metric': f"{recent_daily_burn:.2f}/day"
            })

        overall_status = 'HEALTHY'
        if any(r['severity'] == 'CRITICAL' for r in risks):
            overall_status = 'CRITICAL'
        elif any(r['severity'] == 'WARNING' for r in risks):
            overall_status = 'WARNING'

        return {
            'overall_status': overall_status,
            'risks_count': len(risks),
            'risks': risks,
            'evaluated_at': datetime.now(timezone.utc).isoformat()
        }
