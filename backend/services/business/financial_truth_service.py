"""
DeadlineOS Business OS — Financial Truth Service
================================================
Calculates Confirmed Cash, Committed Inflows/Outflows, Projected Position,
and evaluates the deterministic 5-tier Runway Days state precedence.
"""

from database.db import db
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
import math
from models.business import BusinessTransaction, Invoice, Workspace


class FinancialTruthService:
    @staticmethod
    def get_cash_position(workspace_id: str, window_days: int = 30) -> dict:
        today = date.today()
        window_end = today + timedelta(days=window_days)

        # 1. Confirmed Cash: Sum of all settled, non-reversed transactions
        settled_txs = BusinessTransaction.query.filter(
            BusinessTransaction.workspace_id == workspace_id,
            BusinessTransaction.status == 'CONFIRMED'
        ).all()

        confirmed_cash = Decimal('0.00')
        for t in settled_txs:
            amt = Decimal(str(t.amount))
            if t.transaction_type in ('INCOME', 'ADJUSTMENT'):
                confirmed_cash += amt
            elif t.transaction_type == 'EXPENSE':
                confirmed_cash -= amt

        # 2. Committed Inflows: Receivables due within window
        receivables = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'RECEIVABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date <= window_end
        ).all()
        committed_inflows = sum((Decimal(str(r.balance_due)) for r in receivables), Decimal('0.00'))

        # 3. Committed Outflows: Payables due within window
        payables = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'PAYABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date <= window_end
        ).all()
        committed_outflows = sum((Decimal(str(p.balance_due)) for p in payables), Decimal('0.00'))

        # 4. Projected Position
        projected_position = confirmed_cash + committed_inflows - committed_outflows

        return {
            'confirmed_cash': str(confirmed_cash),
            'committed_inflows': str(committed_inflows),
            'committed_outflows': str(committed_outflows),
            'projected_position': str(projected_position),
            'window_days': window_days,
            'currency': 'INR'
        }

    @staticmethod
    def calculate_runway_days(workspace_id: str) -> dict:
        today = date.today()
        cash_data = FinancialTruthService.get_cash_position(workspace_id, window_days=30)
        confirmed_cash = Decimal(cash_data['confirmed_cash'])

        # 1. Check Priority 1: RUNWAY_NEGATIVE
        if confirmed_cash <= Decimal('0.00'):
            return {
                'state': 'RUNWAY_NEGATIVE',
                'runway_days': 0,
                'confirmed_cash': str(confirmed_cash),
                'adbr_30': '0.00',
                'message': 'Zero or negative cash balance. Immediate capital injection required.'
            }

        # 2. Check Priority 2: RUNWAY_STALE (Last tx > 7 days ago)
        last_tx = BusinessTransaction.query.filter(
            BusinessTransaction.workspace_id == workspace_id,
            BusinessTransaction.status == 'CONFIRMED'
        ).order_by(BusinessTransaction.transaction_date.desc()).first()

        if not last_tx or (today - last_tx.transaction_date).days > 7:
            return {
                'state': 'RUNWAY_STALE',
                'runway_days': None,
                'confirmed_cash': str(confirmed_cash),
                'adbr_30': '0.00',
                'message': 'Stale Data — Record recent transactions to calculate active runway.'
            }

        # 3. Calculate ADBR_30: (Expenses[-30, 0] + Payables[0, +30]) / 60
        past_30 = today - timedelta(days=30)
        fut_30 = today + timedelta(days=30)

        past_expenses = BusinessTransaction.query.filter(
            BusinessTransaction.workspace_id == workspace_id,
            BusinessTransaction.status == 'CONFIRMED',
            BusinessTransaction.transaction_type == 'EXPENSE',
            BusinessTransaction.transaction_date >= past_30,
            BusinessTransaction.transaction_date <= today
        ).all()
        expense_sum = sum((Decimal(str(e.amount)) for e in past_expenses), Decimal('0.00'))

        committed_payables = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'PAYABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date <= fut_30
        ).all()
        payables_sum = sum((Decimal(str(p.balance_due)) for p in committed_payables), Decimal('0.00'))

        adbr_30 = (expense_sum + payables_sum) / Decimal('60.00')

        # 4. Check Priority 3: RUNWAY_INSUFFICIENT_HISTORY (Age < 14 days and payables == 0)
        ws = Workspace.query.filter_by(id=workspace_id).first()
        ws_age_days = (today - ws.created_at.date()).days if ws and ws.created_at else 0

        if ws_age_days < 14 and payables_sum == Decimal('0.00') and expense_sum == Decimal('0.00'):
            return {
                'state': 'RUNWAY_INSUFFICIENT_HISTORY',
                'runway_days': None,
                'confirmed_cash': str(confirmed_cash),
                'adbr_30': '0.00',
                'message': 'Runway calculating (requires 14 days of operational history).'
            }

        # 5. Check Priority 4: RUNWAY_ZERO_BURN
        if adbr_30 == Decimal('0.00'):
            return {
                'state': 'RUNWAY_ZERO_BURN',
                'runway_days': 999,
                'confirmed_cash': str(confirmed_cash),
                'adbr_30': '0.00',
                'message': 'Zero burn rate detected (no active expenses or payables).'
            }

        # 6. Priority 5: CALCULATED
        runway_days = math.floor(confirmed_cash / adbr_30)
        return {
            'state': 'CALCULATED',
            'runway_days': runway_days,
            'confirmed_cash': str(confirmed_cash),
            'adbr_30': f"{adbr_30:.2f}",
            'message': f"{runway_days} days of operational runway remaining."
        }
