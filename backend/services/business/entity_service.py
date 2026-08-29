"""
DeadlineOS Business OS — Business Entity Management Service
===========================================================
Manages legal entities, operating divisions, subsidiaries, and tax identities.
"""

from database.db import db
from datetime import datetime, timezone
import re
from decimal import Decimal
from models.business import BusinessEntity, InterEntityTransfer, WorkspaceMember
from services.business.audit_service import AuditService
from utils.errors import APIError

GSTIN_REGEX = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
PAN_REGEX = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')


class EntityService:
    @staticmethod
    def validate_tax_id(tax_id: str):
        if not tax_id:
            return True
        clean_id = tax_id.strip().upper()
        if len(clean_id) == 15 and GSTIN_REGEX.match(clean_id):
            return True
        if len(clean_id) == 10 and PAN_REGEX.match(clean_id):
            return True
        # Generic alphanumeric EIN / Tax ID allow 3-20 chars
        if re.match(r'^[A-Z0-9\-]{3,20}$', clean_id):
            return True
        raise APIError("Invalid tax identifier format (expected GSTIN, PAN, or valid Tax ID).", code="INVALID_TAX_ID", status=400)

    @staticmethod
    def create_entity(workspace_id: str, user_id: str, data: dict, ip_address: str = None, user_agent: str = None) -> BusinessEntity:
        name = data.get('name')
        if not name or not name.strip():
            raise APIError("Entity name is required.", code="MISSING_NAME", status=400)

        tax_id = data.get('tax_identifier')
        if tax_id:
            EntityService.validate_tax_id(tax_id)

        is_default = bool(data.get('is_default', False))
        if is_default:
            # Unset any existing default in this workspace
            BusinessEntity.query.filter_by(workspace_id=workspace_id, is_default=True).update({'is_default': False})

        entity = BusinessEntity(
            workspace_id=workspace_id,
            name=name.strip(),
            legal_name=data.get('legal_name', '').strip() or None,
            entity_code=data.get('entity_code', '').strip().upper() or None,
            tax_identifier=tax_id.strip().upper() if tax_id else None,
            currency=data.get('currency', 'INR'),
            is_default=is_default,
            status='ACTIVE'
        )
        db.session.add(entity)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='ENTITY_CREATED',
            entity_type='BUSINESS_ENTITY',
            entity_id=entity.id,
            after_state=entity.to_dict(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return entity

    @staticmethod
    def get_entities(workspace_id: str, status: str = None) -> list:
        query = BusinessEntity.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter_by(status=status)
        return [e.to_dict() for e in query.order_by(BusinessEntity.is_default.desc(), BusinessEntity.name.asc()).all()]

    @staticmethod
    def get_entity(workspace_id: str, entity_id: str) -> BusinessEntity:
        entity = BusinessEntity.query.filter_by(id=entity_id, workspace_id=workspace_id).first()
        if not entity:
            raise APIError("Business entity not found.", code="ENTITY_NOT_FOUND", status=404)
        return entity

    @staticmethod
    def record_transfer(
        source_workspace_id: str,
        user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> InterEntityTransfer:
        dest_ws_id = data.get('destination_workspace_id') or source_workspace_id
        source_entity_id = data.get('source_entity_id')
        dest_entity_id = data.get('destination_entity_id')
        amount_raw = data.get('amount')

        if not amount_raw:
            raise APIError("Amount is required.", code="MISSING_AMOUNT", status=400)

        try:
            amount = Decimal(str(amount_raw))
            if amount <= Decimal('0.00'):
                raise ValueError()
        except Exception:
            raise APIError("Amount must be a positive decimal.", code="INVALID_AMOUNT", status=400)

        # Check membership in destination workspace if different
        if dest_ws_id != source_workspace_id:
            dest_member = WorkspaceMember.query.filter_by(workspace_id=dest_ws_id, user_id=user_id, status='ACTIVE').first()
            if not dest_member:
                raise APIError("Not authorized to transfer to target workspace.", code="UNAUTHORIZED_DESTINATION", status=403)

        transfer = InterEntityTransfer(
            source_workspace_id=source_workspace_id,
            source_entity_id=source_entity_id,
            destination_workspace_id=dest_ws_id,
            destination_entity_id=dest_entity_id,
            amount=amount,
            currency=data.get('currency', 'INR'),
            reference_note=data.get('reference_note'),
            status='SETTLED',
            created_by_user_id=user_id
        )
        db.session.add(transfer)
        db.session.commit()

        AuditService.log_event(
            workspace_id=source_workspace_id,
            actor_user_id=user_id,
            action='INTER_ENTITY_TRANSFER_RECORDED',
            entity_type='INTER_ENTITY_TRANSFER',
            entity_id=transfer.id,
            after_state=transfer.to_dict(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return transfer
