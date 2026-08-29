"""
DeadlineOS Business OS — Rescue & Overdue Aging Service
=======================================================
Calculates deterministic overdue aging buckets and priority rankings.
"""

from database.db import db
from datetime import date, datetime, timezone
from decimal import Decimal
from models.business import Invoice
from utils.errors import APIError


class RescueService:
    @staticmethod
    def get_aging_summary(workspace_id: str) -> dict:
        today = date.today()

        invoices = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'RECEIVABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date < today
        ).all()

        bucket_1 = {'label': '1-30 Days', 'count': 0, 'total': Decimal('0.00'), 'invoices': []}
        bucket_2 = {'label': '31-60 Days', 'count': 0, 'total': Decimal('0.00'), 'invoices': []}
        bucket_3 = {'label': '61-90 Days', 'count': 0, 'total': Decimal('0.00'), 'invoices': []}
        bucket_4 = {'label': '90+ Days', 'count': 0, 'total': Decimal('0.00'), 'invoices': []}

        total_overdue = Decimal('0.00')

        for inv in invoices:
            balance = Decimal(str(inv.balance_due))
            if balance <= Decimal('0.00'):
                continue

            days_overdue = (today - inv.due_date).days
            if days_overdue <= 0:
                continue

            total_overdue += balance
            inv_summary = {
                'id': inv.id,
                'invoice_number': inv.invoice_number,
                'partner_name': inv.partner.name if inv.partner else 'Unknown Client',
                'partner_id': inv.partner_id,
                'balance_due': str(balance),
                'due_date': inv.due_date.isoformat(),
                'days_overdue': days_overdue
            }

            if 1 <= days_overdue <= 30:
                bucket_1['count'] += 1
                bucket_1['total'] += balance
                bucket_1['invoices'].append(inv_summary)
            elif 31 <= days_overdue <= 60:
                bucket_2['count'] += 1
                bucket_2['total'] += balance
                bucket_2['invoices'].append(inv_summary)
            elif 61 <= days_overdue <= 90:
                bucket_3['count'] += 1
                bucket_3['total'] += balance
                bucket_3['invoices'].append(inv_summary)
            else:
                bucket_4['count'] += 1
                bucket_4['total'] += balance
                bucket_4['invoices'].append(inv_summary)

        return {
            'workspace_id': workspace_id,
            'as_of_date': today.isoformat(),
            'total_overdue_amount': f"{total_overdue:.2f}",
            'total_overdue_count': len(invoices),
            'buckets': {
                '1_to_30_days': {'count': bucket_1['count'], 'total': f"{bucket_1['total']:.2f}", 'invoices': bucket_1['invoices']},
                '31_to_60_days': {'count': bucket_2['count'], 'total': f"{bucket_2['total']:.2f}", 'invoices': bucket_2['invoices']},
                '61_to_90_days': {'count': bucket_3['count'], 'total': f"{bucket_3['total']:.2f}", 'invoices': bucket_3['invoices']},
                '90_plus_days': {'count': bucket_4['count'], 'total': f"{bucket_4['total']:.2f}", 'invoices': bucket_4['invoices']},
            }
        }

    @staticmethod
    def get_priority_receivables(workspace_id: str, limit: int = 20) -> list:
        today = date.today()

        invoices = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_type == 'RECEIVABLE',
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date < today
        ).all()

        priorities = []
        for inv in invoices:
            balance = Decimal(str(inv.balance_due))
            if balance <= Decimal('0.00'):
                continue

            days_overdue = (today - inv.due_date).days
            if days_overdue <= 0:
                continue

            # Formula: Priority Score = balance_due * (1 + days_overdue / 30)
            multiplier = Decimal('1.00') + (Decimal(days_overdue) / Decimal('30.00'))
            priority_score = balance * multiplier

            recommended_tone = 'GENTLE'
            if 31 <= days_overdue <= 60:
                recommended_tone = 'POLITE'
            elif 61 <= days_overdue <= 90:
                recommended_tone = 'URGENT'
            elif days_overdue > 90:
                recommended_tone = 'LEGAL'

            priorities.append({
                'invoice_id': inv.id,
                'invoice_number': inv.invoice_number,
                'partner_id': inv.partner_id,
                'partner_name': inv.partner.name if inv.partner else 'Unknown Client',
                'balance_due': str(balance),
                'due_date': inv.due_date.isoformat(),
                'days_overdue': days_overdue,
                'priority_score': f"{priority_score:.2f}",
                'recommended_tone': recommended_tone
            })

        # Sort descending by priority score
        priorities.sort(key=lambda x: Decimal(x['priority_score']), reverse=True)
        return priorities[:limit]
