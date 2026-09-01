"""
DeadlineOS Business OS — Location Service
==========================================
Business logic for physical operating facility and location registry.
"""

from database.db import db
from datetime import datetime, timezone
from models.business import BusinessLocation, BusinessEntity
from services.business.audit_service import AuditService
from utils.errors import APIError


class LocationService:
    VALID_TYPES = {'WAREHOUSE', 'STORE', 'BRANCH', 'OFFICE', 'STORAGE_UNIT'}
    VALID_STATUSES = {'ACTIVE', 'INACTIVE'}

    @staticmethod
    def create_location(
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessLocation:
        name = (data.get('name') or '').strip()
        if not name:
            raise APIError("Location 'name' is required.", "VALIDATION_ERROR", 400)

        existing = BusinessLocation.query.filter_by(workspace_id=workspace_id, name=name).first()
        if existing:
            raise APIError(f"Location with name '{name}' already exists in this workspace.", "DUPLICATE_LOCATION", 400)

        location_type = (data.get('location_type') or 'WAREHOUSE').upper()
        if location_type not in LocationService.VALID_TYPES:
            raise APIError(f"Invalid location_type '{location_type}'. Allowed: {LocationService.VALID_TYPES}", "VALIDATION_ERROR", 400)

        entity_id = data.get('entity_id')
        if entity_id:
            entity = BusinessEntity.query.filter_by(id=entity_id, workspace_id=workspace_id).first()
            if not entity:
                raise APIError("Referenced entity not found in this workspace.", "VALIDATION_ERROR", 400)

        location = BusinessLocation(
            workspace_id=workspace_id,
            entity_id=entity_id,
            name=name,
            location_type=location_type,
            address=data.get('address'),
            status='ACTIVE'
        )
        db.session.add(location)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LOCATION_CREATED",
            entity_type="business_location",
            entity_id=location.id,
            after_state=location.serialize(),
            reason="Physical location registered",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return location

    @staticmethod
    def get_locations(
        workspace_id: str,
        status: str = None,
        location_type: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = BusinessLocation.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter_by(status=status.upper())
        if location_type:
            query = query.filter_by(location_type=location_type.upper())

        total = query.count()
        locations = query.order_by(BusinessLocation.name.asc()).offset(offset).limit(min(limit, 100)).all()
        return [l.serialize() for l in locations], total

    @staticmethod
    def get_location_by_id(workspace_id: str, location_id: str) -> BusinessLocation:
        location = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id).first()
        if not location:
            raise APIError("Business location not found in this workspace.", "NOT_FOUND", 404)
        return location

    @staticmethod
    def update_location(
        workspace_id: str,
        actor_user_id: str,
        location_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessLocation:
        location = LocationService.get_location_by_id(workspace_id, location_id)
        before_state = location.serialize()

        if 'name' in data:
            new_name = (data['name'] or '').strip()
            if not new_name:
                raise APIError("Location 'name' cannot be empty.", "VALIDATION_ERROR", 400)
            if new_name != location.name:
                existing = BusinessLocation.query.filter_by(workspace_id=workspace_id, name=new_name).first()
                if existing:
                    raise APIError(f"Location with name '{new_name}' already exists.", "DUPLICATE_LOCATION", 400)
                location.name = new_name

        if 'location_type' in data:
            l_type = (data['location_type'] or '').upper()
            if l_type in LocationService.VALID_TYPES:
                location.location_type = l_type

        if 'address' in data:
            location.address = data['address']

        if 'status' in data:
            status = (data['status'] or '').upper()
            if status in LocationService.VALID_STATUSES:
                location.status = status

        location.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="LOCATION_UPDATED",
            entity_type="business_location",
            entity_id=location.id,
            before_state=before_state,
            after_state=location.serialize(),
            reason="Location details updated",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return location
