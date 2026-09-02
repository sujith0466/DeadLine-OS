"""
DeadlineOS Business OS — Serial Number Tracking & Unit Provenance Service
========================================================================
Authoritative service for serial number registration, deterministic lifecycle
transitions, movement attributions, single-location invariant, and provenance tracking.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any

from database.db import db
from models.business import (
    BusinessProduct,
    BusinessLocation,
    BusinessBatch,
    BusinessGoodsReceipt,
    BusinessStockMovement,
    BusinessSerialNumber,
    BusinessStockMovementSerial,
    AuditEvent
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class SerialService:
    """
    Authoritative domain service for serialized product unit-level provenance.
    """

    @classmethod
    def register_or_receive_serials(
        cls,
        workspace_id: str,
        product_id: str,
        serial_numbers: List[str],
        actor_user_id: str,
        location_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        goods_receipt_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> List[BusinessSerialNumber]:
        """
        Registers individual serialized units in IN_STOCK status with workspace and product isolation.
        Rejects duplicates atomically.
        """
        if not serial_numbers:
            raise APIError("Serial numbers list cannot be empty.", code="EMPTY_SERIALS_LIST", status=400)

        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
        if not product:
            raise APIError("Product not found in this workspace.", code="PRODUCT_NOT_FOUND", status=404)

        if location_id:
            loc = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id).first()
            if not loc:
                raise APIError("Location not found in this workspace.", code="LOCATION_NOT_FOUND", status=404)

        if batch_id:
            batch = BusinessBatch.query.filter_by(id=batch_id, workspace_id=workspace_id).first()
            if not batch:
                raise APIError("Batch not found in this workspace.", code="BATCH_NOT_FOUND", status=404)
            if batch.product_id != product_id:
                raise APIError("Batch does not belong to the specified product.", code="BATCH_PRODUCT_MISMATCH", status=400)

        # Check for in-memory duplicates in provided list
        cleaned_serials = [str(s).strip() for s in serial_numbers if str(s).strip()]
        if len(cleaned_serials) != len(serial_numbers):
            raise APIError("Serial numbers cannot be blank or empty.", code="INVALID_SERIAL_NUMBER", status=400)

        if len(set(cleaned_serials)) != len(cleaned_serials):
            raise APIError("Duplicate serial numbers detected in the input payload.", code="DUPLICATE_SERIAL_IN_PAYLOAD", status=400)

        # Check DB uniqueness for this workspace and product
        existing_serials = BusinessSerialNumber.query.filter(
            BusinessSerialNumber.workspace_id == workspace_id,
            BusinessSerialNumber.product_id == product_id,
            BusinessSerialNumber.serial_number.in_(cleaned_serials)
        ).all()

        if existing_serials:
            dupe_nums = [s.serial_number for s in existing_serials]
            raise APIError(
                f"Serial numbers already registered for SKU '{product.sku}': {', '.join(dupe_nums)}.",
                code="DUPLICATE_SERIAL",
                status=400
            )

        now = datetime.now(timezone.utc)
        created_records = []
        for s_num in cleaned_serials:
            serial_obj = BusinessSerialNumber(
                workspace_id=workspace_id,
                product_id=product_id,
                serial_number=s_num,
                batch_id=batch_id,
                goods_receipt_id=goods_receipt_id,
                current_location_id=location_id,
                status='IN_STOCK',
                received_at=now,
                notes=notes
            )
            db.session.add(serial_obj)
            created_records.append(serial_obj)

        db.session.flush()

        for s_obj in created_records:
            AuditService.log_event(
                workspace_id=workspace_id,
                actor_user_id=actor_user_id,
                action='SERIAL_REGISTERED',
                entity_type='BUSINESS_SERIAL_NUMBER',
                entity_id=s_obj.id,
                after_state={
                    'serial_number': s_obj.serial_number,
                    'product_id': product_id,
                    'product_sku': product.sku,
                    'status': s_obj.status,
                    'batch_id': batch_id,
                    'location_id': location_id,
                    'goods_receipt_id': goods_receipt_id
                }
            )

        return created_records

    @classmethod
    def get_serial(cls, workspace_id: str, serial_id: str) -> BusinessSerialNumber:
        """
        Retrieves a serial number with workspace tenancy isolation.
        """
        serial = BusinessSerialNumber.query.filter_by(id=serial_id, workspace_id=workspace_id).first()
        if not serial:
            raise APIError("Serial number record not found in this workspace.", code="SERIAL_NOT_FOUND", status=404)
        return serial

    @classmethod
    def get_serial_by_number(cls, workspace_id: str, product_id: str, serial_number: str) -> Optional[BusinessSerialNumber]:
        """
        Retrieves a serial number by product and number within workspace.
        """
        return BusinessSerialNumber.query.filter_by(
            workspace_id=workspace_id,
            product_id=product_id,
            serial_number=serial_number.strip()
        ).first()

    @classmethod
    def list_serials(
        cls,
        workspace_id: str,
        product_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        status: Optional[str] = None,
        location_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Lists and filters serial numbers with workspace tenancy isolation.
        """
        query = BusinessSerialNumber.query.filter_by(workspace_id=workspace_id)

        if product_id:
            query = query.filter_by(product_id=product_id)
        if batch_id:
            query = query.filter_by(batch_id=batch_id)
        if status:
            query = query.filter_by(status=status.upper())
        if location_id:
            query = query.filter_by(current_location_id=location_id)
        if search:
            query = query.filter(BusinessSerialNumber.serial_number.ilike(f"%{search.strip()}%"))

        total = query.count()
        serials = query.order_by(BusinessSerialNumber.created_at.desc()).offset(offset).limit(limit).all()

        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'items': [s.serialize() for s in serials]
        }

    @classmethod
    def transition_lifecycle(
        cls,
        workspace_id: str,
        serial_id: str,
        target_status: str,
        actor_user_id: str,
        reason: Optional[str] = None,
        location_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> BusinessSerialNumber:
        """
        Executes a validated lifecycle state transition.
        Enforces state machine rules and records forensic audit event.
        """
        serial = cls.get_serial(workspace_id, serial_id)
        target = target_status.upper().strip()

        if target not in BusinessSerialNumber.VALID_STATUSES:
            raise APIError(
                f"Invalid target status '{target}'. Allowed: {list(BusinessSerialNumber.VALID_STATUSES)}",
                code="INVALID_STATUS",
                status=400
            )

        if not serial.can_transition_to(target):
            raise APIError(
                f"Cannot transition serial '{serial.serial_number}' from '{serial.status}' to '{target}'.",
                code="INVALID_LIFECYCLE_TRANSITION",
                status=400
            )

        before_status = serial.status
        now = datetime.now(timezone.utc)
        serial.status = target

        if target == 'ALLOCATED':
            serial.allocated_at = now
        elif target == 'SHIPPED':
            serial.shipped_at = now
            serial.current_location_id = None
        elif target == 'CONSUMED':
            serial.consumed_at = now
            serial.current_location_id = None
        elif target == 'DEFECTIVE':
            serial.defective_at = now
            serial.quarantine_reason = reason or "Flagged as defective"
        elif target == 'DISPOSED':
            serial.disposed_at = now
            serial.current_location_id = None
        elif target == 'IN_STOCK':
            serial.allocated_at = None
            if location_id:
                loc = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id).first()
                if not loc:
                    raise APIError("Location not found in this workspace.", code="LOCATION_NOT_FOUND", status=404)
                serial.current_location_id = location_id

        if notes:
            serial.notes = f"{serial.notes or ''}\n[{now.isoformat()}] {notes}".strip()

        db.session.flush()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='SERIAL_STATUS_CHANGED',
            entity_type='BUSINESS_SERIAL_NUMBER',
            entity_id=serial.id,
            before_state={'status': before_status},
            after_state={'status': serial.status, 'reason': reason},
            reason=reason
        )

        return serial

    @classmethod
    def validate_and_attribute_movement(
        cls,
        workspace_id: str,
        movement: BusinessStockMovement,
        product: BusinessProduct,
        serials: List[Any],
        actor_user_id: str,
        notes: Optional[str] = None
    ) -> List[BusinessStockMovementSerial]:
        """
        Validates serial attributions against a stock movement, enforces exact quantity matching,
        executes row-locking concurrency defense, validates single-location invariant,
        and records immutable attribution links.
        """
        if not serials:
            raise APIError(
                f"Product '{product.sku}' is serialized. Serial numbers must be provided for stock movement.",
                code="SERIALS_REQUIRED",
                status=400
            )

        # Quantity must be a whole number for serialized items
        if movement.quantity % 1 != Decimal('0'):
            raise APIError(
                f"Serialized product movement quantity must be an integer, got {movement.quantity}.",
                code="INVALID_SERIAL_QUANTITY",
                status=400
            )

        expected_count = int(movement.quantity)
        if len(serials) != expected_count:
            raise APIError(
                f"Serial count mismatch: expected {expected_count} serials for movement quantity {movement.quantity}, got {len(serials)}.",
                code="SERIAL_COUNT_MISMATCH",
                status=400
            )

        # Extract serial strings
        serial_str_list = []
        for s in serials:
            if isinstance(s, dict):
                s_num = (s.get('serial_number') or s.get('serial') or '').strip()
            else:
                s_num = str(s).strip()
            if not s_num:
                raise APIError("Encountered blank or invalid serial number in attribution payload.", code="INVALID_SERIAL_NUMBER", status=400)
            serial_str_list.append(s_num)

        if len(set(serial_str_list)) != len(serial_str_list):
            raise APIError("Duplicate serial numbers provided in attribution payload.", code="DUPLICATE_SERIAL_IN_PAYLOAD", status=400)

        now = datetime.now(timezone.utc)
        attributions = []

        if movement.direction == 'IN':
            # IN movement: register or receive serials
            # First check if any exist in DB
            existing = BusinessSerialNumber.query.filter(
                BusinessSerialNumber.workspace_id == workspace_id,
                BusinessSerialNumber.product_id == movement.product_id,
                BusinessSerialNumber.serial_number.in_(serial_str_list)
            ).all()

            existing_map = {e.serial_number: e for e in existing}
            for s_num in serial_str_list:
                if s_num in existing_map:
                    s_obj = existing_map[s_num]
                    # If already in stock, cannot receive it into stock again
                    if s_obj.status == 'IN_STOCK':
                        raise APIError(
                            f"Serial '{s_num}' is already IN_STOCK at location '{s_obj.current_location_id}'.",
                            code="DUPLICATE_SERIAL",
                            status=400
                        )
                    # Returning / re-entering stock
                    s_obj.status = 'IN_STOCK'
                    s_obj.current_location_id = movement.location_id
                else:
                    s_obj = BusinessSerialNumber(
                        workspace_id=workspace_id,
                        product_id=movement.product_id,
                        serial_number=s_num,
                        current_location_id=movement.location_id,
                        status='IN_STOCK',
                        received_at=now,
                        notes=notes
                    )
                    db.session.add(s_obj)

                db.session.flush()

                # Link attribution
                attr = BusinessStockMovementSerial(
                    workspace_id=workspace_id,
                    stock_movement_id=movement.id,
                    serial_id=s_obj.id
                )
                db.session.add(attr)
                attributions.append(attr)

        elif movement.direction == 'OUT':
            # OUT movement: Acquire transactional row-lock on serial records to prevent double-dispatch
            serial_objs = BusinessSerialNumber.query.filter(
                BusinessSerialNumber.workspace_id == workspace_id,
                BusinessSerialNumber.product_id == movement.product_id,
                BusinessSerialNumber.serial_number.in_(serial_str_list)
            ).with_for_update().all()

            if len(serial_objs) != len(serial_str_list):
                found_nums = {s.serial_number for s in serial_objs}
                missing = [s for s in serial_str_list if s not in found_nums]
                raise APIError(
                    f"Serial numbers not found in workspace for SKU '{product.sku}': {', '.join(missing)}.",
                    code="SERIAL_NOT_FOUND",
                    status=404
                )

            # Check batch attributions if movement is batch-attributed
            movement_batch_ids = {ba.batch_id for ba in (movement.batch_attributions or [])}

            for s_obj in serial_objs:
                # 1. State must be available for dispatch
                if s_obj.status not in ('IN_STOCK', 'ALLOCATED'):
                    raise APIError(
                        f"Serial '{s_obj.serial_number}' is not available for dispatch (Current status: '{s_obj.status}').",
                        code="SERIAL_NOT_AVAILABLE",
                        status=400
                    )

                # 2. Location invariant: must be in the movement's origin location
                if s_obj.current_location_id and s_obj.current_location_id != movement.location_id:
                    raise APIError(
                        f"Serial '{s_obj.serial_number}' is located at '{s_obj.current_location_id}', "
                        f"not movement location '{movement.location_id}'.",
                        code="SERIAL_LOCATION_MISMATCH",
                        status=400
                    )

                # 3. Batch consistency: if movement specifies batch, serial must belong to that batch
                if movement_batch_ids and s_obj.batch_id:
                    if s_obj.batch_id not in movement_batch_ids:
                        raise APIError(
                            f"Serial '{s_obj.serial_number}' belongs to batch '{s_obj.batch_id}', "
                            f"which is not in movement batch attributions.",
                            code="BATCH_SERIAL_MISMATCH",
                            status=400
                        )

                # Transition lifecycle state
                if movement.movement_type == 'SALE':
                    s_obj.status = 'SHIPPED'
                    s_obj.shipped_at = now
                    s_obj.current_location_id = None
                elif movement.movement_type in ('DAMAGED', 'DEFECTIVE'):
                    s_obj.status = 'DEFECTIVE'
                    s_obj.defective_at = now
                else:
                    s_obj.status = 'SHIPPED'
                    s_obj.shipped_at = now
                    s_obj.current_location_id = None

                db.session.flush()

                # Link attribution
                attr = BusinessStockMovementSerial(
                    workspace_id=workspace_id,
                    stock_movement_id=movement.id,
                    serial_id=s_obj.id
                )
                db.session.add(attr)
                attributions.append(attr)

        db.session.flush()
        return attributions

    @classmethod
    def get_serial_provenance(cls, workspace_id: str, serial_id: str) -> Dict[str, Any]:
        """
        Compiles the complete lifecycle provenance trail for an individual serial number.
        """
        serial = cls.get_serial(workspace_id, serial_id)

        # Retrieve all movement attributions ordered chronologically
        movement_attributions = (
            BusinessStockMovementSerial.query.filter_by(
                workspace_id=workspace_id,
                serial_id=serial.id
            )
            .join(BusinessStockMovement, BusinessStockMovementSerial.stock_movement_id == BusinessStockMovement.id)
            .order_by(BusinessStockMovement.created_at.asc())
            .all()
        )

        history = []
        for attr in movement_attributions:
            sm = attr.stock_movement
            history.append({
                'attribution_id': attr.id,
                'stock_movement_id': sm.id,
                'movement_type': sm.movement_type,
                'direction': sm.direction,
                'location_id': sm.location_id,
                'location_name': sm.location.name if sm.location else None,
                'reference_type': sm.reference_type,
                'reference_id': sm.reference_id,
                'reason': sm.reason,
                'timestamp': sm.created_at.isoformat() if sm.created_at else None
            })

        # Retrieve audit events
        audit_events = (
            AuditEvent.query.filter_by(
                workspace_id=workspace_id,
                entity_id=serial.id
            )
            .order_by(AuditEvent.created_at.asc())
            .all()
        )

        events = []
        for ae in audit_events:
            events.append({
                'audit_id': ae.id,
                'action': ae.action,
                'actor_user_id': ae.actor_user_id,
                'before_state': ae.before_state,
                'after_state': ae.after_state,
                'reason': ae.reason,
                'timestamp': ae.created_at.isoformat() if ae.created_at else None
            })

        return {
            'serial': serial.serialize(),
            'provenance_history': history,
            'audit_events': events
        }
