"""
DeadlineOS Business OS — Staging Service
========================================
Manages the 8-state staging lifecycle, human review updates,
and explicit confirmation / rejection actions.
"""

from database.db import db
from datetime import datetime, timezone
from models.business import StagedExtraction
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
        item = StagingService.get_staged_item_by_id(workspace_id, staging_id)
        if item.status == 'CONFIRMED':
            raise APIError("Extraction is already confirmed.", code="ALREADY_CONFIRMED", status=409)
        if item.status in ('REJECTED', 'EXPIRED'):
            raise APIError(f"Cannot confirm extraction in terminal state '{item.status}'.", code="INVALID_STATE_TRANSITION", status=400)

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
        item = StagingService.get_staged_item_by_id(workspace_id, staging_id)
        if item.status in ('CONFIRMED', 'REJECTED', 'EXPIRED'):
            raise APIError(f"Cannot reject extraction in terminal state '{item.status}'.", code="INVALID_STATE_TRANSITION", status=400)

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
