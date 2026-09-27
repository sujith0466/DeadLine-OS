"""
DeadlineOS Business OS — Shelf Zone Service (Phase C4.1)
=========================================================
Manages physical shelf zone topology, planogram configurations,
and fixture metadata with strict tenant isolation, location ownership
validation, product assignment verification, and forensic audit logging.
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timezone
import re

from database.db import db
from models.business import (
    Workspace,
    BusinessLocation,
    BusinessProduct,
    BusinessShelfZone,
    AuditEvent
)
from services.business.audit_service import AuditService
from utils.errors import APIError

VALID_ZONE_TYPES = {'SHELF', 'RACK', 'PALLET_SLOT', 'BIN', 'ENDCAP', 'COOLER', 'DISPLAY'}
VALID_STATUSES = {'ACTIVE', 'INACTIVE', 'MAINTENANCE'}


class ShelfZoneService:
    """
    Authoritative service managing physical shelf and rack topologies.
    """

    @classmethod
    def create_shelf_zone(
        cls,
        workspace_id: str,
        actor_user_id: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessShelfZone:
        """
        Creates a new physical shelf zone or fixture in a workspace location.
        """
        # 1. Validate Workspace
        ws = db.session.get(Workspace, workspace_id)
        if not ws or ws.status != 'ACTIVE':
            raise APIError("Active workspace is required.", code="INVALID_WORKSPACE", status=400)

        # 2. Validate Location
        location_id = data.get('location_id')
        if not location_id:
            raise APIError("Field 'location_id' is required.", code="MISSING_LOCATION", status=400)

        location = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not location:
            raise APIError("Location not found or inactive in this workspace.", code="LOCATION_NOT_FOUND", status=404)

        # 3. Validate Zone Code & Name
        zone_code = str(data.get('zone_code', '')).strip().upper()
        if not zone_code:
            raise APIError("Field 'zone_code' is required.", code="MISSING_ZONE_CODE", status=400)
        if not re.match(r'^[A-Z0-9_\-\.]{2,50}$', zone_code):
            raise APIError(
                "Zone code must be 2-50 characters alphanumeric (letters, numbers, hyphens, underscores).",
                code="INVALID_ZONE_CODE",
                status=400
            )

        name = str(data.get('name', '')).strip()
        if not name:
            raise APIError("Field 'name' is required.", code="MISSING_NAME", status=400)

        zone_type = str(data.get('zone_type', 'SHELF')).strip().upper()
        if zone_type not in VALID_ZONE_TYPES:
            raise APIError(
                f"Invalid zone_type '{zone_type}'. Allowed types: {', '.join(sorted(VALID_ZONE_TYPES))}.",
                code="INVALID_ZONE_TYPE",
                status=400
            )

        # 4. Check Uniqueness in (workspace_id, location_id, zone_code)
        existing = BusinessShelfZone.query.filter_by(
            workspace_id=workspace_id,
            location_id=location_id,
            zone_code=zone_code
        ).first()
        if existing:
            raise APIError(
                f"Shelf zone '{zone_code}' already exists at location '{location.name}'.",
                code="DUPLICATE_ZONE_CODE",
                status=400
            )

        # 5. Validate Assigned Product (Planogram Target)
        assigned_product_id = data.get('assigned_product_id')
        if assigned_product_id:
            prod = BusinessProduct.query.filter_by(
                id=assigned_product_id,
                workspace_id=workspace_id,
                status='ACTIVE'
            ).first()
            if not prod:
                raise APIError("Assigned product not found or inactive in this workspace.", code="PRODUCT_NOT_FOUND", status=404)

        # 6. Parse and Validate Quantitative Thresholds
        try:
            expected_capacity = Decimal(str(data.get('expected_capacity', '0.00'))).quantize(Decimal('0.01'))
            if expected_capacity < Decimal('0.00'):
                raise ValueError()
        except Exception:
            raise APIError("Field 'expected_capacity' must be a non-negative decimal.", code="INVALID_CAPACITY", status=400)

        try:
            target_facings = int(data.get('target_facings', 1))
            if target_facings < 0:
                raise ValueError()
        except Exception:
            raise APIError("Field 'target_facings' must be a non-negative integer.", code="INVALID_FACINGS", status=400)

        try:
            reorder_threshold = Decimal(str(data.get('reorder_threshold', '0.00'))).quantize(Decimal('0.01'))
            if reorder_threshold < Decimal('0.00'):
                raise ValueError()
        except Exception:
            raise APIError("Field 'reorder_threshold' must be a non-negative decimal.", code="INVALID_REORDER_THRESHOLD", status=400)

        notes = data.get('notes')

        # 7. Create Entity
        zone = BusinessShelfZone(
            workspace_id=workspace_id,
            location_id=location_id,
            zone_code=zone_code,
            name=name,
            zone_type=zone_type,
            assigned_product_id=assigned_product_id,
            expected_capacity=expected_capacity,
            target_facings=target_facings,
            reorder_threshold=reorder_threshold,
            status='ACTIVE',
            notes=notes
        )
        db.session.add(zone)
        db.session.commit()

        # 8. Log Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="SHELF_ZONE_CREATED",
            entity_type="business_shelf_zone",
            entity_id=zone.id,
            after_state=zone.serialize(),
            reason=f"Created shelf zone {zone.zone_code} ({zone.name}) at location {location.name}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return zone

    @classmethod
    def get_shelf_zone_by_id(cls, workspace_id: str, zone_id: str) -> BusinessShelfZone:
        """
        Retrieves a shelf zone ensuring strict tenant isolation.
        """
        zone = BusinessShelfZone.query.filter_by(id=zone_id, workspace_id=workspace_id).first()
        if not zone:
            raise APIError("Shelf zone not found in this workspace.", code="ZONE_NOT_FOUND", status=404)
        return zone

    @classmethod
    def list_shelf_zones(
        cls,
        workspace_id: str,
        location_id: Optional[str] = None,
        status: Optional[str] = None,
        product_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lists shelf zones with filtering and pagination.
        """
        query = BusinessShelfZone.query.filter_by(workspace_id=workspace_id)

        if location_id:
            query = query.filter_by(location_id=location_id)
        if status:
            query = query.filter_by(status=status.upper())
        if product_id:
            query = query.filter_by(assigned_product_id=product_id)

        total_count = query.count()
        zones = query.order_by(BusinessShelfZone.created_at.desc()).offset(offset).limit(limit).all()

        return [z.serialize() for z in zones], total_count

    @classmethod
    def update_shelf_zone(
        cls,
        workspace_id: str,
        zone_id: str,
        actor_user_id: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessShelfZone:
        """
        Updates an existing shelf zone.
        """
        zone = cls.get_shelf_zone_by_id(workspace_id, zone_id)
        before_state = zone.serialize()

        # Optional update fields
        if 'name' in data:
            new_name = str(data['name']).strip()
            if not new_name:
                raise APIError("Field 'name' cannot be empty.", code="INVALID_NAME", status=400)
            zone.name = new_name

        if 'zone_type' in data:
            new_type = str(data['zone_type']).strip().upper()
            if new_type not in VALID_ZONE_TYPES:
                raise APIError(
                    f"Invalid zone_type '{new_type}'. Allowed types: {', '.join(sorted(VALID_ZONE_TYPES))}.",
                    code="INVALID_ZONE_TYPE",
                    status=400
                )
            zone.zone_type = new_type

        if 'status' in data:
            new_status = str(data['status']).strip().upper()
            if new_status not in VALID_STATUSES:
                raise APIError(
                    f"Invalid status '{new_status}'. Allowed statuses: {', '.join(sorted(VALID_STATUSES))}.",
                    code="INVALID_STATUS",
                    status=400
                )
            zone.status = new_status

        if 'assigned_product_id' in data:
            prod_id = data['assigned_product_id']
            if prod_id:
                prod = BusinessProduct.query.filter_by(id=prod_id, workspace_id=workspace_id, status='ACTIVE').first()
                if not prod:
                    raise APIError("Assigned product not found or inactive in this workspace.", code="PRODUCT_NOT_FOUND", status=404)
                zone.assigned_product_id = prod.id
            else:
                zone.assigned_product_id = None

        if 'expected_capacity' in data:
            try:
                cap = Decimal(str(data['expected_capacity'])).quantize(Decimal('0.01'))
                if cap < Decimal('0.00'):
                    raise ValueError()
                zone.expected_capacity = cap
            except Exception:
                raise APIError("Field 'expected_capacity' must be a non-negative decimal.", code="INVALID_CAPACITY", status=400)

        if 'target_facings' in data:
            try:
                facings = int(data['target_facings'])
                if facings < 0:
                    raise ValueError()
                zone.target_facings = facings
            except Exception:
                raise APIError("Field 'target_facings' must be a non-negative integer.", code="INVALID_FACINGS", status=400)

        if 'reorder_threshold' in data:
            try:
                threshold = Decimal(str(data['reorder_threshold'])).quantize(Decimal('0.01'))
                if threshold < Decimal('0.00'):
                    raise ValueError()
                zone.reorder_threshold = threshold
            except Exception:
                raise APIError("Field 'reorder_threshold' must be a non-negative decimal.", code="INVALID_REORDER_THRESHOLD", status=400)

        if 'notes' in data:
            zone.notes = data['notes']

        zone.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Log Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="SHELF_ZONE_UPDATED",
            entity_type="business_shelf_zone",
            entity_id=zone.id,
            before_state=before_state,
            after_state=zone.serialize(),
            reason=f"Updated shelf zone {zone.zone_code}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return zone

    @classmethod
    def deactivate_shelf_zone(
        cls,
        workspace_id: str,
        zone_id: str,
        actor_user_id: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessShelfZone:
        """
        Deactivates a shelf zone fixture.
        """
        zone = cls.get_shelf_zone_by_id(workspace_id, zone_id)
        before_state = zone.serialize()

        zone.status = 'INACTIVE'
        zone.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="SHELF_ZONE_DEACTIVATED",
            entity_type="business_shelf_zone",
            entity_id=zone.id,
            before_state=before_state,
            after_state=zone.serialize(),
            reason=reason or f"Deactivated shelf zone {zone.zone_code}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return zone
