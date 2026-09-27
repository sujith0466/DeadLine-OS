"""
DeadlineOS Business OS — Staging Service
========================================
Manages the staging lifecycle, human review updates, and explicit confirmation /
rejection actions, bridging candidates to financial and inventory ledgers.
"""

from decimal import Decimal
from datetime import datetime, timezone
from database.db import db
from models.business import StagedExtraction, WorkspaceMember, BusinessVisualObservation
from services.business.audit_service import AuditService
from services.business.normalizer_service import NormalizerService
from utils.errors import APIError


class StagingService:
    @staticmethod
    def get_staged_items(
        workspace_id: str,
        status: str = None,
        candidate_type: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = StagedExtraction.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter_by(status=status.upper())
        if candidate_type:
            query = query.filter_by(candidate_type=candidate_type.upper())

        total = query.count()
        items = query.order_by(StagedExtraction.created_at.desc()).offset(offset).limit(limit).all()
        return [item.serialize() for item in items], total

    @staticmethod
    def get_staged_item_by_id(workspace_id: str, staging_id: str) -> StagedExtraction:
        item = StagedExtraction.query.filter_by(id=staging_id, workspace_id=workspace_id).first()
        if not item:
            raise APIError("Staged extraction not found.", code="STAGING_ITEM_NOT_FOUND", status=404)
        return item

    @staticmethod
    def update_staged_item(
        workspace_id: str,
        staging_id: str,
        actor_user_id: str,
        updates: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> StagedExtraction:
        item = StagingService.get_staged_item_by_id(workspace_id, staging_id)
        if item.status in ('CONFIRMED', 'REJECTED', 'EXPIRED'):
            raise APIError(f"Cannot edit extraction in terminal state '{item.status}'.", code="INVALID_STATE_TRANSITION", status=400)

        before_state = item.serialize()
        current_data = dict(item.normalized_data or {})

        if 'normalized_data' in updates and isinstance(updates['normalized_data'], dict):
            new_norm = updates['normalized_data']
            # Financial fields
            if 'amount' in new_norm:
                current_data['amount'] = NormalizerService.normalize_amount(new_norm['amount'])
            if 'currency' in new_norm:
                current_data['currency'] = NormalizerService.normalize_currency(new_norm['currency'])
            if 'date' in new_norm:
                current_data['date'] = NormalizerService.normalize_date(new_norm['date'])
            if 'partner_id' in new_norm:
                current_data['partner_id'] = new_norm['partner_id']
            if 'partner_name' in new_norm:
                current_data['partner_name'] = new_norm['partner_name']
            if 'description' in new_norm:
                current_data['description'] = new_norm['description']
            if 'candidate_type' in new_norm:
                current_data['candidate_type'] = new_norm['candidate_type'].upper()
                item.candidate_type = current_data['candidate_type']

            # Inventory / Reconciliation fields
            if 'quantity' in new_norm:
                current_data['quantity'] = str(Decimal(str(new_norm['quantity'])).quantize(Decimal('0.01')))
            if 'discrepancy_quantity' in new_norm:
                current_data['discrepancy_quantity'] = str(Decimal(str(new_norm['discrepancy_quantity'])).quantize(Decimal('0.01')))
            if 'direction' in new_norm:
                dir_val = str(new_norm['direction']).upper()
                if dir_val in ('IN', 'OUT'):
                    current_data['direction'] = dir_val
            if 'unit_cost' in new_norm:
                current_data['unit_cost'] = str(Decimal(str(new_norm['unit_cost'])).quantize(Decimal('0.01'))) if new_norm['unit_cost'] is not None else None
            if 'product_id' in new_norm:
                current_data['product_id'] = new_norm['product_id']
            if 'location_id' in new_norm:
                current_data['location_id'] = new_norm['location_id']
            if 'reason' in new_norm:
                current_data['reason'] = str(new_norm['reason']).strip()
            if 'batch_attributions' in new_norm:
                current_data['batch_attributions'] = new_norm['batch_attributions']
            if 'serial_attributions' in new_norm:
                current_data['serial_attributions'] = new_norm['serial_attributions']

        if 'candidate_type' in updates and updates['candidate_type']:
            item.candidate_type = updates['candidate_type'].upper()
            current_data['candidate_type'] = item.candidate_type

        item.normalized_data = current_data
        item.reviewed_by_user_id = actor_user_id
        item.reviewed_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='STAGED_EXTRACTION_UPDATED',
            entity_type='STAGED_EXTRACTION',
            entity_id=item.id,
            before_state=before_state,
            after_state=item.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return item

    @staticmethod
    def confirm_staged_item(
        workspace_id: str,
        staging_id: str,
        actor_user_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> StagedExtraction:
        # Acquire row-level lock against concurrent confirmations
        item = (
            StagedExtraction.query
            .filter_by(id=staging_id, workspace_id=workspace_id)
            .with_for_update()
            .first()
        )
        if not item:
            raise APIError("Staged extraction not found.", code="STAGING_ITEM_NOT_FOUND", status=404)

        if item.status == 'CONFIRMED':
            raise APIError("Extraction is already confirmed.", code="ALREADY_CONFIRMED", status=409)
        if item.status in ('REJECTED', 'EXPIRED'):
            raise APIError(f"Cannot confirm extraction in terminal state '{item.status}'.", code="INVALID_STATE_TRANSITION", status=400)

        # Candidate Type: Inventory Reconciliation
        if item.candidate_type in ('INVENTORY_RECONCILIATION', 'INVENTORY_ADJUSTMENT'):
            # Enforce strict RBAC: Only OWNER or ADMIN can confirm inventory modifications
            member = WorkspaceMember.query.filter_by(
                workspace_id=workspace_id,
                user_id=actor_user_id,
                status='ACTIVE'
            ).first()
            if not member or member.role not in ('OWNER', 'ADMIN'):
                raise APIError("Only OWNER and ADMIN roles may confirm inventory reconciliation candidates.", "FORBIDDEN", 403)

            from services.business.inventory_service import InventoryService

            norm = dict(item.normalized_data or {})
            product_id = norm.get('product_id')
            location_id = norm.get('location_id')
            if not product_id or not location_id:
                raise APIError("Reconciliation candidate missing product_id or location_id.", "VALIDATION_ERROR", 400)

            direction = (norm.get('direction') or 'IN').upper()
            qty_val = norm.get('quantity') or norm.get('discrepancy_quantity') or '0.00'
            try:
                quantity = abs(Decimal(str(qty_val))).quantize(Decimal('0.01'))
            except Exception:
                raise APIError("Invalid quantity in reconciliation candidate.", "VALIDATION_ERROR", 400)

            if quantity <= Decimal('0.00'):
                raise APIError("Reconciliation quantity must be greater than zero.", "VALIDATION_ERROR", 400)

            unit_cost = None
            if norm.get('unit_cost') is not None:
                try:
                    unit_cost = Decimal(str(norm['unit_cost'])).quantize(Decimal('0.01'))
                except Exception:
                    unit_cost = None

            movement_data = {
                'product_id': product_id,
                'location_id': location_id,
                'movement_type': 'MANUAL_ADJUSTMENT',
                'direction': direction,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'reference_type': 'STAGED_EXTRACTION',
                'reference_id': item.id,
                'batch_attributions': norm.get('batch_attributions'),
                'serial_attributions': norm.get('serial_attributions'),
                'reason': norm.get('reason') or f"Visual reconciliation confirmed for candidate {item.id}"
            }

            # Records stock movement (enforces negative-stock validation and C3 batch/serial logic)
            movement = InventoryService.record_stock_movement(
                workspace_id=workspace_id,
                actor_user_id=actor_user_id,
                data=movement_data,
                staged_extraction_id=item.id,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Update linked BusinessVisualObservation if present
            obs = BusinessVisualObservation.query.filter_by(
                staged_extraction_id=item.id,
                workspace_id=workspace_id
            ).first()
            if obs:
                obs.status = 'RECONCILED'
                obs.reviewed_by_user_id = actor_user_id
                obs.reviewed_at = datetime.now(timezone.utc)
                obs.review_notes = f"Reconciled via candidate {item.id}. Movement ID: {movement.id}"

        before_state = item.serialize()
        item.status = 'CONFIRMED'
        item.confirmed_at = datetime.now(timezone.utc)
        item.reviewed_by_user_id = actor_user_id
        item.reviewed_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='STAGED_EXTRACTION_CONFIRMED',
            entity_type='STAGED_EXTRACTION',
            entity_id=item.id,
            before_state=before_state,
            after_state=item.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return item

    @staticmethod
    def reject_staged_item(
        workspace_id: str,
        staging_id: str,
        actor_user_id: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> StagedExtraction:
        item = (
            StagedExtraction.query
            .filter_by(id=staging_id, workspace_id=workspace_id)
            .with_for_update()
            .first()
        )
        if not item:
            raise APIError("Staged extraction not found.", code="STAGING_ITEM_NOT_FOUND", status=404)

        if item.status in ('CONFIRMED', 'REJECTED', 'EXPIRED'):
            raise APIError(f"Cannot reject extraction in terminal state '{item.status}'.", code="INVALID_STATE_TRANSITION", status=400)

        # Update linked BusinessVisualObservation if present
        obs = BusinessVisualObservation.query.filter_by(
            staged_extraction_id=item.id,
            workspace_id=workspace_id
        ).first()
        if obs and obs.status != 'RECONCILED':
            obs.status = 'DISMISSED'
            obs.reviewed_by_user_id = actor_user_id
            obs.reviewed_at = datetime.now(timezone.utc)
            obs.review_notes = reason.strip() if reason else f"Candidate {item.id} rejected by reviewer"

        before_state = item.serialize()
        item.status = 'REJECTED'
        item.rejection_reason = reason.strip() if reason else "Rejected by reviewer"
        item.reviewed_by_user_id = actor_user_id
        item.reviewed_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='STAGED_EXTRACTION_REJECTED',
            entity_type='STAGED_EXTRACTION',
            entity_id=item.id,
            before_state=before_state,
            after_state=item.serialize(),
            reason=item.rejection_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return item
