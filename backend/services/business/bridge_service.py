"""
DeadlineOS Business OS — Polymorphic Bridge Adapter
===================================================
Projects business deadlines and cash obligations into the user's unified
Today / Calendar schedule feed without mutating Personal OS schemas.
"""

from database.db import db
from datetime import date, timedelta
from decimal import Decimal
from models.business import Invoice, WorkspaceMember


class BridgeService:
    @staticmethod
    def get_user_unified_feed(user_id: str, window_days: int = 14) -> list:
        """
        Gathers active business obligations across all workspaces where user is a member
        and projects them as read-only virtual calendar feed items.
        """
        today = date.today()
        window_end = today + timedelta(days=window_days)

        # 1. Find all active workspaces for user
        memberships = WorkspaceMember.query.filter_by(user_id=user_id, status='ACTIVE').all()
        workspace_ids = [m.workspace_id for m in memberships]

        if not workspace_ids:
            return []

        # 2. Query open receivables and payables due within window
        invoices = Invoice.query.filter(
            Invoice.workspace_id.in_(workspace_ids),
            Invoice.status.in_(['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']),
            Invoice.due_date <= window_end
        ).order_by(Invoice.due_date.asc()).all()

        virtual_feed = []
        for inv in invoices:
            partner_name = inv.partner.name if inv.partner else 'Commercial Partner'
            if inv.invoice_type == 'RECEIVABLE':
                title = f"Collect ₹{inv.balance_due} from {partner_name} ({inv.invoice_number})"
                urgency = 'CRITICAL' if inv.due_date < today else ('HIGH' if inv.due_date == today else 'MEDIUM')
            else:
                title = f"Pay ₹{inv.balance_due} to {partner_name} ({inv.invoice_number})"
                urgency = 'CRITICAL' if inv.due_date < today else ('HIGH' if inv.due_date == today else 'LOW')

            virtual_feed.append({
                'id': f"virt-inv-{inv.id}",
                'source_domain': 'BUSINESS_OS',
                'entity_type': f"INVOICE_{inv.invoice_type}",
                'entity_id': inv.id,
                'workspace_id': inv.workspace_id,
                'title': title,
                'amount': str(inv.balance_due),
                'currency': inv.currency,
                'due_date': inv.due_date.isoformat(),
                'status': inv.status,
                'urgency': urgency,
                'action_url': f"/business/invoices/{inv.id}"
            })

        return virtual_feed
