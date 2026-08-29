"""
DeadlineOS Business OS — Financial Consolidation Service
========================================================
Deterministic multi-workspace and multi-entity financial consolidation with
inter-entity transfer elimination and exact Decimal arithmetic.
"""

from decimal import Decimal
from models.business import WorkspaceMember, Workspace, Invoice, BusinessTransaction, InterEntityTransfer
from services.business.financial_truth_service import FinancialTruthService
from utils.errors import APIError


class ConsolidationService:
    @staticmethod
    def get_consolidated_overview(user_id: str, workspace_ids: list = None) -> dict:
        """
        Computes real-time consolidated financial position across multiple workspaces.
        Strict Invariant: Asserts user membership in ALL requested workspaces.
        """
        # If workspace_ids not provided, find all active workspaces user belongs to
        if not workspace_ids:
            memberships = WorkspaceMember.query.filter_by(user_id=user_id, status='ACTIVE').all()
            target_ids = [m.workspace_id for m in memberships]
        else:
            target_ids = list(set(workspace_ids))
            for ws_id in target_ids:
                mem = WorkspaceMember.query.filter_by(workspace_id=ws_id, user_id=user_id, status='ACTIVE').first()
                if not mem:
                    raise APIError(f"Unauthorized: You do not belong to workspace {ws_id}.", code="WORKSPACE_UNAUTHORIZED", status=403)

        if not target_ids:
            return {
                'consolidated_cash': '0.00',
                'consolidated_revenue': '0.00',
                'consolidated_expenses': '0.00',
                'consolidated_receivables': '0.00',
                'consolidated_payables': '0.00',
                'inter_entity_eliminations': '0.00',
                'net_operating_cashflow': '0.00',
                'workspaces_count': 0,
                'workspace_breakdowns': []
            }

        total_cash = Decimal('0.00')
        total_rev = Decimal('0.00')
        total_exp = Decimal('0.00')
        total_ar = Decimal('0.00')
        total_ap = Decimal('0.00')
        breakdowns = []

        for ws_id in target_ids:
            ws = Workspace.query.get(ws_id)
            if not ws:
                continue

            # Deterministic truth from B3
            cash_data = FinancialTruthService.get_cash_position(ws_id, window_days=30)
            runway_data = FinancialTruthService.calculate_runway_days(ws_id)

            cash_pos = Decimal(cash_data['confirmed_cash'])
            ar_pos = Decimal(cash_data['committed_inflows'])
            ap_pos = Decimal(cash_data['committed_outflows'])
            runway_days = runway_data.get('runway_days')

            # Calculate total income & expense transactions in this workspace
            incomes = BusinessTransaction.query.filter_by(workspace_id=ws_id, transaction_type='INCOME', status='CONFIRMED').all()
            ws_rev = sum((Decimal(str(t.amount)) for t in incomes), Decimal('0.00'))

            expenses = BusinessTransaction.query.filter_by(workspace_id=ws_id, transaction_type='EXPENSE', status='CONFIRMED').all()
            ws_exp = sum((Decimal(str(t.amount)) for t in expenses), Decimal('0.00'))

            total_cash += cash_pos
            total_ar += ar_pos
            total_ap += ap_pos
            total_rev += ws_rev
            total_exp += ws_exp

            breakdowns.append({
                'workspace_id': ws_id,
                'workspace_name': ws.name,
                'cash_position': str(cash_pos),
                'receivables': str(ar_pos),
                'payables': str(ap_pos),
                'revenue': str(ws_rev),
                'expenses': str(ws_exp),
                'runway_days': runway_days
            })

        # Calculate inter-entity eliminations between target workspaces
        internal_transfers = InterEntityTransfer.query.filter(
            InterEntityTransfer.source_workspace_id.in_(target_ids),
            InterEntityTransfer.destination_workspace_id.in_(target_ids),
            InterEntityTransfer.status == 'SETTLED'
        ).all()

        eliminations = sum((Decimal(str(t.amount)) for t in internal_transfers), Decimal('0.00'))
        net_cashflow = (total_rev - total_exp)

        return {
            'consolidated_cash': str(total_cash),
            'consolidated_revenue': str(total_rev),
            'consolidated_expenses': str(total_exp),
            'consolidated_receivables': str(total_ar),
            'consolidated_payables': str(total_ap),
            'inter_entity_eliminations': str(eliminations),
            'net_operating_cashflow': str(net_cashflow),
            'workspaces_count': len(target_ids),
            'workspace_breakdowns': breakdowns
        }
