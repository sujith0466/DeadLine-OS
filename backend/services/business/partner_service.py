"""
DeadlineOS Business OS — Commercial Partner Service
===================================================
Manages Customers, Suppliers, and Counterparties with validation,
duplicate protection, and audit emission.
"""

from database.db import db
from models.business import CommercialPartner
from services.business.audit_service import AuditService
from utils.errors import APIError


class PartnerService:
    @staticmethod
    def create_partner(
        workspace_id: str,
        actor_user_id: str,
        partner_type: str,
        name: str,
        legal_name: str = None,
        phone: str = None,
        email: str = None,
        tax_identifier: str = None,
        credit_period_days: int = 30,
        ip_address: str = None,
        user_agent: str = None
    ) -> CommercialPartner:
        partner_type = partner_type.upper() if partner_type else ''
        if partner_type not in ('CUSTOMER', 'SUPPLIER', 'BOTH'):
            raise APIError("Invalid partner_type. Must be 'CUSTOMER', 'SUPPLIER', or 'BOTH'.", code="VALIDATION_ERROR", status=400)

        if not name or not name.strip():
            raise APIError("Partner name is required.", code="VALIDATION_ERROR", status=400)

        # Duplicate check within active workspace
        existing = CommercialPartner.query.filter_by(
            workspace_id=workspace_id,
            name=name.strip(),
            status='ACTIVE'
        ).first()
        if existing:
            raise APIError(f"A partner named '{name.strip()}' already exists in this workspace.", code="PARTNER_ALREADY_EXISTS", status=409)

        partner = CommercialPartner(
            workspace_id=workspace_id,
            partner_type=partner_type,
            name=name.strip(),
            legal_name=legal_name.strip() if legal_name else None,
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            tax_identifier=tax_identifier.strip() if tax_identifier else None,
            credit_period_days=credit_period_days if credit_period_days is not None and credit_period_days >= 0 else 30,
            status='ACTIVE'
        )
        db.session.add(partner)
        db.session.commit()

        # Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='PARTNER_CREATED',
            entity_type='COMMERCIAL_PARTNER',
            entity_id=partner.id,
            after_state=partner.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return partner

    @staticmethod
    def get_partners(
        workspace_id: str,
        partner_type: str = None,
        search: str = None,
        status: str = 'ACTIVE',
        limit: int = 50,
        offset: int = 0
    ):
        query = CommercialPartner.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter_by(status=status)
        if partner_type:
            partner_type = partner_type.upper()
            if partner_type in ('CUSTOMER', 'SUPPLIER'):
                query = query.filter(CommercialPartner.partner_type.in_([partner_type, 'BOTH']))
            else:
                query = query.filter_by(partner_type=partner_type)
        if search:
            query = query.filter(CommercialPartner.name.ilike(f"%{search.strip()}%"))

        total = query.count()
        partners = query.order_by(CommercialPartner.name.asc()).offset(offset).limit(limit).all()
        return [p.serialize() for p in partners], total

    @staticmethod
    def get_partner_by_id(workspace_id: str, partner_id: str) -> CommercialPartner:
        partner = CommercialPartner.query.filter_by(
            id=partner_id,
            workspace_id=workspace_id
        ).first()
        if not partner:
            raise APIError("Commercial partner not found.", code="PARTNER_NOT_FOUND", status=404)
        return partner

    @staticmethod
    def update_partner(
        workspace_id: str,
        partner_id: str,
        actor_user_id: str,
        updates: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> CommercialPartner:
        partner = PartnerService.get_partner_by_id(workspace_id, partner_id)
        before_state = partner.serialize()

        if 'name' in updates and updates['name']:
            new_name = updates['name'].strip()
            # Check duplicate name collision
            collision = CommercialPartner.query.filter(
                CommercialPartner.workspace_id == workspace_id,
                CommercialPartner.name == new_name,
                CommercialPartner.id != partner.id,
                CommercialPartner.status == 'ACTIVE'
            ).first()
            if collision:
                raise APIError(f"A partner named '{new_name}' already exists in this workspace.", code="PARTNER_ALREADY_EXISTS", status=409)
            partner.name = new_name

        if 'partner_type' in updates and updates['partner_type']:
            pt = updates['partner_type'].upper()
            if pt in ('CUSTOMER', 'SUPPLIER', 'BOTH'):
                partner.partner_type = pt
        if 'legal_name' in updates:
            partner.legal_name = updates['legal_name'].strip() if updates['legal_name'] else None
        if 'phone' in updates:
            partner.phone = updates['phone'].strip() if updates['phone'] else None
        if 'email' in updates:
            partner.email = updates['email'].strip() if updates['email'] else None
        if 'tax_identifier' in updates:
            partner.tax_identifier = updates['tax_identifier'].strip() if updates['tax_identifier'] else None
        if 'credit_period_days' in updates and updates['credit_period_days'] is not None:
            if updates['credit_period_days'] >= 0:
                partner.credit_period_days = updates['credit_period_days']

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='PARTNER_UPDATED',
            entity_type='COMMERCIAL_PARTNER',
            entity_id=partner.id,
            before_state=before_state,
            after_state=partner.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return partner

    @staticmethod
    def archive_partner(
        workspace_id: str,
        partner_id: str,
        actor_user_id: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> CommercialPartner:
        partner = PartnerService.get_partner_by_id(workspace_id, partner_id)
        before_state = partner.serialize()
        partner.status = 'ARCHIVED'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='PARTNER_ARCHIVED',
            entity_type='COMMERCIAL_PARTNER',
            entity_id=partner.id,
            before_state=before_state,
            after_state=partner.serialize(),
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return partner
