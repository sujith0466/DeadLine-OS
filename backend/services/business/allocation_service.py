"""
DeadlineOS Business OS — Payment Allocation Service
===================================================
Coordinates payment allocations to invoices with strict conservation math
and balance synchronization.
"""

from database.db import db
from datetime import datetime, timezone
from decimal import Decimal
from models.business import PaymentAllocation, BusinessTransaction, Invoice
from services.business.audit_service import AuditService
from services.business.invoice_service import InvoiceService
from services.business.normalizer_service import NormalizerService
from utils.errors import APIError
import uuid


class AllocationService:
    @staticmethod
    def allocate_payment(
        workspace_id: str,
        user_id: str,
        transaction_id: str,
        allocations_data: list,
        ip_address: str = None,
        user_agent: str = None
    ) -> list:
        tx = BusinessTransaction.query.filter_by(id=transaction_id, workspace_id=workspace_id).first()
        if not tx:
            raise APIError("Transaction not found.", code="TRANSACTION_NOT_FOUND", status=404)
        if tx.status != 'CONFIRMED':
            raise APIError(f"Cannot allocate non-confirmed transaction in status '{tx.status}'.", code="INVALID_TRANSACTION_STATUS", status=400)

        # 1. Compute already allocated amount for this transaction
        existing_allocations = PaymentAllocation.query.filter_by(
            transaction_id=tx.id,
            status='ACTIVE'
        ).all()
        current_allocated_total = sum((Decimal(str(a.allocated_amount)) for a in existing_allocations), Decimal('0.00'))
        tx_amount = Decimal(str(tx.amount))
        available_tx_balance = tx_amount - current_allocated_total

        created_allocations = []
        invoices_to_recalc = set()

        for req in allocations_data:
            inv_id = req.get('invoice_id')
            alloc_amt = Decimal(NormalizerService.normalize_amount(req.get('allocated_amount', '0.00')))
            if alloc_amt <= Decimal('0.00'):
                raise APIError("Allocated amount must be strictly greater than 0.", code="INVALID_ALLOCATION_AMOUNT", status=400)

            if alloc_amt > available_tx_balance:
                raise APIError(f"Allocation of {alloc_amt} exceeds available transaction balance of {available_tx_balance}.", code="INSUFFICIENT_TRANSACTION_BALANCE", status=400)

            inv = Invoice.query.filter_by(id=inv_id, workspace_id=workspace_id).first()
            if not inv:
                raise APIError(f"Invoice '{inv_id}' not found.", code="INVOICE_NOT_FOUND", status=404)
            if inv.status in ('DRAFT', 'VOID'):
                raise APIError(f"Cannot allocate payment to invoice in status '{inv.status}'.", code="INVALID_INVOICE_STATUS", status=400)

            if tx.currency != inv.currency:
                raise APIError(f"Currency mismatch: Transaction ({tx.currency}) != Invoice ({inv.currency}).", code="CURRENCY_MISMATCH", status=400)

            if alloc_amt > inv.balance_due:
                raise APIError(f"Allocation of {alloc_amt} exceeds invoice balance due of {inv.balance_due}.", code="ALLOCATION_EXCEEDS_BALANCE", status=400)

            alloc_id = str(uuid.uuid4())
            alloc = PaymentAllocation(
                id=alloc_id,
                workspace_id=workspace_id,
                transaction_id=tx.id,
                invoice_id=inv.id,
                allocated_amount=alloc_amt,
                status='ACTIVE',
                allocated_by_user_id=user_id,
                notes=req.get('notes')
            )
            db.session.add(alloc)
            available_tx_balance -= alloc_amt
            created_allocations.append(alloc)
            invoices_to_recalc.add(inv.id)

        db.session.commit()

        for inv_id in invoices_to_recalc:
            InvoiceService.recalculate_invoice_balance(workspace_id, inv_id)

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='PAYMENT_ALLOCATED',
            entity_type='TRANSACTION',
            entity_id=tx.id,
            after_state={'allocations': [a.serialize() for a in created_allocations]},
            ip_address=ip_address,
            user_agent=user_agent
        )
        return created_allocations
