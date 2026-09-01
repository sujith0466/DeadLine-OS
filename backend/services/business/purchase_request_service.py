"""
DeadlineOS Business OS — Purchase Request Service
=================================================
Authoritative service for Purchase Request lifecycle, sequential numbering,
administrative approvals, and PR-to-PO conversion.
"""

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import func
from database.db import db
from models.business import (
    BusinessPurchaseRequest,
    BusinessProduct,
    BusinessLocation,
    WorkspaceMember
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class PurchaseRequestService:
    VALID_PRIORITIES = {'LOW', 'MEDIUM', 'HIGH', 'URGENT'}
    VALID_STATUSES = {'DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'ORDERED', 'CANCELLED'}

    @staticmethod
    def generate_request_number(workspace_id: str) -> str:
        """
        Generates a concurrency-safe sequential request number scoped per workspace and year:
        e.g., PR-2026-0001
        """
        current_year = date.today().year
        prefix = f"PR-{current_year}-"

        # Query highest sequence number for this workspace and year with a lock
        count = db.session.query(func.count(BusinessPurchaseRequest.id)).filter(
            BusinessPurchaseRequest.workspace_id == workspace_id,
            BusinessPurchaseRequest.request_number.like(f"{prefix}%")
        ).scalar() or 0

        sequence = count + 1
        request_number = f"{prefix}{sequence:04d}"

        # Ensure uniqueness in case of race condition
        while BusinessPurchaseRequest.query.filter_by(workspace_id=workspace_id, request_number=request_number).first():
            sequence += 1
            request_number = f"{prefix}{sequence:04d}"

        return request_number

    @staticmethod
    def create_request(
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseRequest:
        product_id = data.get('product_id')
        if not product_id:
            raise APIError("Field 'product_id' is required.", "VALIDATION_ERROR", 400)

        product = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not product:
            raise APIError("Product not found or inactive in this workspace.", "VALIDATION_ERROR", 400)

        location_id = data.get('location_id')
        if not location_id:
            raise APIError("Field 'location_id' is required.", "VALIDATION_ERROR", 400)

        location = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not location:
            raise APIError("Destination location not found or inactive in this workspace.", "VALIDATION_ERROR", 400)

        try:
            qty = Decimal(str(data.get('requested_quantity', '0'))).quantize(Decimal('0.01'))
            if qty <= Decimal('0.00'):
                raise ValueError()
        except Exception:
            raise APIError("Field 'requested_quantity' must be a positive decimal greater than 0.", "VALIDATION_ERROR", 400)

        unit_price = product.cost_price or Decimal('0.00')
        if data.get('estimated_unit_price') is not None:
            try:
                unit_price = Decimal(str(data['estimated_unit_price'])).quantize(Decimal('0.01'))
                if unit_price < Decimal('0.00'):
                    raise ValueError()
            except Exception:
                raise APIError("Field 'estimated_unit_price' must be a non-negative decimal.", "VALIDATION_ERROR", 400)

        total_price = (qty * unit_price).quantize(Decimal('0.01'))
        priority = (data.get('priority') or 'MEDIUM').upper()
        if priority not in PurchaseRequestService.VALID_PRIORITIES:
            raise APIError(f"Invalid priority '{priority}'.", "VALIDATION_ERROR", 400)

        initial_status = (data.get('status') or 'SUBMITTED').upper()
        if initial_status not in ('DRAFT', 'SUBMITTED'):
            raise APIError("Initial request status must be 'DRAFT' or 'SUBMITTED'.", "VALIDATION_ERROR", 400)

        request_number = PurchaseRequestService.generate_request_number(workspace_id)

        pr = BusinessPurchaseRequest(
            workspace_id=workspace_id,
            request_number=request_number,
            product_id=product.id,
            location_id=location.id,
            requested_quantity=qty,
            estimated_unit_price=unit_price,
            estimated_total_price=total_price,
            currency=data.get('currency', product.currency or 'INR').upper(),
            priority=priority,
            status=initial_status,
            reason=data.get('reason'),
            requested_by_user_id=actor_user_id
        )

        db.session.add(pr)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PR_CREATED",
            entity_type="business_purchase_request",
            entity_id=pr.id,
            before_state=None,
            after_state=pr.serialize(),
            reason=f"Created Purchase Request {pr.request_number} ({pr.status})",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return pr

    @staticmethod
    def get_requests(
        workspace_id: str,
        status: str = None,
        priority: str = None,
        product_id: str = None,
        location_id: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = BusinessPurchaseRequest.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter_by(status=status.upper())
        if priority:
            query = query.filter_by(priority=priority.upper())
        if product_id:
            query = query.filter_by(product_id=product_id)
        if location_id:
            query = query.filter_by(location_id=location_id)
        if search:
            query = query.filter(
                (BusinessPurchaseRequest.request_number.ilike(f"%{search}%")) |
                (BusinessPurchaseRequest.reason.ilike(f"%{search}%"))
            )

        total = query.count()
        requests = query.order_by(BusinessPurchaseRequest.created_at.desc()).offset(offset).limit(min(limit, 100)).all()
        return [r.serialize() for r in requests], total

    @staticmethod
    def get_request_by_id(workspace_id: str, request_id: str) -> BusinessPurchaseRequest:
        pr = BusinessPurchaseRequest.query.filter_by(id=request_id, workspace_id=workspace_id).first()
        if not pr:
            raise APIError("Purchase request not found in this workspace.", "NOT_FOUND", 404)
        return pr

    @staticmethod
    def update_request(
        workspace_id: str,
        actor_user_id: str,
        request_id: str,
        data: dict,
        user_role: str = 'MEMBER',
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseRequest:
        pr = PurchaseRequestService.get_request_by_id(workspace_id, request_id)
        before_state = pr.serialize()

        if pr.status not in ('DRAFT', 'SUBMITTED'):
            raise APIError(f"Cannot update purchase request in status '{pr.status}'.", "INVALID_STATE", 400)

        if user_role == 'MEMBER' and pr.requested_by_user_id != actor_user_id:
            raise APIError("Members can only modify their own purchase requests.", "FORBIDDEN", 403)

        if 'requested_quantity' in data:
            try:
                qty = Decimal(str(data['requested_quantity'])).quantize(Decimal('0.01'))
                if qty <= Decimal('0.00'):
                    raise ValueError()
                pr.requested_quantity = qty
            except Exception:
                raise APIError("Field 'requested_quantity' must be a positive decimal.", "VALIDATION_ERROR", 400)

        if 'estimated_unit_price' in data:
            try:
                unit_price = Decimal(str(data['estimated_unit_price'])).quantize(Decimal('0.01'))
                if unit_price < Decimal('0.00'):
                    raise ValueError()
                pr.estimated_unit_price = unit_price
            except Exception:
                raise APIError("Field 'estimated_unit_price' must be a non-negative decimal.", "VALIDATION_ERROR", 400)

        pr.estimated_total_price = (pr.requested_quantity * pr.estimated_unit_price).quantize(Decimal('0.01'))

        if 'priority' in data:
            p = (data['priority'] or 'MEDIUM').upper()
            if p not in PurchaseRequestService.VALID_PRIORITIES:
                raise APIError(f"Invalid priority '{p}'.", "VALIDATION_ERROR", 400)
            pr.priority = p

        if 'reason' in data:
            pr.reason = data['reason']

        if 'location_id' in data:
            loc = BusinessLocation.query.filter_by(id=data['location_id'], workspace_id=workspace_id, status='ACTIVE').first()
            if not loc:
                raise APIError("Location not found in this workspace.", "VALIDATION_ERROR", 400)
            pr.location_id = loc.id

        if 'product_id' in data:
            prod = BusinessProduct.query.filter_by(id=data['product_id'], workspace_id=workspace_id, status='ACTIVE').first()
            if not prod:
                raise APIError("Product not found in this workspace.", "VALIDATION_ERROR", 400)
            pr.product_id = prod.id

        pr.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PR_UPDATED",
            entity_type="business_purchase_request",
            entity_id=pr.id,
            before_state=before_state,
            after_state=pr.serialize(),
            reason=f"Updated Purchase Request {pr.request_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return pr

    @staticmethod
    def approve_request(
        workspace_id: str,
        actor_user_id: str,
        request_id: str,
        approval_notes: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseRequest:
        pr = PurchaseRequestService.get_request_by_id(workspace_id, request_id)
        before_state = pr.serialize()

        if pr.status != 'SUBMITTED':
            raise APIError(f"Cannot approve request in status '{pr.status}'. Must be in 'SUBMITTED' status.", "INVALID_STATE", 400)

        pr.status = 'APPROVED'
        pr.approved_by_user_id = actor_user_id
        pr.approval_notes = approval_notes
        pr.approved_at = datetime.now(timezone.utc)
        pr.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PR_APPROVED",
            entity_type="business_purchase_request",
            entity_id=pr.id,
            before_state=before_state,
            after_state=pr.serialize(),
            reason=f"Approved Purchase Request {pr.request_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return pr

    @staticmethod
    def reject_request(
        workspace_id: str,
        actor_user_id: str,
        request_id: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseRequest:
        pr = PurchaseRequestService.get_request_by_id(workspace_id, request_id)
        before_state = pr.serialize()

        if pr.status != 'SUBMITTED':
            raise APIError(f"Cannot reject request in status '{pr.status}'. Must be in 'SUBMITTED' status.", "INVALID_STATE", 400)

        pr.status = 'REJECTED'
        pr.approved_by_user_id = actor_user_id
        pr.approval_notes = reason
        pr.approved_at = datetime.now(timezone.utc)
        pr.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PR_REJECTED",
            entity_type="business_purchase_request",
            entity_id=pr.id,
            before_state=before_state,
            after_state=pr.serialize(),
            reason=f"Rejected Purchase Request {pr.request_number}: {reason or 'No reason provided'}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return pr

    @staticmethod
    def cancel_request(
        workspace_id: str,
        actor_user_id: str,
        request_id: str,
        reason: str = None,
        user_role: str = 'MEMBER',
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessPurchaseRequest:
        pr = PurchaseRequestService.get_request_by_id(workspace_id, request_id)
        before_state = pr.serialize()

        if pr.status not in ('DRAFT', 'SUBMITTED', 'APPROVED'):
            raise APIError(f"Cannot cancel purchase request in status '{pr.status}'.", "INVALID_STATE", 400)

        if user_role == 'MEMBER' and pr.requested_by_user_id != actor_user_id:
            raise APIError("Members can only cancel their own purchase requests.", "FORBIDDEN", 403)

        pr.status = 'CANCELLED'
        pr.approval_notes = reason or pr.approval_notes
        pr.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="PR_CANCELLED",
            entity_type="business_purchase_request",
            entity_id=pr.id,
            before_state=before_state,
            after_state=pr.serialize(),
            reason=f"Cancelled Purchase Request {pr.request_number}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return pr
