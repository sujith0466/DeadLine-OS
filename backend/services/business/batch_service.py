"""
DeadlineOS Business OS — Batch, Lot & Expiry Lifecycle Service
==============================================================
Authoritative service for batch master management, deterministic expiry evaluation,
quarantine isolation, FEFO advisory allocation, and movement-to-batch attribution.
"""

import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, InvalidOperation
from sqlalchemy import func, case
from database.db import db
from models.business import (
    Workspace,
    BusinessBatch,
    BusinessStockMovementBatch,
    BusinessStockMovement,
    BusinessProduct,
    CommercialPartner,
    BusinessGoodsReceipt
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class BatchService:
    """
    Core domain service managing product batches, lot provenance, expiry lifecycle,
    and authoritative stock movement attributions.
    """

    DEFAULT_WARNING_HORIZON_DAYS = 30

    @classmethod
    def get_batch_available_stock(cls, workspace_id: str, batch_id: str) -> Decimal:
        """
        Dynamically calculates the available quantity of a batch by querying
        the authoritative stock movement ledger.
        NEVER reads or writes a mutable balance column.
        Formula: SUM(IN batch attributions) - SUM(OUT batch attributions)
        """
        result = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (BusinessStockMovement.direction == 'IN', BusinessStockMovementBatch.quantity),
                        (BusinessStockMovement.direction == 'OUT', -BusinessStockMovementBatch.quantity),
                        else_=Decimal('0.00')
                    )
                ),
                Decimal('0.00')
            )
        ).join(
            BusinessStockMovement,
            BusinessStockMovementBatch.stock_movement_id == BusinessStockMovement.id
        ).filter(
            BusinessStockMovementBatch.workspace_id == workspace_id,
            BusinessStockMovementBatch.batch_id == batch_id
        ).scalar()

        return Decimal(str(result or '0.00')).quantize(Decimal('0.01'))

    @classmethod
    def create_batch(cls, workspace_id: str, actor_user_id: str, data: dict) -> BusinessBatch:
        """
        Creates a new product batch with workspace isolation and uniqueness verification.
        """
        batch_number = (data.get('batch_number') or '').strip()
        if not batch_number:
            raise APIError("Batch number is required.", code="MISSING_BATCH_NUMBER", status=400)

        product_id = data.get('product_id')
        if not product_id:
            raise APIError("Product ID is required.", code="MISSING_PRODUCT_ID", status=400)

        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
        if not product:
            raise APIError("Product not found in this workspace.", code="PRODUCT_NOT_FOUND", status=404)

        # Uniqueness check: (workspace_id, product_id, batch_number)
        existing = BusinessBatch.query.filter_by(
            workspace_id=workspace_id,
            product_id=product_id,
            batch_number=batch_number
        ).first()
        if existing:
            raise APIError(
                f"Batch '{batch_number}' already exists for product '{product.sku}'.",
                code="DUPLICATE_BATCH",
                status=400
            )

        # Parse dates
        mfg_date = None
        if data.get('manufacture_date'):
            try:
                mfg_date = datetime.strptime(str(data['manufacture_date']).split('T')[0], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                raise APIError("Invalid manufacture_date format. Expected YYYY-MM-DD.", code="INVALID_DATE", status=400)

        exp_date = None
        if data.get('expiry_date'):
            try:
                exp_date = datetime.strptime(str(data['expiry_date']).split('T')[0], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                raise APIError("Invalid expiry_date format. Expected YYYY-MM-DD.", code="INVALID_DATE", status=400)

        if mfg_date and exp_date and exp_date < mfg_date:
            raise APIError("Expiry date cannot precede manufacture date.", code="INVALID_EXPIRY_DATE", status=400)

        supplier_partner_id = data.get('supplier_partner_id')
        if supplier_partner_id:
            supplier = CommercialPartner.query.filter_by(id=supplier_partner_id, workspace_id=workspace_id).first()
            if not supplier:
                raise APIError("Supplier partner not found.", code="SUPPLIER_NOT_FOUND", status=404)

        goods_receipt_id = data.get('goods_receipt_id')
        if goods_receipt_id:
            grn = BusinessGoodsReceipt.query.filter_by(id=goods_receipt_id, workspace_id=workspace_id).first()
            if not grn:
                raise APIError("Goods receipt not found.", code="GRN_NOT_FOUND", status=404)

        batch = BusinessBatch(
            workspace_id=workspace_id,
            product_id=product_id,
            batch_number=batch_number,
            supplier_partner_id=supplier_partner_id,
            goods_receipt_id=goods_receipt_id,
            manufacture_date=mfg_date,
            expiry_date=exp_date,
            status='ACTIVE',
            notes=data.get('notes')
        )
        db.session.add(batch)
        db.session.flush()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='BATCH_CREATED',
            entity_type='BUSINESS_BATCH',
            entity_id=batch.id,
            after_state={
                'batch_number': batch.batch_number,
                'product_id': batch.product_id,
                'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None,
                'manufacture_date': batch.manufacture_date.isoformat() if batch.manufacture_date else None
            }
        )
        db.session.commit()
        return batch

    @classmethod
    def get_or_create_batch(
        cls,
        workspace_id: str,
        product_id: str,
        batch_number: str,
        actor_user_id: str = None,
        supplier_partner_id: str = None,
        goods_receipt_id: str = None,
        manufacture_date: date = None,
        expiry_date: date = None,
        notes: str = None
    ) -> BusinessBatch:
        """
        Retrieves an existing batch or automatically creates one during receipt / ingestion workflows.
        """
        batch_number = (batch_number or '').strip()
        if not batch_number:
            raise APIError("Batch number is required.", code="MISSING_BATCH_NUMBER", status=400)

        batch = BusinessBatch.query.filter_by(
            workspace_id=workspace_id,
            product_id=product_id,
            batch_number=batch_number
        ).first()

        if batch:
            # Update dates or references if newly supplied and currently empty
            updated = False
            if expiry_date and not batch.expiry_date:
                batch.expiry_date = expiry_date
                updated = True
            if manufacture_date and not batch.manufacture_date:
                batch.manufacture_date = manufacture_date
                updated = True
            if goods_receipt_id and not batch.goods_receipt_id:
                batch.goods_receipt_id = goods_receipt_id
                updated = True
            if updated:
                db.session.flush()
            return batch

        batch = BusinessBatch(
            workspace_id=workspace_id,
            product_id=product_id,
            batch_number=batch_number,
            supplier_partner_id=supplier_partner_id,
            goods_receipt_id=goods_receipt_id,
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
            status='ACTIVE',
            notes=notes
        )
        db.session.add(batch)
        db.session.flush()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='BATCH_CREATED',
            entity_type='BUSINESS_BATCH',
            entity_id=batch.id,
            after_state={
                'batch_number': batch.batch_number,
                'product_id': batch.product_id,
                'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None,
                'source': 'AUTO_CREATED_GRN' if goods_receipt_id else 'AUTO_CREATED'
            }
        )
        return batch

    @classmethod
    def get_batch(cls, workspace_id: str, batch_id: str) -> dict:
        """
        Fetches a batch with calculated stock and derived lifecycle status.
        """
        batch = BusinessBatch.query.filter_by(id=batch_id, workspace_id=workspace_id).first()
        if not batch:
            raise APIError("Batch not found in this workspace.", code="BATCH_NOT_FOUND", status=404)

        avail_stock = cls.get_batch_available_stock(workspace_id, batch.id)
        return batch.serialize(available_quantity=avail_stock)

    @classmethod
    def list_batches(
        cls,
        workspace_id: str,
        product_id: str = None,
        status: str = None,
        expiring_soon_days: int = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Lists batches with filtering, search, dynamic stock calculation, and pagination.
        """
        query = BusinessBatch.query.filter_by(workspace_id=workspace_id)

        if product_id:
            query = query.filter(BusinessBatch.product_id == product_id)

        if status:
            status_upper = status.upper()
            if status_upper in ('ACTIVE', 'QUARANTINED', 'EXHAUSTED'):
                query = query.filter(BusinessBatch.status == status_upper)
            elif status_upper == 'EXPIRED':
                today = datetime.now(timezone.utc).date()
                query = query.filter(BusinessBatch.expiry_date != None, BusinessBatch.expiry_date < today)
            elif status_upper == 'EXPIRING_SOON':
                today = datetime.now(timezone.utc).date()
                horizon = today + timedelta(days=expiring_soon_days or cls.DEFAULT_WARNING_HORIZON_DAYS)
                query = query.filter(
                    BusinessBatch.status == 'ACTIVE',
                    BusinessBatch.expiry_date != None,
                    BusinessBatch.expiry_date >= today,
                    BusinessBatch.expiry_date <= horizon
                )

        if search:
            query = query.filter(BusinessBatch.batch_number.ilike(f"%{search}%"))

        total_count = query.count()
        batches = query.order_by(BusinessBatch.expiry_date.asc().nullslast(), BusinessBatch.created_at.desc()).offset(offset).limit(limit).all()

        serialized = []
        for b in batches:
            avail = cls.get_batch_available_stock(workspace_id, b.id)
            serialized.append(b.serialize(available_quantity=avail))

        return {
            'batches': serialized,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }

    @classmethod
    def quarantine_batch(cls, workspace_id: str, batch_id: str, actor_user_id: str, reason: str) -> dict:
        """
        Places a batch into QUARANTINED state. Quarantined batches cannot participate in normal sales/dispatches.
        """
        batch = BusinessBatch.query.filter_by(id=batch_id, workspace_id=workspace_id).first()
        if not batch:
            raise APIError("Batch not found in this workspace.", code="BATCH_NOT_FOUND", status=404)

        if not reason or not reason.strip():
            raise APIError("Quarantine reason is required.", code="MISSING_QUARANTINE_REASON", status=400)

        batch.status = 'QUARANTINED'
        batch.quarantine_reason = reason.strip()
        batch.updated_at = datetime.now(timezone.utc)

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='BATCH_QUARANTINED',
            entity_type='BUSINESS_BATCH',
            entity_id=batch.id,
            after_state={
                'batch_number': batch.batch_number,
                'product_id': batch.product_id,
                'reason': batch.quarantine_reason
            }
        )
        db.session.commit()
        avail = cls.get_batch_available_stock(workspace_id, batch.id)
        return batch.serialize(available_quantity=avail)

    @classmethod
    def release_quarantine(cls, workspace_id: str, batch_id: str, actor_user_id: str, release_notes: str = None) -> dict:
        """
        Releases a batch from QUARANTINE back to ACTIVE state.
        """
        batch = BusinessBatch.query.filter_by(id=batch_id, workspace_id=workspace_id).first()
        if not batch:
            raise APIError("Batch not found in this workspace.", code="BATCH_NOT_FOUND", status=404)

        if batch.status != 'QUARANTINED':
            raise APIError("Batch is not currently quarantined.", code="NOT_QUARANTINED", status=400)

        batch.status = 'ACTIVE'
        prior_reason = batch.quarantine_reason
        batch.quarantine_reason = None
        batch.updated_at = datetime.now(timezone.utc)

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='BATCH_RELEASED',
            entity_type='BUSINESS_BATCH',
            entity_id=batch.id,
            after_state={
                'batch_number': batch.batch_number,
                'product_id': batch.product_id,
                'prior_quarantine_reason': prior_reason,
                'release_notes': release_notes
            }
        )
        db.session.commit()
        avail = cls.get_batch_available_stock(workspace_id, batch.id)
        return batch.serialize(available_quantity=avail)

    @classmethod
    def get_fefo_allocation(
        cls,
        workspace_id: str,
        product_id: str,
        requested_quantity: Decimal = None
    ) -> dict:
        """
        Advisory FEFO (First-Expired, First-Out) Engine:
        Sorts active, non-quarantined, non-expired batches by earliest expiry_date ASC, created_at ASC.
        Provides deterministic batch allocation suggestions to fulfill the requested quantity.
        """
        today = datetime.now(timezone.utc).date()
        batches = BusinessBatch.query.filter(
            BusinessBatch.workspace_id == workspace_id,
            BusinessBatch.product_id == product_id,
            BusinessBatch.status == 'ACTIVE',
            db.or_(BusinessBatch.expiry_date == None, BusinessBatch.expiry_date >= today)
        ).order_by(
            BusinessBatch.expiry_date.asc().nullslast(),
            BusinessBatch.created_at.asc()
        ).all()

        allocations = []
        remaining_needed = requested_quantity if requested_quantity is not None else Decimal('0.00')

        for b in batches:
            avail = cls.get_batch_available_stock(workspace_id, b.id)
            if avail <= Decimal('0.00'):
                continue

            allocated_qty = Decimal('0.00')
            if requested_quantity is not None:
                if remaining_needed > Decimal('0.00'):
                    allocated_qty = min(avail, remaining_needed)
                    remaining_needed -= allocated_qty

            allocations.append({
                'batch_id': b.id,
                'batch_number': b.batch_number,
                'expiry_date': b.expiry_date.isoformat() if b.expiry_date else None,
                'available_quantity': str(avail),
                'suggested_allocation': str(allocated_qty) if requested_quantity is not None else None
            })

        fulfilled = (remaining_needed == Decimal('0.00')) if requested_quantity is not None else True
        shortfall = remaining_needed if requested_quantity is not None else Decimal('0.00')

        return {
            'product_id': product_id,
            'requested_quantity': str(requested_quantity) if requested_quantity is not None else None,
            'fulfilled': fulfilled,
            'shortfall': str(shortfall),
            'allocations': allocations
        }

    @classmethod
    def validate_and_attribute_movement(
        cls,
        workspace_id: str,
        movement: BusinessStockMovement,
        attributions: list,
        actor_user_id: str,
        fefo_override_reason: str = None
    ) -> list:
        """
        Authoritative validation and attribution of stock movement to batches:
        1. Ensures SUM(attribution quantities) == movement.quantity.
        2. Validates batch workspace tenancy and product matching.
        3. For OUT movements:
           - Rejects QUARANTINED batches (BATCH_QUARANTINED).
           - Rejects EXPIRED batches for sale/dispatch (BATCH_EXPIRED).
           - Rejects if attribution quantity > available batch quantity (INSUFFICIENT_BATCH_STOCK).
        4. Inserts BusinessStockMovementBatch records atomically.
        5. Logs FEFO override audit event if user diverged from earliest expiry and provided reason.
        """
        if not attributions or not isinstance(attributions, list):
            raise APIError("Attributions must be a non-empty list of batch allocations.", code="EMPTY_ATTRIBUTIONS", status=400)

        total_attr_qty = Decimal('0.00')
        parsed_attributions = []

        for idx, item in enumerate(attributions):
            batch_id = item.get('batch_id')
            if not batch_id:
                raise APIError(f"Attribution {idx + 1}: batch_id is required.", code="MISSING_BATCH_ID", status=400)

            try:
                qty = Decimal(str(item.get('quantity', 0))).quantize(Decimal('0.01'))
            except (InvalidOperation, TypeError, ValueError):
                raise APIError(f"Attribution {idx + 1}: quantity must be a valid number.", code="INVALID_QUANTITY", status=400)

            if qty <= Decimal('0.00'):
                raise APIError(f"Attribution {idx + 1}: quantity must be strictly greater than zero.", code="INVALID_QUANTITY", status=400)

            total_attr_qty += qty
            parsed_attributions.append({'batch_id': batch_id, 'quantity': qty})

        # CRITICAL INVARIANT: SUM(batch attribution quantities) == stock movement quantity
        movement_qty = Decimal(str(movement.quantity)).quantize(Decimal('0.01'))
        if total_attr_qty != movement_qty:
            raise APIError(
                f"Total batch attribution quantity ({total_attr_qty}) does not equal stock movement quantity ({movement_qty}).",
                code="BATCH_QUANTITY_MISMATCH",
                status=400
            )

        today = datetime.now(timezone.utc).date()
        created_records = []

        for p_attr in parsed_attributions:
            batch = BusinessBatch.query.filter_by(id=p_attr['batch_id'], workspace_id=workspace_id).first()
            if not batch:
                raise APIError(f"Batch with ID '{p_attr['batch_id']}' not found in this workspace.", code="BATCH_NOT_FOUND", status=404)

            if batch.product_id != movement.product_id:
                raise APIError(
                    f"Batch '{batch.batch_number}' belongs to a different product than the movement.",
                    code="BATCH_PRODUCT_MISMATCH",
                    status=400
                )

            if movement.direction == 'OUT':
                # Safety check 1: Quarantine
                if batch.status == 'QUARANTINED':
                    raise APIError(
                        f"Cannot dispatch from quarantined batch '{batch.batch_number}'. Reason: {batch.quarantine_reason or 'None'}",
                        code="BATCH_QUARANTINED",
                        status=400
                    )

                # Safety check 2: Expiry (SALE / TRANSFER dispatch cannot use expired stock)
                if movement.movement_type in ('SALE', 'TRANSFER_OUT', 'MANUAL_ADJUSTMENT'):
                    if batch.expiry_date and today > batch.expiry_date:
                        raise APIError(
                            f"Cannot dispatch from expired batch '{batch.batch_number}' (Expired on {batch.expiry_date}).",
                            code="BATCH_EXPIRED",
                            status=400
                        )

                # Safety check 3: Available batch stock
                avail_batch_stock = cls.get_batch_available_stock(workspace_id, batch.id)
                if p_attr['quantity'] > avail_batch_stock:
                    raise APIError(
                        f"Insufficient stock in batch '{batch.batch_number}'. Available: {avail_batch_stock}, Requested: {p_attr['quantity']}.",
                        code="INSUFFICIENT_BATCH_STOCK",
                        status=400
                    )

            sm_batch = BusinessStockMovementBatch(
                workspace_id=workspace_id,
                stock_movement_id=movement.id,
                batch_id=batch.id,
                quantity=p_attr['quantity']
            )
            db.session.add(sm_batch)
            created_records.append(sm_batch)

        # Audit FEFO override if an override reason was supplied
        if fefo_override_reason:
            AuditService.log_event(
                workspace_id=workspace_id,
                actor_user_id=actor_user_id,
                action='FEFO_OVERRIDE_RECORDED',
                entity_type='BUSINESS_STOCK_MOVEMENT',
                entity_id=movement.id,
                after_state={
                    'movement_id': movement.id,
                    'override_reason': fefo_override_reason,
                    'allocated_batches': [p['batch_id'] for p in parsed_attributions]
                }
            )

        db.session.flush()
        return created_records
