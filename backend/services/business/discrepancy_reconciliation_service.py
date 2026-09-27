"""
DeadlineOS Business OS — Visual Discrepancy Reconciliation Service (Phase C4.3)
=============================================================================
Manages the evaluation of visual stock discrepancies, generates human-reviewable
staged correction candidates in `business_staged_extractions`, coordinates
dismissals with zero ledger impact, and protects append-only inventory integrity.
"""

from decimal import Decimal
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone
from database.db import db
from models.business import (
    BusinessVisualObservation,
    StagedExtraction,
    BusinessProduct,
    BusinessLocation,
    BusinessShelfZone,
    WorkspaceMember
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class DiscrepancyReconciliationService:
    @staticmethod
    def propose_reconciliation(
        workspace_id: str,
        observation_id: str,
        actor_user_id: str,
        override_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[StagedExtraction]:
        """
        Evaluates a visual observation's discrepancy quantity.
        If discrepancy != 0, creates a StagedExtraction candidate with status NEEDS_REVIEW.
        If discrepancy == 0, returns None (no-op).
        Ensures idempotency: if an open candidate exists, returns it without creating duplicates.
        """
        obs = BusinessVisualObservation.query.filter_by(
            id=observation_id,
            workspace_id=workspace_id
        ).first()

        if not obs:
            raise APIError("Visual observation not found in this workspace.", "OBSERVATION_NOT_FOUND", 404)

        # Idempotency check: Return existing staged candidate if in NEEDS_REVIEW
        if obs.staged_extraction_id:
            existing_staged = StagedExtraction.query.filter_by(
                id=obs.staged_extraction_id,
                workspace_id=workspace_id
            ).first()
            if existing_staged:
                if existing_staged.status == 'NEEDS_REVIEW':
                    return existing_staged
                elif existing_staged.status == 'CONFIRMED':
                    raise APIError(
                        "Visual observation has already been reconciled and confirmed.",
                        "ALREADY_RECONCILED",
                        409
                    )

        # Discrepancy validation
        if obs.discrepancy_quantity is None:
            return None

        try:
            disc_qty = Decimal(str(obs.discrepancy_quantity)).quantize(Decimal('0.01'))
        except Exception:
            disc_qty = Decimal('0.00')

        if disc_qty == Decimal('0.00'):
            # Zero discrepancy: No-op
            return None

        # Resolve target product
        product_id = obs.matched_product_id
        if not product_id and obs.shelf_zone_id:
            zone = BusinessShelfZone.query.filter_by(
                id=obs.shelf_zone_id,
                workspace_id=workspace_id
            ).first()
            if zone:
                product_id = zone.assigned_product_id

        if not product_id:
            raise APIError(
                "Cannot propose reconciliation without a matched product or assigned shelf zone product.",
                "PRODUCT_REQUIRED",
                400
            )

        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
        if not product:
            raise APIError("Target product not found in this workspace.", "PRODUCT_NOT_FOUND", 404)

        if product.status == 'ARCHIVED':
            raise APIError(f"Cannot reconcile archived product '{product.sku}'.", "PRODUCT_ARCHIVED", 400)

        # Resolve target location
        location = BusinessLocation.query.filter_by(id=obs.location_id, workspace_id=workspace_id).first()
        if not location:
            raise APIError("Target location not found in this workspace.", "LOCATION_NOT_FOUND", 404)

        if location.status == 'INACTIVE':
            raise APIError(f"Cannot reconcile inactive location '{location.name}'.", "LOCATION_INACTIVE", 400)

        # Determine adjustment direction and magnitude
        direction = 'IN' if disc_qty > Decimal('0.00') else 'OUT'
        abs_qty = abs(disc_qty)

        shelf_zone_code = obs.shelf_zone.zone_code if obs.shelf_zone else None
        default_reason = (
            f"Visual discrepancy reconciliation: {direction} {abs_qty} {product.unit} "
            f"(visual count: {obs.visual_count}, system stock: {obs.system_stock_at_capture}) "
            f"on shelf zone {shelf_zone_code or 'N/A'}"
        )

        normalized_data = {
            'observation_id': obs.id,
            'location_id': obs.location_id,
            'location_name': location.name,
            'shelf_zone_id': obs.shelf_zone_id,
            'shelf_zone_code': shelf_zone_code,
            'product_id': product.id,
            'product_sku': product.sku,
            'product_name': product.name,
            'system_stock_at_capture': str(obs.system_stock_at_capture) if obs.system_stock_at_capture is not None else None,
            'visual_count': str(obs.visual_count) if obs.visual_count is not None else None,
            'discrepancy_quantity': str(disc_qty),
            'quantity': str(abs_qty),
            'direction': direction,
            'movement_type': 'MANUAL_ADJUSTMENT',
            'reference_type': 'STAGED_EXTRACTION',
            'unit_cost': str(product.cost_price) if product.cost_price is not None else None,
            'batch_attributions': [],
            'serial_attributions': [],
            'reason': override_reason.strip() if override_reason else default_reason
        }

        staged = StagedExtraction(
            workspace_id=workspace_id,
            created_by_user_id=actor_user_id,
            source_channel='CAMERA_SENSOR',
            candidate_type='INVENTORY_RECONCILIATION',
            status='NEEDS_REVIEW',
            confidence_score=int(obs.overall_confidence) if obs.overall_confidence else 100,
            raw_extracted_data={
                'observation_id': obs.id,
                'model_provider': obs.model_provider,
                'model_name': obs.model_name,
                'detected_items_count': len(obs.detected_items or []),
                'inference_confidence': float(obs.overall_confidence or 0),
                'anomaly_type': obs.anomaly_type,
                'capture_device': obs.capture_device
            },
            normalized_data=normalized_data
        )
        db.session.add(staged)
        db.session.flush()

        obs.staged_extraction_id = staged.id
        obs.status = 'REVIEW_REQUIRED'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='RECONCILIATION_PROPOSED',
            entity_type='staged_extraction',
            entity_id=staged.id,
            after_state=staged.serialize(),
            reason=f"Proposed {direction} adjustment of {abs_qty} {product.unit} from observation {obs.id}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return staged

    @staticmethod
    def dismiss_observation(
        workspace_id: str,
        observation_id: str,
        actor_user_id: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessVisualObservation:
        """
        Dismisses a visual observation without creating any stock movements.
        If an open staged extraction is attached, transitions it to REJECTED.
        Sets observation status to DISMISSED.
        """
        obs = BusinessVisualObservation.query.filter_by(
            id=observation_id,
            workspace_id=workspace_id
        ).first()

        if not obs:
            raise APIError("Visual observation not found in this workspace.", "OBSERVATION_NOT_FOUND", 404)

        if obs.status == 'RECONCILED':
            raise APIError(
                "Cannot dismiss an observation that has already been reconciled into authoritative inventory.",
                "ALREADY_RECONCILED",
                400
            )

        before_state = obs.serialize()
        dismissal_reason = reason.strip() if reason else "Dismissed by operator during visual review"

        # Update linked staged extraction if present
        if obs.staged_extraction_id:
            staged = StagedExtraction.query.filter_by(
                id=obs.staged_extraction_id,
                workspace_id=workspace_id
            ).first()
            if staged and staged.status == 'NEEDS_REVIEW':
                staged_before = staged.serialize()
                staged.status = 'REJECTED'
                staged.rejection_reason = dismissal_reason
                staged.reviewed_by_user_id = actor_user_id
                staged.reviewed_at = datetime.now(timezone.utc)
                db.session.flush()

                AuditService.log_event(
                    workspace_id=workspace_id,
                    actor_user_id=actor_user_id,
                    action='STAGED_EXTRACTION_REJECTED',
                    entity_type='staged_extraction',
                    entity_id=staged.id,
                    before_state=staged_before,
                    after_state=staged.serialize(),
                    reason=dismissal_reason,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

        obs.status = 'DISMISSED'
        obs.reviewed_by_user_id = actor_user_id
        obs.reviewed_at = datetime.now(timezone.utc)
        obs.review_notes = dismissal_reason
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='OBSERVATION_DISMISSED',
            entity_type='business_visual_observation',
            entity_id=obs.id,
            before_state=before_state,
            after_state=obs.serialize(),
            reason=dismissal_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return obs

    @staticmethod
    def list_pending_discrepancies(
        workspace_id: str,
        location_id: Optional[str] = None,
        shelf_zone_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lists pending visual observations that have non-zero quantity discrepancies.
        """
        query = BusinessVisualObservation.query.filter(
            BusinessVisualObservation.workspace_id == workspace_id,
            BusinessVisualObservation.discrepancy_quantity.isnot(None),
            BusinessVisualObservation.discrepancy_quantity != 0
        )

        if location_id:
            query = query.filter(BusinessVisualObservation.location_id == location_id)
        if shelf_zone_id:
            query = query.filter(BusinessVisualObservation.shelf_zone_id == shelf_zone_id)

        total = query.count()
        observations = (
            query.order_by(BusinessVisualObservation.capture_timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [obs.serialize() for obs in observations], total
