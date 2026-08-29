"""
DeadlineOS Business OS — Transaction Service
============================================
Manages operational event ledger ingestion and the formal append-only
counter-adjustment reversal protocol.
"""

from database.db import db
from datetime import datetime, timezone, date
from decimal import Decimal
from models.business import BusinessTransaction, CommercialPartner, PaymentAllocation
from services.business.audit_service import AuditService
from services.business.normalizer_service import NormalizerService
from utils.errors import APIError
import uuid


class TransactionService:
    @staticmethod
    def record_transaction(
        workspace_id: str,
        user_id: str,
        data: dict,
        staged_extraction_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessTransaction:
        partner_id = data.get('partner_id')
        if partner_id:
            partner = CommercialPartner.query.filter_by(id=partner_id, workspace_id=workspace_id).first()
            if not partner:
                raise APIError("Commercial partner not found.", code="PARTNER_NOT_FOUND", status=404)

        tx_type = str(data.get('transaction_type', 'EXPENSE')).upper()
        amount_dec = Decimal(NormalizerService.normalize_amount(data.get('amount', '0.00')))
        if amount_dec <= Decimal('0.00'):
            raise APIError("Transaction amount must be strictly greater than 0.", code="INVALID_AMOUNT", status=400)

        currency = NormalizerService.normalize_currency(data.get('currency', 'INR'))
        tx_date_str = NormalizerService.normalize_date(data.get('transaction_date', date.today()))
        settle_date_str = NormalizerService.normalize_date(data.get('settlement_date', tx_date_str)) if data.get('settlement_date') else None

        tx_id = str(uuid.uuid4())
        tx = BusinessTransaction(
            id=tx_id,
            workspace_id=workspace_id,
            transaction_type=tx_type,
            amount=amount_dec,
            currency=currency,
            transaction_date=datetime.strptime(tx_date_str, '%Y-%m-%d').date(),
            settlement_date=datetime.strptime(settle_date_str, '%Y-%m-%d').date() if settle_date_str else None,
            partner_id=partner_id,
            payment_method=data.get('payment_method'),
            reference_number=data.get('reference_number'),
            status='CONFIRMED',
            created_by_user_id=user_id,
            staged_extraction_id=staged_extraction_id,
            notes=data.get('notes')
        )
        db.session.add(tx)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='TRANSACTION_RECORDED',
            entity_type='TRANSACTION',
            entity_id=tx.id,
            after_state=tx.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return tx

    @staticmethod
    def reverse_transaction(
        workspace_id: str,
        transaction_id: str,
        user_id: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessTransaction:
        if not reason or not str(reason).strip():
            raise APIError("A non-empty reason is strictly required to reverse a transaction.", code="REASON_REQUIRED", status=400)

        tx = BusinessTransaction.query.filter_by(id=transaction_id, workspace_id=workspace_id).first()
        if not tx:
            raise APIError("Transaction not found.", code="TRANSACTION_NOT_FOUND", status=404)
        if tx.status != 'CONFIRMED':
            raise APIError(f"Cannot reverse transaction in status '{tx.status}'. Only CONFIRMED transactions can be reversed.", code="INVALID_STATE_TRANSITION", status=400)

        before_state = tx.serialize()

        # 1. Create counter-adjustment transaction
        adj_id = str(uuid.uuid4())
        adj_tx = BusinessTransaction(
            id=adj_id,
            workspace_id=workspace_id,
            transaction_type='ADJUSTMENT',
            amount=-Decimal(str(tx.amount)),
            currency=tx.currency,
            transaction_date=date.today(),
            settlement_date=date.today(),
            partner_id=tx.partner_id,
            status='CONFIRMED',
            reversal_of_transaction_id=tx.id,
            created_by_user_id=user_id,
            notes=f"Counter-adjustment for reversal of {tx.id}: {reason.strip()}"
        )
        db.session.add(adj_tx)

        # 2. Transition original status to REVERSED
        tx.status = 'REVERSED'

        # 3. Reverse linked allocations and restore invoice balances
        linked_allocations = PaymentAllocation.query.filter_by(
            transaction_id=tx.id,
            status='ACTIVE'
        ).all()

        invoices_to_recalc = set()
        for alloc in linked_allocations:
            alloc.status = 'REVERSED'
            invoices_to_recalc.add(alloc.invoice_id)

        db.session.commit()

        # Recalculate affected invoices
        from services.business.invoice_service import InvoiceService
        for inv_id in invoices_to_recalc:
            InvoiceService.recalculate_invoice_balance(workspace_id, inv_id)

        # 4. Log Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='TRANSACTION_REVERSED',
            entity_type='TRANSACTION',
            entity_id=tx.id,
            before_state=before_state,
            after_state=tx.serialize(),
            reason=reason.strip(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return tx

    @staticmethod
    def get_transactions(
        workspace_id: str,
        transaction_type: str = None,
        status: str = None,
        partner_id: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = BusinessTransaction.query.filter_by(workspace_id=workspace_id)
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type.upper())
        if status:
            query = query.filter_by(status=status.upper())
        if partner_id:
            query = query.filter_by(partner_id=partner_id)

        total = query.count()
        txs = query.order_by(BusinessTransaction.transaction_date.desc()).offset(offset).limit(limit).all()
        return [t.serialize() for t in txs], total

    @staticmethod
    def get_transaction_by_id(workspace_id: str, transaction_id: str) -> BusinessTransaction:
        tx = BusinessTransaction.query.filter_by(id=transaction_id, workspace_id=workspace_id).first()
        if not tx:
            raise APIError("Transaction not found.", code="TRANSACTION_NOT_FOUND", status=404)
        return tx
