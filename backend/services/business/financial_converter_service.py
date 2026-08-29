"""
DeadlineOS Business OS — Financial Converter Gateway
=====================================================
Bridges human-confirmed StagedExtractions into authoritative Invoices
or BusinessTransactions.
"""

from database.db import db
from models.business import StagedExtraction
from services.business.invoice_service import InvoiceService
from services.business.transaction_service import TransactionService
from services.business.audit_service import AuditService
from utils.errors import APIError


class FinancialConverterService:
    @staticmethod
    def commit_staged_item(
        workspace_id: str,
        staging_id: str,
        user_id: str,
        target_domain: str = None,  # INVOICE, TRANSACTION
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        staged = StagedExtraction.query.filter_by(id=staging_id, workspace_id=workspace_id).first()
        if not staged:
            raise APIError("Staged extraction not found.", code="STAGING_ITEM_NOT_FOUND", status=404)
        if staged.status != 'CONFIRMED':
            raise APIError(f"Cannot commit extraction in status '{staged.status}'. Must be CONFIRMED by reviewer first.", code="ITEM_NOT_CONFIRMED", status=400)

        norm = staged.normalized_data or {}
        target = target_domain or ('INVOICE' if staged.candidate_type in ('INVOICE_RECEIVABLE', 'INVOICE_PAYABLE') else 'TRANSACTION')

        if target == 'INVOICE':
            inv_type = 'RECEIVABLE' if staged.candidate_type == 'INVOICE_RECEIVABLE' else 'PAYABLE'
            inv = InvoiceService.create_invoice(
                workspace_id=workspace_id,
                user_id=user_id,
                data={
                    'invoice_type': inv_type,
                    'partner_id': norm.get('partner_id'),
                    'issue_date': norm.get('date'),
                    'due_date': norm.get('date'),
                    'currency': norm.get('currency', 'INR'),
                    'subtotal': norm.get('amount', '0.00'),
                    'notes': norm.get('description')
                },
                staged_extraction_id=staged.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'INVOICE', 'entity': inv.serialize()}
        else:
            tx = TransactionService.record_transaction(
                workspace_id=workspace_id,
                user_id=user_id,
                data={
                    'transaction_type': 'INCOME' if staged.candidate_type == 'INVOICE_RECEIVABLE' else 'EXPENSE',
                    'amount': norm.get('amount', '0.00'),
                    'currency': norm.get('currency', 'INR'),
                    'transaction_date': norm.get('date'),
                    'partner_id': norm.get('partner_id'),
                    'notes': norm.get('description')
                },
                staged_extraction_id=staged.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {'target': 'TRANSACTION', 'entity': tx.serialize()}
