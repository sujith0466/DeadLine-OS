"""
DeadlineOS Business OS — Invoice Service
========================================
Manages invoice lifecycle, line items, sequential invoice numbering,
issuance freezes, voiding rules, and settlement balance synchronization.
"""

from database.db import db
from datetime import datetime, timezone, date
from decimal import Decimal
from models.business import Invoice, InvoiceLineItem, CommercialPartner, PaymentAllocation
from services.business.audit_service import AuditService
from services.business.normalizer_service import NormalizerService
from utils.errors import APIError
import uuid


class InvoiceService:
    @staticmethod
    def generate_invoice_number(workspace_id: str) -> str:
        current_year = date.today().year
        prefix = f"INV-{current_year}-"
        last_inv = Invoice.query.filter(
            Invoice.workspace_id == workspace_id,
            Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(Invoice.created_at.desc()).first()

        next_seq = 1
        if last_inv:
            try:
                last_seq = int(last_inv.invoice_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                pass
        return f"{prefix}{next_seq:04d}"

    @staticmethod
    def create_invoice(
        workspace_id: str,
        user_id: str,
        data: dict,
        staged_extraction_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Invoice:
        partner_id = data.get('partner_id')
        if partner_id:
            partner = CommercialPartner.query.filter_by(id=partner_id, workspace_id=workspace_id).first()
            if not partner:
                raise APIError("Commercial partner not found.", code="PARTNER_NOT_FOUND", status=404)

        invoice_type = str(data.get('invoice_type', 'RECEIVABLE')).upper()
        issue_date_str = NormalizerService.normalize_date(data.get('issue_date', date.today()))
        due_date_str = NormalizerService.normalize_date(data.get('due_date', date.today()))
        currency = NormalizerService.normalize_currency(data.get('currency', 'INR'))

        # Line items & Subtotal calculation
        items_data = data.get('items', [])
        subtotal_dec = Decimal('0.00')
        line_item_objects = []

        if items_data:
            for item in items_data:
                desc = item.get('description', 'Item')
                qty = Decimal(str(item.get('quantity', '1.00')))
                uprice = Decimal(str(item.get('unit_price', '0.00')))
                amt = qty * uprice
                subtotal_dec += amt
                line_item_objects.append({
                    'description': desc,
                    'quantity': qty,
                    'unit_price': uprice,
                    'amount': amt
                })
        else:
            raw_subtotal = data.get('subtotal', data.get('total_amount', '0.00'))
            subtotal_dec = Decimal(NormalizerService.normalize_amount(raw_subtotal))

        tax_dec = Decimal(NormalizerService.normalize_amount(data.get('tax_amount', '0.00')))
        disc_dec = Decimal(NormalizerService.normalize_amount(data.get('discount_amount', '0.00')))

        if disc_dec > (subtotal_dec + tax_dec):
            raise APIError("Discount amount cannot exceed subtotal + tax amount.", code="INVALID_DISCOUNT", status=400)

        total_dec = subtotal_dec + tax_dec - disc_dec
        if total_dec < 0:
            raise APIError("Total amount cannot be negative.", code="INVALID_AMOUNT", status=400)

        inv_number = data.get('invoice_number') or InvoiceService.generate_invoice_number(workspace_id)

        # Check invoice_number uniqueness within workspace
        existing = Invoice.query.filter_by(workspace_id=workspace_id, invoice_number=inv_number).first()
        if existing:
            raise APIError(f"Invoice number '{inv_number}' already exists in this workspace.", code="DUPLICATE_INVOICE_NUMBER", status=409)

        invoice_id = str(uuid.uuid4())
        invoice = Invoice(
            id=invoice_id,
            workspace_id=workspace_id,
            invoice_number=inv_number,
            invoice_type=invoice_type,
            partner_id=partner_id,
            issue_date=datetime.strptime(issue_date_str, '%Y-%m-%d').date(),
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date(),
            currency=currency,
            subtotal=subtotal_dec,
            tax_amount=tax_dec,
            discount_amount=disc_dec,
            total_amount=total_dec,
            paid_amount=Decimal('0.00'),
            balance_due=total_dec,
            status='DRAFT',
            notes=data.get('notes'),
            created_by_user_id=user_id,
            staged_extraction_id=staged_extraction_id
        )
        db.session.add(invoice)

        for lio in line_item_objects:
            li = InvoiceLineItem(
                invoice_id=invoice_id,
                workspace_id=workspace_id,
                description=lio['description'],
                quantity=lio['quantity'],
                unit_price=lio['unit_price'],
                amount=lio['amount']
            )
            db.session.add(li)

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='INVOICE_CREATED',
            entity_type='INVOICE',
            entity_id=invoice.id,
            after_state=invoice.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return invoice

    @staticmethod
    def issue_invoice(
        workspace_id: str,
        invoice_id: str,
        user_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Invoice:
        invoice = Invoice.query.filter_by(id=invoice_id, workspace_id=workspace_id).first()
        if not invoice:
            raise APIError("Invoice not found.", code="INVOICE_NOT_FOUND", status=404)
        if invoice.status != 'DRAFT':
            raise APIError(f"Cannot issue invoice with status '{invoice.status}'. Only DRAFT can be issued.", code="INVALID_STATE_TRANSITION", status=400)

        before_state = invoice.serialize()
        invoice.status = 'ISSUED'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='INVOICE_ISSUED',
            entity_type='INVOICE',
            entity_id=invoice.id,
            before_state=before_state,
            after_state=invoice.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return invoice

    @staticmethod
    def void_invoice(
        workspace_id: str,
        invoice_id: str,
        user_id: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Invoice:
        invoice = Invoice.query.filter_by(id=invoice_id, workspace_id=workspace_id).first()
        if not invoice:
            raise APIError("Invoice not found.", code="INVOICE_NOT_FOUND", status=404)
        if invoice.status in ('PAID', 'VOID'):
            raise APIError(f"Cannot void invoice in status '{invoice.status}'.", code="INVALID_STATE_TRANSITION", status=400)
        if invoice.paid_amount > Decimal('0.00'):
            raise APIError("Cannot void an invoice that has active payment allocations. Reverse payments first.", code="INVOICE_HAS_PAYMENTS", status=400)

        before_state = invoice.serialize()
        invoice.status = 'VOID'
        invoice.balance_due = Decimal('0.00')
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='INVOICE_VOIDED',
            entity_type='INVOICE',
            entity_id=invoice.id,
            before_state=before_state,
            after_state=invoice.serialize(),
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return invoice

    @staticmethod
    def recalculate_invoice_balance(workspace_id: str, invoice_id: str) -> Invoice:
        invoice = Invoice.query.filter_by(id=invoice_id, workspace_id=workspace_id).first()
        if not invoice or invoice.status == 'VOID':
            return invoice

        allocations = PaymentAllocation.query.filter_by(
            invoice_id=invoice.id,
            status='ACTIVE'
        ).all()

        total_paid = sum((Decimal(str(a.allocated_amount)) for a in allocations), Decimal('0.00'))
        invoice.paid_amount = total_paid
        invoice.balance_due = invoice.total_amount - total_paid

        if invoice.status != 'DRAFT':
            if invoice.balance_due <= Decimal('0.00'):
                invoice.status = 'PAID'
            elif invoice.paid_amount > Decimal('0.00'):
                invoice.status = 'PARTIALLY_PAID'
            elif date.today() > invoice.due_date:
                invoice.status = 'OVERDUE'
            else:
                invoice.status = 'ISSUED'

        db.session.commit()
        return invoice

    @staticmethod
    def get_invoices(
        workspace_id: str,
        status: str = None,
        invoice_type: str = None,
        partner_id: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = Invoice.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter_by(status=status.upper())
        if invoice_type:
            query = query.filter_by(invoice_type=invoice_type.upper())
        if partner_id:
            query = query.filter_by(partner_id=partner_id)

        total = query.count()
        invoices = query.order_by(Invoice.issue_date.desc()).offset(offset).limit(limit).all()
        return [inv.serialize() for inv in invoices], total

    @staticmethod
    def get_invoice_by_id(workspace_id: str, invoice_id: str) -> Invoice:
        invoice = Invoice.query.filter_by(id=invoice_id, workspace_id=workspace_id).first()
        if not invoice:
            raise APIError("Invoice not found.", code="INVOICE_NOT_FOUND", status=404)
        return invoice
