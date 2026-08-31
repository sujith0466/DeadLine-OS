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

    @staticmethod
    def update_entity(
        workspace_id: str,
        entity_id: str,
        user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessEntity:
        entity = EntityService.get_entity(workspace_id, entity_id)
        before_state = entity.to_dict()

        if 'name' in data:
            name = data['name'].strip() if data['name'] else ''
            if not name:
                raise APIError("Entity name cannot be empty.", code="INVALID_NAME", status=400)
            entity.name = name

        if 'legal_name' in data:
            entity.legal_name = data['legal_name'].strip() if data['legal_name'] else None

        if 'entity_code' in data:
            entity.entity_code = data['entity_code'].strip().upper() if data['entity_code'] else None

        if 'tax_identifier' in data:
            tax_id = data['tax_identifier']
            if tax_id:
                EntityService.validate_tax_id(tax_id)
                entity.tax_identifier = tax_id.strip().upper()
            else:
                entity.tax_identifier = None

        if 'currency' in data and data['currency']:
            entity.currency = data['currency'].strip().upper()

        if 'status' in data and data['status'] in ('ACTIVE', 'INACTIVE'):
            entity.status = data['status']

        if data.get('is_default') is True:
            # Unset all other defaults in this workspace
            BusinessEntity.query.filter_by(workspace_id=workspace_id, is_default=True).update({'is_default': False})
            entity.is_default = True
        elif 'is_default' in data and data['is_default'] is False:
            entity.is_default = False

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='ENTITY_UPDATED',
            entity_type='BUSINESS_ENTITY',
            entity_id=entity.id,
            before_state=before_state,
            after_state=entity.to_dict(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return entity

    @staticmethod
    def archive_entity(
        workspace_id: str,
        entity_id: str,
        user_id: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessEntity:
        entity = EntityService.get_entity(workspace_id, entity_id)
        before_state = entity.to_dict()

        entity.status = 'INACTIVE'
        if entity.is_default:
            entity.is_default = False

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='ENTITY_ARCHIVED',
            entity_type='BUSINESS_ENTITY',
            entity_id=entity.id,
            before_state=before_state,
            after_state=entity.to_dict(),
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return entity

    @staticmethod
    def get_transfers(workspace_id: str, limit: int = 50, offset: int = 0) -> list:
        transfers = InterEntityTransfer.query.filter(
            (InterEntityTransfer.source_workspace_id == workspace_id) |
            (InterEntityTransfer.destination_workspace_id == workspace_id)
        ).order_by(InterEntityTransfer.created_at.desc()).offset(offset).limit(limit).all()

        return [t.to_dict() for t in transfers]
