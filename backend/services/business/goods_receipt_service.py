"""
DeadlineOS Business OS — Goods Receipt Service (Phase C2.2)
============================================================
Encapsulates all business logic for physical goods arrival, quality inspection,
accepted vs rejected quantities, atomic inventory ledger posting, PO lifecycle synchronization,
and staging trust boundary bridging for Accounts Payable candidate generation.
"""

from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation
from database.db import db
from models.business import (
    Workspace,
    CommercialPartner,
    BusinessLocation,
    BusinessProduct,
    BusinessStockMovement,
    BusinessPurchaseOrder,
    BusinessPurchaseOrderLine,
    BusinessGoodsReceipt,
    BusinessGoodsReceiptLine,
    StagedExtraction,
    AuditEvent
)
from utils.errors import APIError
from services.business.batch_service import BatchService
from services.business.serial_service import SerialService
from models.business import BusinessStockMovementBatch, BusinessStockMovementSerial


class GoodsReceiptService:
    """
    Manages physical goods receiving, inspection, inventory movement creation,
    and AP staging extraction generation.
    """

    @staticmethod
    def _generate_grn_number(workspace_id: str) -> str:
        """
        Generates the next sequential Goods Receipt Note number in the format:
        GRN-{YYYY}-{SEQUENCE:04d} scoped to the workspace.
        """
        current_year = date.today().year
        prefix = f"GRN-{current_year}-"

        # Count existing GRNs for this workspace and year to determine sequence
        existing_count = BusinessGoodsReceipt.query.filter(
            BusinessGoodsReceipt.workspace_id == workspace_id,
            BusinessGoodsReceipt.grn_number.like(f"{prefix}%")
        ).count()

        sequence = existing_count + 1
        grn_number = f"{prefix}{sequence:04d}"

        # Collision safety check
        while BusinessGoodsReceipt.query.filter_by(workspace_id=workspace_id, grn_number=grn_number).first():
            sequence += 1
            grn_number = f"{prefix}{sequence:04d}"

        return grn_number

    @classmethod
    def create_goods_receipt(
        cls,
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessGoodsReceipt:
        """
        Executes atomic physical goods receiving:
        1. Validates PO status and receiving lines.
        2. Creates BusinessGoodsReceipt and BusinessGoodsReceiptLine items.
        3. Inserts BusinessStockMovement records for accepted_quantity > 0.
        4. Updates BusinessPurchaseOrderLine received_quantity and status.
        5. Updates BusinessPurchaseOrder header status.
        6. Inserts StagedExtraction candidate for AP review.
        7. Emits forensic AuditEvents.
        """
        # 1. Validate Workspace
        ws = db.session.get(Workspace, workspace_id)
        if not ws or ws.status != 'ACTIVE':
            raise APIError("Active workspace required for goods receiving.", code="INVALID_WORKSPACE", status=400)

        # 2. Validate Purchase Order
        po_id = data.get('purchase_order_id')
        if not po_id:
            raise APIError("Purchase order ID is required.", code="MISSING_PURCHASE_ORDER", status=400)

        po = BusinessPurchaseOrder.query.filter_by(id=po_id, workspace_id=workspace_id).first()
        if not po:
            raise APIError("Purchase order not found in workspace.", code="NOT_FOUND", status=404)

        allowed_po_statuses = {'APPROVED', 'SENT_TO_SUPPLIER', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED'}
        if po.status not in allowed_po_statuses:
            raise APIError(
                f"Cannot receive goods against Purchase Order with status '{po.status}'. Must be approved or in-transit.",
                code="INVALID_PO_STATUS",
                status=400
            )

        # 3. Validate Lines
        raw_lines = data.get('lines', [])
        if not raw_lines or not isinstance(raw_lines, list):
            raise APIError("At least one goods receipt line item is required.", code="EMPTY_RECEIPT_LINES", status=400)

        po_lines_by_id = {line.id: line for line in po.lines}
        processed_lines = []
        has_discrepancy = False
        total_accepted_value = Decimal('0.00')

        for idx, raw_line in enumerate(raw_lines):
            pol_id = raw_line.get('purchase_order_line_id')
            if not pol_id or pol_id not in po_lines_by_id:
                raise APIError(f"Line {idx + 1}: Invalid or missing purchase_order_line_id for PO {po.po_number}.", code="INVALID_PO_LINE", status=400)

            pol = po_lines_by_id[pol_id]

            try:
                recv_qty = Decimal(str(raw_line.get('received_quantity', 0)))
                acc_qty = Decimal(str(raw_line.get('accepted_quantity', 0)))
                rej_qty = Decimal(str(raw_line.get('rejected_quantity', 0)))
            except (InvalidOperation, TypeError, ValueError):
                raise APIError(f"Line {idx + 1}: Quantities must be valid decimal numbers.", code="INVALID_QUANTITY", status=400)

            if recv_qty < Decimal('0.00') or acc_qty < Decimal('0.00') or rej_qty < Decimal('0.00'):
                raise APIError(f"Line {idx + 1}: Quantities cannot be negative.", code="NEGATIVE_QUANTITY", status=400)

            if recv_qty == Decimal('0.00'):
                continue  # Skip zero-received lines

            # Mathematical invariant: received == accepted + rejected
            if (acc_qty + rej_qty) != recv_qty:
                raise APIError(
                    f"Line {idx + 1}: Received quantity ({recv_qty}) must equal Accepted ({acc_qty}) + Rejected ({rej_qty}).",
                    code="QUANTITY_MISMATCH",
                    status=400
                )

            # Rejection reason validation
            rej_reason = raw_line.get('rejection_reason')
            if rej_qty > Decimal('0.00'):
                has_discrepancy = True

            # Over-receiving detection
            remaining_ordered = pol.ordered_quantity - pol.received_quantity
            if acc_qty > remaining_ordered:
                has_discrepancy = True

            line_value = acc_qty * pol.unit_price
            total_accepted_value += line_value

            exp_d = None
            if raw_line.get('expiry_date'):
                try:
                    exp_d = datetime.strptime(str(raw_line['expiry_date']).split('T')[0], '%Y-%m-%d').date()
                except Exception:
                    pass
            mfg_d = None
            if raw_line.get('manufacture_date'):
                try:
                    mfg_d = datetime.strptime(str(raw_line['manufacture_date']).split('T')[0], '%Y-%m-%d').date()
                except Exception:
                    pass

            raw_serials = raw_line.get('serial_numbers') or raw_line.get('serials') or []
            cleaned_serials = [str(s).strip() for s in raw_serials if str(s).strip()]
            if pol.product.is_serialized and acc_qty > Decimal('0.00') and not cleaned_serials:
                raise APIError(
                    f"Line {idx + 1}: Product '{pol.product.sku}' is serialized. Serial numbers must be provided for accepted quantity ({acc_qty}).",
                    code="SERIALS_REQUIRED",
                    status=400
                )
            if cleaned_serials:
                if acc_qty % 1 != Decimal('0'):
                    raise APIError(
                        f"Line {idx + 1}: Serialized accepted quantity must be an integer, got {acc_qty}.",
                        code="INVALID_SERIAL_QUANTITY",
                        status=400
                    )
                if len(cleaned_serials) != int(acc_qty):
                    raise APIError(
                        f"Line {idx + 1}: Serial count ({len(cleaned_serials)}) must equal accepted quantity ({int(acc_qty)}).",
                        code="SERIAL_COUNT_MISMATCH",
                        status=400
                    )
                if len(set(cleaned_serials)) != len(cleaned_serials):
                    raise APIError(
                        f"Line {idx + 1}: Duplicate serial numbers detected in input payload.",
                        code="DUPLICATE_SERIAL_IN_PAYLOAD",
                        status=400
                    )

            processed_lines.append({
                'pol': pol,
                'received_qty': recv_qty,
                'accepted_qty': acc_qty,
                'rejected_qty': rej_qty,
                'rejection_reason': rej_reason,
                'unit_cost': pol.unit_price,
                'batch_number': (raw_line.get('batch_number') or '').strip() or None,
                'expiry_date': exp_d,
                'manufacture_date': mfg_d,
                'serial_numbers': cleaned_serials or None,
            })

        if not processed_lines:
            raise APIError("Goods receipt must have at least one non-zero receiving line.", code="ZERO_RECEIPT_ITEMS", status=400)

        # 4. Generate GRN Header
        grn_number = cls._generate_grn_number(workspace_id)
        receipt_date = data.get('receipt_date')
        if receipt_date:
            try:
                receipt_date = datetime.strptime(receipt_date, '%Y-%m-%d').date()
            except ValueError:
                receipt_date = datetime.now(timezone.utc).date()
        else:
            receipt_date = datetime.now(timezone.utc).date()

        grn = BusinessGoodsReceipt(
            workspace_id=workspace_id,
            grn_number=grn_number,
            purchase_order_id=po.id,
            supplier_partner_id=po.supplier_partner_id,
            destination_location_id=po.destination_location_id,
            receipt_date=receipt_date,
            carrier_name=data.get('carrier_name'),
            tracking_number=data.get('tracking_number'),
            delivery_note_number=data.get('delivery_note_number'),
            status='COMPLETED',
            notes=data.get('notes'),
            received_by_user_id=actor_user_id,
        )
        db.session.add(grn)
        db.session.flush()

        # 5. Process Lines & Create Atomic Stock Movements
        staged_line_payloads = []

        for p_line in processed_lines:
            pol = p_line['pol']
            acc_qty = p_line['accepted_qty']
            stock_mv_id = None

            # Create immutable stock movement for accepted physical inventory only
            if acc_qty > Decimal('0.00'):
                stock_mv = BusinessStockMovement(
                    workspace_id=workspace_id,
                    product_id=pol.product_id,
                    location_id=po.destination_location_id,
                    movement_type='PURCHASE_RECEIVED',
                    direction='IN',
                    quantity=acc_qty,
                    unit_cost=pol.unit_price,
                    reference_type='GOODS_RECEIPT',
                    reference_id=grn.id,
                    actor_user_id=actor_user_id,
                    reason=f"GRN {grn_number} received against PO {po.po_number}",
                )
                db.session.add(stock_mv)
                db.session.flush()
                stock_mv_id = stock_mv.id

                # C3.2 Batch attribution if batch_number provided
                if p_line.get('batch_number'):
                    batch = BatchService.get_or_create_batch(
                        workspace_id=workspace_id,
                        product_id=pol.product_id,
                        batch_number=p_line['batch_number'],
                        actor_user_id=actor_user_id,
                        supplier_partner_id=po.supplier_partner_id,
                        goods_receipt_id=grn.id,
                        manufacture_date=p_line.get('manufacture_date'),
                        expiry_date=p_line.get('expiry_date'),
                        notes=f"Auto-created from GRN {grn_number}"
                    )
                    sm_batch = BusinessStockMovementBatch(
                        workspace_id=workspace_id,
                        stock_movement_id=stock_mv.id,
                        batch_id=batch.id,
                        quantity=acc_qty
                    )
                    db.session.add(sm_batch)
                    db.session.flush()

                # C3.3 Serial attribution if serial_numbers provided
                if p_line.get('serial_numbers'):
                    serials = SerialService.register_or_receive_serials(
                        workspace_id=workspace_id,
                        product_id=pol.product_id,
                        serial_numbers=p_line['serial_numbers'],
                        actor_user_id=actor_user_id,
                        location_id=po.destination_location_id,
                        batch_id=batch.id if (p_line.get('batch_number') and 'batch' in locals()) else None,
                        goods_receipt_id=grn.id,
                        notes=f"Auto-received from GRN {grn_number}"
                    )
                    for s_obj in serials:
                        sm_serial = BusinessStockMovementSerial(
                            workspace_id=workspace_id,
                            stock_movement_id=stock_mv.id,
                            serial_id=s_obj.id
                        )
                        db.session.add(sm_serial)
                    db.session.flush()

            # Create GRN line record
            grn_line = BusinessGoodsReceiptLine(
                goods_receipt_id=grn.id,
                purchase_order_line_id=pol.id,
                product_id=pol.product_id,
                received_quantity=p_line['received_qty'],
                accepted_quantity=acc_qty,
                rejected_quantity=p_line['rejected_qty'],
                rejection_reason=p_line['rejection_reason'],
                unit_cost=pol.unit_price,
                stock_movement_id=stock_mv_id,
            )
            db.session.add(grn_line)

            # Update PO line fulfillment status
            pol.received_quantity += acc_qty
            if pol.received_quantity >= pol.ordered_quantity:
                pol.status = 'FULLY_RECEIVED'
            elif pol.received_quantity > Decimal('0.00'):
                pol.status = 'PARTIALLY_RECEIVED'

            staged_line_payloads.append({
                'product_id': pol.product_id,
                'product_name': pol.product.name if pol.product else None,
                'product_sku': pol.product.sku if pol.product else None,
                'accepted_quantity': str(acc_qty),
                'rejected_quantity': str(p_line['rejected_qty']),
                'unit_price': str(pol.unit_price),
                'line_total': str(acc_qty * pol.unit_price),
            })

        # 6. Synchronize PO Header Status
        all_lines_fully_received = all(
            line.received_quantity >= line.ordered_quantity
            for line in po.lines
        )
        any_line_received = any(
            line.received_quantity > Decimal('0.00')
            for line in po.lines
        )

        if all_lines_fully_received:
            po.status = 'FULLY_RECEIVED'
        elif any_line_received:
            po.status = 'PARTIALLY_RECEIVED'

        # 7. Create Accounts Payable Staged Extraction (Staging Trust Boundary)
        staged_extraction = StagedExtraction(
            workspace_id=workspace_id,
            created_by_user_id=actor_user_id,
            source_channel='DOCUMENT_UPLOAD',
            candidate_type='INVOICE_PAYABLE',
            status='NEEDS_REVIEW',
            confidence_score=100,
            normalized_data={
                'partner_id': po.supplier_partner_id,
                'partner_name': po.supplier.name if po.supplier else None,
                'po_id': po.id,
                'po_number': po.po_number,
                'grn_id': grn.id,
                'grn_number': grn.grn_number,
                'receipt_date': grn.receipt_date.isoformat(),
                'total_accepted_amount': str(total_accepted_value),
                'currency': po.currency,
                'delivery_note_number': grn.delivery_note_number,
                'lines': staged_line_payloads,
            },
            provenance_metadata={
                'source': 'GOODS_RECEIPT',
                'grn_id': grn.id,
                'po_id': po.id,
                'created_by': actor_user_id,
            }
        )
        db.session.add(staged_extraction)
        db.session.flush()

        # Link staged extraction to GRN
        grn.staged_extraction_id = staged_extraction.id

        # 8. Emit Forensic Audit Events
        audit_event = AuditEvent(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='GRN_CREATED',
            entity_type='business_goods_receipt',
            entity_id=grn.id,
            after_state=grn.serialize(include_lines=True),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(audit_event)

        if has_discrepancy:
            discrepancy_audit = AuditEvent(
                workspace_id=workspace_id,
                actor_user_id=actor_user_id,
                action='GRN_DISCREPANCY_DETECTED',
                entity_type='business_goods_receipt',
                entity_id=grn.id,
                metadata={
                    'grn_number': grn_number,
                    'po_number': po.po_number,
                    'reason': 'Quality rejections or over-receiving detected on delivery.',
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.session.add(discrepancy_audit)

        db.session.commit()
        return grn

    @classmethod
    def get_goods_receipt_by_id(cls, workspace_id: str, grn_id: str) -> BusinessGoodsReceipt:
        """
        Retrieves a Goods Receipt Note by ID with workspace isolation.
        """
        grn = BusinessGoodsReceipt.query.filter_by(id=grn_id, workspace_id=workspace_id).first()
        if not grn:
            raise APIError("Goods receipt note not found.", code="NOT_FOUND", status=404)
        return grn

    @classmethod
    def list_goods_receipts(
        cls,
        workspace_id: str,
        po_id: str = None,
        supplier_partner_id: str = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[BusinessGoodsReceipt], int]:
        """
        Lists Goods Receipt Notes in a workspace with optional filters.
        """
        query = BusinessGoodsReceipt.query.filter_by(workspace_id=workspace_id)

        if po_id:
            query = query.filter_by(purchase_order_id=po_id)
        if supplier_partner_id:
            query = query.filter_by(supplier_partner_id=supplier_partner_id)
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        items = query.order_by(BusinessGoodsReceipt.created_at.desc()).limit(limit).offset(offset).all()
        return items, total