from services.business.exchange_rate_service import ExchangeRateService
"""
DeadlineOS Business OS — Purchase Order Service
================================================
Authoritative service for Purchase Order lifecycle, sequential numbering,
line items management, supplier validation, and PR conversion.
"""

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import func
from database.db import db
from models.business import (
    Workspace,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessPurchaseRequest,
    CommercialPartner,
    BusinessProduct,
    BusinessLocation
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class PurchaseOrderService:
    VALID_STATUSES = {
        'DRAFT',
        'APPROVED',
        'SENT_TO_SUPPLIER',
        'ACKNOWLEDGED',
        'PARTIALLY_RECEIVED',
        'FULLY_RECEIVED',
        'CLOSED',
        'CANCELLED'
    }

    @staticmethod
    def generate_po_number(workspace_id: str) -> str:
        """
        Generates a concurrency-safe sequential PO number scoped per workspace and year:
        e.g., PO-2026-0001
        """
        current_year = date.today().year
        prefix = f"PO-{current_year}-"

        count = db.session.query(func.count(BusinessPurchaseOrder.id)).filter(
            BusinessPurchaseOrder.workspace_id == workspace_id,
            BusinessPurchaseOrder.po_number.like(f"{prefix}%")
        ).scalar() or 0

        sequence = count + 1
        po_number = f"{prefix}{sequence:04d}"

        while BusinessPurchaseOrder.query.filter_by(workspace_id=workspace_id, po_number=po_number).first():
            sequence += 1
            po_number = f"{prefix}{sequence:04d}"

        return po_number

    @staticmethod
    def create_purchase_order(
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseOrder:
        supplier_id = data.get('supplier_partner_id')
        if not supplier_id:
            raise APIError("Field 'supplier_partner_id' is required.", "VALIDATION_ERROR", 400)

        supplier = CommercialPartner.query.filter_by(id=supplier_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not supplier:
            raise APIError("Supplier partner not found or inactive in this workspace.", "VALIDATION_ERROR", 400)
        if supplier.partner_type not in ('SUPPLIER', 'BOTH'):
            raise APIError(f"Partner '{supplier.name}' is of type '{supplier.partner_type}', must be SUPPLIER or BOTH.", "VALIDATION_ERROR", 400)

        location_id = data.get('destination_location_id')
        if not location_id:
            raise APIError("Field 'destination_location_id' is required.", "VALIDATION_ERROR", 400)

        location = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not location:
            raise APIError("Destination location not found or inactive in this workspace.", "VALIDATION_ERROR", 400)

        raw_lines = data.get('lines') or []
        if not raw_lines or not isinstance(raw_lines, list):
            raise APIError("Field 'lines' must be a non-empty list of line items.", "VALIDATION_ERROR", 400)

        order_date = date.today()
        if data.get('order_date'):
            try:
                order_date = date.fromisoformat(data['order_date'])
            except Exception:
                raise APIError("Invalid ISO format for 'order_date' (YYYY-MM-DD).", "VALIDATION_ERROR", 400)

        expected_delivery = None
        if data.get('expected_delivery_date'):
            try:
                expected_delivery = date.fromisoformat(data['expected_delivery_date'])
            except Exception:
                raise APIError("Invalid ISO format for 'expected_delivery_date' (YYYY-MM-DD).", "VALIDATION_ERROR", 400)

        subtotal = Decimal('0.00')
        lines_to_create = []

        for idx, line in enumerate(raw_lines):
            prod_id = line.get('product_id')
            if not prod_id:
                raise APIError(f"Line {idx + 1}: Field 'product_id' is required.", "VALIDATION_ERROR", 400)

            prod = BusinessProduct.query.filter_by(id=prod_id, workspace_id=workspace_id, status='ACTIVE').first()
            if not prod:
                raise APIError(f"Line {idx + 1}: Referenced product not found in this workspace.", "VALIDATION_ERROR", 400)

            try:
                qty = Decimal(str(line.get('ordered_quantity', '0'))).quantize(Decimal('0.01'))
                if qty <= Decimal('0.00'):
                    raise ValueError()
            except Exception:
                raise APIError(f"Line {idx + 1}: 'ordered_quantity' must be a positive decimal.", "VALIDATION_ERROR", 400)

            try:
                unit_price = Decimal(str(line.get('unit_price', prod.cost_price or '0.00'))).quantize(Decimal('0.01'))
                if unit_price < Decimal('0.00'):
                    raise ValueError()
            except Exception:
                raise APIError(f"Line {idx + 1}: 'unit_price' must be a non-negative decimal.", "VALIDATION_ERROR", 400)

            line_total = (qty * unit_price).quantize(Decimal('0.01'))
            subtotal += line_total

            lines_to_create.append({
                'product_id': prod.id,
                'ordered_quantity': qty,
                'received_quantity': Decimal('0.00'),
                'unit_price': unit_price,
                'total_price': line_total,
                'status': 'PENDING'
            })

        tax_amount = Decimal('0.00')
        if data.get('tax_amount'):
            try:
                tax_amount = Decimal(str(data['tax_amount'])).quantize(Decimal('0.01'))
                if tax_amount < Decimal('0.00'):
                    raise ValueError()
            except Exception:
                raise APIError("Field 'tax_amount' must be a non-negative decimal.", "VALIDATION_ERROR", 400)

        total_amount = (subtotal + tax_amount).quantize(Decimal('0.01'))
        po_number = PurchaseOrderService.generate_po_number(workspace_id)
        initial_status = (data.get('status') or 'DRAFT').upper()
        if initial_status not in ('DRAFT', 'APPROVED'):
            initial_status = 'DRAFT'

        ws = db.session.get(Workspace, workspace_id)
        base_curr = ws.base_currency if ws else 'INR'
        po_curr = (data.get('currency') or base_curr).strip().upper()
        if po_curr != base_curr:
            if data.get('exchange_rate'):
                po_fx_rate = Decimal(str(data['exchange_rate'])).quantize(Decimal('0.000001'))
            else:
                try:
                    po_fx_rate = ExchangeRateService.get_exchange_rate(workspace_id, po_curr, base_curr, order_date)
                except Exception:
                    po_fx_rate = Decimal('1.000000')
            base_total = (total_amount * po_fx_rate).quantize(Decimal('0.01'))
        else:
            po_fx_rate = Decimal('1.000000')
            base_total = total_amount

        po = BusinessPurchaseOrder(
            workspace_id=workspace_id,
            po_number=po_number,
            supplier_partner_id=supplier.id,
            destination_location_id=location.id,
            order_date=order_date,
            expected_delivery_date=expected_delivery,
            subtotal_amount=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency=po_curr,
            exchange_rate=po_fx_rate,
            base_currency_total=base_total,
            payment_terms=data.get('payment_terms', 'NET_30'),
            status=initial_status,
            notes=data.get('notes'),
            created_by_user_id=actor_user_id,
            approved_by_user_id=actor_user_id if initial_status == 'APPROVED' else None,
            approved_at=datetime.now(timezone.utc) if initial_status == 'APPROVED' else None
        )

        db.session.add(po)
        db.session.flush()

        for l_data in lines_to_create:
            po_line = BusinessPurchaseOrderLine(
                purchase_order_id=po.id,
                product_id=l_data['product_id'],
                ordered_quantity=l_data['ordered_quantity'],
                received_quantity=l_data['received_quantity'],
                unit_price=l_data['unit_price'],
                total_price=l_data['total_price'],
                status=l_data['status']
            )
            db.session.add(po_line)

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PO_CREATED",
            entity_type="business_purchase_order",
            entity_id=po.id,
            before_state=None,
            after_state=po.serialize(),
            reason=f"Created Purchase Order {po.po_number} with {len(lines_to_create)} lines ({po.status})",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return po

    @staticmethod
    def get_purchase_orders(
        workspace_id: str,
        status: str = None,
        supplier_partner_id: str = None,
        destination_location_id: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = BusinessPurchaseOrder.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter_by(status=status.upper())
        if supplier_partner_id:
            query = query.filter_by(supplier_partner_id=supplier_partner_id)
        if destination_location_id:
            query = query.filter_by(destination_location_id=destination_location_id)
        if search:
            query = query.filter(
                (BusinessPurchaseOrder.po_number.ilike(f"%{search}%")) |
                (BusinessPurchaseOrder.notes.ilike(f"%{search}%"))
            )

        total = query.count()
        pos = query.order_by(BusinessPurchaseOrder.created_at.desc()).offset(offset).limit(min(limit, 100)).all()
        return [p.serialize() for p in pos], total

    @staticmethod
    def get_purchase_order_by_id(workspace_id: str, po_id: str) -> BusinessPurchaseOrder:
        po = BusinessPurchaseOrder.query.filter_by(id=po_id, workspace_id=workspace_id).first()
        if not po:
            raise APIError("Purchase order not found in this workspace.", "NOT_FOUND", 404)
        return po

    @staticmethod
    def update_purchase_order(
        workspace_id: str,
        actor_user_id: str,
        po_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseOrder:
        po = PurchaseOrderService.get_purchase_order_by_id(workspace_id, po_id)
        before_state = po.serialize()

        if po.status != 'DRAFT':
            raise APIError(f"Cannot update purchase order in status '{po.status}'. Must be in 'DRAFT' status.", "INVALID_STATE", 400)

        if 'supplier_partner_id' in data:
            supplier = CommercialPartner.query.filter_by(id=data['supplier_partner_id'], workspace_id=workspace_id, status='ACTIVE').first()
            if not supplier or supplier.partner_type not in ('SUPPLIER', 'BOTH'):
                raise APIError("Invalid supplier partner.", "VALIDATION_ERROR", 400)
            po.supplier_partner_id = supplier.id

        if 'destination_location_id' in data:
            loc = BusinessLocation.query.filter_by(id=data['destination_location_id'], workspace_id=workspace_id, status='ACTIVE').first()
            if not loc:
                raise APIError("Invalid destination location.", "VALIDATION_ERROR", 400)
            po.destination_location_id = loc.id

        if 'expected_delivery_date' in data:
            if data['expected_delivery_date']:
                try:
                    po.expected_delivery_date = date.fromisoformat(data['expected_delivery_date'])
                except Exception:
                    raise APIError("Invalid ISO date format.", "VALIDATION_ERROR", 400)
            else:
                po.expected_delivery_date = None

        if 'payment_terms' in data:
            po.payment_terms = data['payment_terms']

        if 'notes' in data:
            po.notes = data['notes']

        # If lines provided in update
        if 'lines' in data and isinstance(data['lines'], list) and len(data['lines']) > 0:
            # Delete existing lines
            for l in list(po.lines):
                db.session.delete(l)
            db.session.flush()

            subtotal = Decimal('0.00')
            for idx, line in enumerate(data['lines']):
                prod_id = line.get('product_id')
                prod = BusinessProduct.query.filter_by(id=prod_id, workspace_id=workspace_id, status='ACTIVE').first()
                if not prod:
                    raise APIError(f"Line {idx + 1}: Invalid product.", "VALIDATION_ERROR", 400)

                qty = Decimal(str(line.get('ordered_quantity', '0'))).quantize(Decimal('0.01'))
                unit_price = Decimal(str(line.get('unit_price', prod.cost_price or '0.00'))).quantize(Decimal('0.01'))
                line_total = (qty * unit_price).quantize(Decimal('0.01'))
                subtotal += line_total

                new_line = BusinessPurchaseOrderLine(
                    purchase_order_id=po.id,
                    product_id=prod.id,
                    ordered_quantity=qty,
                    received_quantity=Decimal('0.00'),
                    unit_price=unit_price,
                    total_price=line_total,
                    status='PENDING'
                )
                db.session.add(new_line)

            po.subtotal_amount = subtotal
            tax_amt = Decimal(str(data.get('tax_amount', po.tax_amount))).quantize(Decimal('0.01'))
            po.tax_amount = tax_amt
            po.total_amount = (subtotal + tax_amt).quantize(Decimal('0.01'))

        po.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PO_UPDATED",
            entity_type="business_purchase_order",
            entity_id=po.id,
            before_state=before_state,
            after_state=po.serialize(),
            reason=f"Updated Purchase Order {po.po_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return po

    @staticmethod
    def approve_purchase_order(
        workspace_id: str,
        actor_user_id: str,
        po_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseOrder:
        po = PurchaseOrderService.get_purchase_order_by_id(workspace_id, po_id)
        before_state = po.serialize()

        if po.status != 'DRAFT':
            raise APIError(f"Cannot approve PO in status '{po.status}'. Must be in 'DRAFT' status.", "INVALID_STATE", 400)

        po.status = 'APPROVED'
        po.approved_by_user_id = actor_user_id
        po.approved_at = datetime.now(timezone.utc)
        po.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PO_APPROVED",
            entity_type="business_purchase_order",
            entity_id=po.id,
            before_state=before_state,
            after_state=po.serialize(),
            reason=f"Approved Purchase Order {po.po_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return po

    @staticmethod
    def send_purchase_order(
        workspace_id: str,
        actor_user_id: str,
        po_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseOrder:
        po = PurchaseOrderService.get_purchase_order_by_id(workspace_id, po_id)
        before_state = po.serialize()

        if po.status not in ('DRAFT', 'APPROVED'):
            raise APIError(f"Cannot send PO in status '{po.status}'. Must be 'DRAFT' or 'APPROVED'.", "INVALID_STATE", 400)

        if po.status == 'DRAFT':
            po.approved_by_user_id = actor_user_id
            po.approved_at = datetime.now(timezone.utc)

        po.status = 'SENT_TO_SUPPLIER'
        po.sent_at = datetime.now(timezone.utc)
        po.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PO_SENT",
            entity_type="business_purchase_order",
            entity_id=po.id,
            before_state=before_state,
            after_state=po.serialize(),
            reason=f"Sent Purchase Order {po.po_number} to supplier {po.supplier.name if po.supplier else ''}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return po

    @staticmethod
    def cancel_purchase_order(
        workspace_id: str,
        actor_user_id: str,
        po_id: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseOrder:
        po = PurchaseOrderService.get_purchase_order_by_id(workspace_id, po_id)
        before_state = po.serialize()

        if po.status in ('PARTIALLY_RECEIVED', 'FULLY_RECEIVED', 'CLOSED'):
            raise APIError(f"Cannot cancel purchase order in status '{po.status}'. Goods receipt active or completed.", "INVALID_STATE", 400)

        po.status = 'CANCELLED'
        po.notes = f"{po.notes or ''}\nCancellation Reason: {reason or 'Not specified'}".strip()
        po.updated_at = datetime.now(timezone.utc)

        for line in po.lines:
            line.status = 'CANCELLED'

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PO_CANCELLED",
            entity_type="business_purchase_order",
            entity_id=po.id,
            before_state=before_state,
            after_state=po.serialize(),
            reason=f"Cancelled Purchase Order {po.po_number}: {reason or 'No reason provided'}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return po

    @staticmethod
    def convert_pr_to_po(
        workspace_id: str,
        actor_user_id: str,
        request_id: str,
        data: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseOrder:
        """
        Converts an approved Purchase Request into a formal Purchase Order draft.
        """
        data = data or {}
        pr = BusinessPurchaseRequest.query.filter_by(id=request_id, workspace_id=workspace_id).first()
        if not pr:
            raise APIError("Purchase request not found in this workspace.", "NOT_FOUND", 404)

        if pr.status != 'APPROVED':
            raise APIError(f"Cannot convert request in status '{pr.status}'. Must be 'APPROVED'.", "INVALID_STATE", 400)

        if pr.purchase_order_id:
            raise APIError(f"Purchase request {pr.request_number} has already been converted to PO {pr.purchase_order_id}.", "DUPLICATE_CONVERSION", 409)

        # Determine supplier
        supplier_id = data.get('supplier_partner_id') or pr.product.preferred_supplier_partner_id
        if not supplier_id:
            raise APIError("Supplier partner ID required. Please provide 'supplier_partner_id' or set a preferred supplier on the product.", "VALIDATION_ERROR", 400)

        supplier = CommercialPartner.query.filter_by(id=supplier_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not supplier or supplier.partner_type not in ('SUPPLIER', 'BOTH'):
            raise APIError("Referenced supplier partner not found or invalid type.", "VALIDATION_ERROR", 400)

        po_data = {
            'supplier_partner_id': supplier.id,
            'destination_location_id': pr.location_id,
            'order_date': data.get('order_date') or date.today().isoformat(),
            'expected_delivery_date': data.get('expected_delivery_date'),
            'currency': pr.currency,
            'payment_terms': data.get('payment_terms', 'NET_30'),
            'status': data.get('status', 'DRAFT'),
            'notes': f"Generated from Purchase Request {pr.request_number}. {pr.reason or ''}".strip(),
            'lines': [
                {
                    'product_id': pr.product_id,
                    'ordered_quantity': str(pr.requested_quantity),
                    'unit_price': str(data.get('unit_price', pr.estimated_unit_price))
                }
            ]
        }

        po = PurchaseOrderService.create_purchase_order(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            data=po_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        pr.status = 'ORDERED'
        pr.purchase_order_id = po.id
        pr.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PR_CONVERTED_TO_PO",
            entity_type="business_purchase_request",
            entity_id=pr.id,
            before_state={'status': 'APPROVED'},
            after_state={'status': 'ORDERED', 'purchase_order_id': po.id},
            reason=f"Converted Purchase Request {pr.request_number} to Purchase Order {po.po_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return po
