"""
DeadlineOS Business OS — Camera Calibration Service (Phase C4.5)
================================================================
Authoritative service for ambient camera device registration, pairing token hashing,
optical spatial calibration, normalized coordinate validation, and ROI polygon mapping.
"""

import secrets
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from database.db import db
from models.business import (
    Workspace,
    BusinessLocation,
    BusinessShelfZone,
    BusinessCameraDevice,
    BusinessCameraCalibration
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class CameraCalibrationService:
    """
    Manages camera devices, pairing tokens, spatial calibration geometry,
    and deterministic bounding-box to shelf-zone mappings.
    """

    VALID_DEVICE_TYPES = {'FIXED_OVERHEAD', 'SHELF_EDGE', 'MOBILE_TERMINAL'}
    VALID_DEVICE_STATUSES = {'ACTIVE', 'INACTIVE', 'PAUSED'}
    MIN_POLYGON_VERTICES = 3
    MIN_POLYGON_AREA = 0.0001

    # ── Device Management ────────────────────────────────────────────────────────

    @classmethod
    def register_camera_device(
        cls,
        workspace_id: str,
        location_id: str,
        data: dict,
        actor_user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[BusinessCameraDevice, str]:
        """
        Registers an ambient camera or edge device.
        Generates a cryptographically secure pairing token, hashes it with SHA-256,
        persists the device, and logs an audit event. Returns the device and raw plaintext token once.
        """
        device_code = (data.get('device_code') or '').strip().upper()
        name = (data.get('name') or '').strip()
        device_type = (data.get('device_type') or 'SHELF_EDGE').strip().upper()

        if not device_code:
            raise APIError("device_code is required.", code="MISSING_DEVICE_CODE", status=400)
        if not name:
            raise APIError("name is required.", code="MISSING_DEVICE_NAME", status=400)
        if device_type not in cls.VALID_DEVICE_TYPES:
            raise APIError(f"Invalid device_type '{device_type}'. Allowed: {cls.VALID_DEVICE_TYPES}", code="INVALID_DEVICE_TYPE", status=400)

        # Validate location
        loc = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not loc:
            raise APIError("Active location not found in this workspace.", code="LOCATION_NOT_FOUND", status=404)

        # Check unique device_code in workspace
        existing = BusinessCameraDevice.query.filter_by(workspace_id=workspace_id, device_code=device_code).first()
        if existing:
            raise APIError(f"Device code '{device_code}' already exists in this workspace.", code="DUPLICATE_DEVICE_CODE", status=409)

        # Generate 256-bit cryptographically secure token
        raw_token = f"cam_live_{secrets.token_hex(24)}"
        token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

        device = BusinessCameraDevice(
            workspace_id=workspace_id,
            location_id=location_id,
            device_code=device_code,
            name=name,
            device_type=device_type,
            api_key_hash=token_hash,
            status='ACTIVE',
            firmware_version=data.get('firmware_version'),
            notes=data.get('notes')
        )
        db.session.add(device)
        db.session.flush()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='DEVICE_REGISTERED',
            entity_type='business_camera_device',
            entity_id=device.id,
            after_state={'device_code': device.device_code, 'name': device.name, 'device_type': device.device_type, 'location_id': location_id},
            reason=f"Registered camera device '{device.device_code}'",
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.commit()

        return device, raw_token

    @classmethod
    def deactivate_camera_device(
        cls,
        workspace_id: str,
        device_id: str,
        actor_user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessCameraDevice:
        """Deactivates a camera device, revoking all sync capabilities."""
        device = BusinessCameraDevice.query.filter_by(id=device_id, workspace_id=workspace_id).first()
        if not device:
            raise APIError("Camera device not found.", code="DEVICE_NOT_FOUND", status=404)

        device.status = 'INACTIVE'
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='DEVICE_DEACTIVATED',
            entity_type='business_camera_device',
            entity_id=device.id,
            after_state={'status': 'INACTIVE'},
            reason=f"Deactivated camera device '{device.device_code}'",
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.commit()
        return device

    @classmethod
    def list_camera_devices(
        cls,
        workspace_id: str,
        location_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[dict], int]:
        """Lists and filters camera devices in a workspace."""
        query = BusinessCameraDevice.query.filter_by(workspace_id=workspace_id)
        if location_id:
            query = query.filter_by(location_id=location_id)
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        devices = query.order_by(BusinessCameraDevice.created_at.desc()).offset(offset).limit(limit).all()
        return [d.serialize() for d in devices], total

    @classmethod
    def get_camera_device(cls, workspace_id: str, device_id: str) -> BusinessCameraDevice:
        """Retrieves a single camera device."""
        device = BusinessCameraDevice.query.filter_by(id=device_id, workspace_id=workspace_id).first()
        if not device:
            raise APIError("Camera device not found.", code="DEVICE_NOT_FOUND", status=404)
        return device

    # ── Geometry & Spatial Calibration ──────────────────────────────────────────

    @classmethod
    def validate_polygon_geometry(cls, roi_polygon: Any) -> List[List[float]]:
        """
        Validates that roi_polygon is a valid, non-degenerate polygon of normalized coordinates [x, y] in [0.0, 1.0].
        """
        if not isinstance(roi_polygon, list) or len(roi_polygon) < cls.MIN_POLYGON_VERTICES:
            raise APIError(
                f"roi_polygon must be a list of at least {cls.MIN_POLYGON_VERTICES} coordinate pairs [[x0, y0], ...]",
                code="INVALID_POLYGON_STRUCTURE",
                status=400
            )

        clean_poly = []
        for idx, pt in enumerate(roi_polygon):
            if not isinstance(pt, (list, tuple)) or len(pt) != 2:
                raise APIError(f"Vertex {idx} must be a 2-element [x, y] coordinate pair.", code="INVALID_VERTEX", status=400)
            try:
                x = float(pt[0])
                y = float(pt[1])
            except (ValueError, TypeError):
                raise APIError(f"Vertex {idx} coordinates must be numbers.", code="INVALID_VERTEX_COORDINATES", status=400)

            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                raise APIError(f"Vertex {idx} coordinates [{x}, {y}] must be normalized within [0.0, 1.0].", code="COORDINATE_OUT_OF_BOUNDS", status=400)
            clean_poly.append([x, y])

        # Compute Polygon Area using Shoelace formula
        n = len(clean_poly)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += clean_poly[i][0] * clean_poly[j][1]
            area -= clean_poly[j][0] * clean_poly[i][1]
        area = abs(area) / 2.0

        if area < cls.MIN_POLYGON_AREA:
            raise APIError(f"Polygon area ({area:.6f}) is degenerate/too small. Minimum area required: {cls.MIN_POLYGON_AREA}", code="DEGENERATE_POLYGON", status=400)

        return clean_poly

    @classmethod
    def validate_facing_divisions(cls, facing_divisions: Any) -> List[float]:
        """Validates optional vertical/horizontal split lines."""
        if not facing_divisions:
            return []
        if not isinstance(facing_divisions, list):
            raise APIError("facing_divisions must be a list of normalized split values in [0.0, 1.0]", code="INVALID_FACINGS", status=400)

        clean_divs = []
        for div in facing_divisions:
            try:
                v = float(div)
            except (ValueError, TypeError):
                raise APIError("Facing division values must be numeric.", code="INVALID_FACING_VALUE", status=400)
            if not (0.0 <= v <= 1.0):
                raise APIError(f"Facing division value {v} must be normalized in [0.0, 1.0].", code="FACING_OUT_OF_BOUNDS", status=400)
            clean_divs.append(v)

        clean_divs.sort()
        return clean_divs

    @classmethod
    def create_or_update_calibration(
        cls,
        workspace_id: str,
        camera_device_id: str,
        shelf_zone_id: str,
        data: dict,
        actor_user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BusinessCameraCalibration:
        """
        Creates or updates a spatial calibration profile for a camera and shelf zone.
        If an ACTIVE profile exists, marks it SUPERSEDED and increments calibration_version.
        """
        device = BusinessCameraDevice.query.filter_by(id=camera_device_id, workspace_id=workspace_id).first()
        if not device:
            raise APIError("Camera device not found.", code="DEVICE_NOT_FOUND", status=404)

        zone = BusinessShelfZone.query.filter_by(id=shelf_zone_id, workspace_id=workspace_id).first()
        if not zone:
            raise APIError("Shelf zone not found.", code="ZONE_NOT_FOUND", status=404)

        if device.location_id != zone.location_id:
            raise APIError("Camera device and shelf zone must belong to the same location.", code="LOCATION_MISMATCH", status=400)

        clean_polygon = cls.validate_polygon_geometry(data.get('roi_polygon'))
        clean_facings = cls.validate_facing_divisions(data.get('facing_divisions'))

        # Find existing active calibration
        active_calib = BusinessCameraCalibration.query.filter_by(
            workspace_id=workspace_id,
            camera_device_id=camera_device_id,
            shelf_zone_id=shelf_zone_id,
            status='ACTIVE'
        ).first()

        if active_calib:
            active_calib.status = 'SUPERSEDED'
            new_version = active_calib.calibration_version + 1
            action = 'CAMERA_RECALIBRATED'
        else:
            new_version = 1
            action = 'CAMERA_CALIBRATED'

        new_calib = BusinessCameraCalibration(
            workspace_id=workspace_id,
            camera_device_id=camera_device_id,
            shelf_zone_id=shelf_zone_id,
            calibration_version=new_version,
            roi_polygon=clean_polygon,
            facing_divisions=clean_facings,
            homography_matrix=data.get('homography_matrix'),
            status='ACTIVE',
            calibrated_by_user_id=actor_user_id,
            notes=data.get('notes')
        )
        db.session.add(new_calib)
        db.session.flush()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type='business_camera_calibration',
            entity_id=new_calib.id,
            after_state={
                'camera_device_id': camera_device_id,
                'shelf_zone_id': shelf_zone_id,
                'calibration_version': new_version,
                'roi_polygon_vertex_count': len(clean_polygon)
            },
            reason=f"Calibrated zone '{zone.zone_code}' with camera '{device.device_code}' (v{new_version})",
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.commit()

        return new_calib

    @classmethod
    def get_active_calibration_for_zone(cls, workspace_id: str, shelf_zone_id: str) -> Optional[BusinessCameraCalibration]:
        """Retrieves active calibration for a shelf zone."""
        return BusinessCameraCalibration.query.filter_by(
            workspace_id=workspace_id,
            shelf_zone_id=shelf_zone_id,
            status='ACTIVE'
        ).first()

    @classmethod
    def list_calibrations(
        cls,
        workspace_id: str,
        camera_device_id: Optional[str] = None,
        shelf_zone_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[dict], int]:
        """Lists calibration profiles in a workspace."""
        query = BusinessCameraCalibration.query.filter_by(workspace_id=workspace_id)
        if camera_device_id:
            query = query.filter_by(camera_device_id=camera_device_id)
        if shelf_zone_id:
            query = query.filter_by(shelf_zone_id=shelf_zone_id)
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        calibs = query.order_by(BusinessCameraCalibration.created_at.desc()).offset(offset).limit(limit).all()
        return [c.serialize() for c in calibs], total

    # ── Spatial Point-In-Polygon Mapping ────────────────────────────────────────

    @staticmethod
    def point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
        """
        Ray-casting algorithm to test if a 2D point (x, y) is inside a polygon.
        """
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @classmethod
    def map_bounding_box_to_shelf_zone(
        cls,
        workspace_id: str,
        camera_device_id: str,
        bounding_box: List[float]
    ) -> Optional[Tuple[BusinessShelfZone, BusinessCameraCalibration]]:
        """
        Maps a normalized bounding box [ymin, xmin, ymax, xmax] to an active shelf zone
        calibrated for the camera device by evaluating box centroid against active ROI polygons.
        """
        if not bounding_box or len(bounding_box) != 4:
            return None

        ymin, xmin, ymax, xmax = [float(c) for c in bounding_box]
        center_x = (xmin + xmax) / 2.0
        center_y = (ymin + ymax) / 2.0

        active_calibs = BusinessCameraCalibration.query.filter_by(
            workspace_id=workspace_id,
            camera_device_id=camera_device_id,
            status='ACTIVE'
        ).all()

        for calib in active_calibs:
            if cls.point_in_polygon((center_x, center_y), calib.roi_polygon):
                zone = BusinessShelfZone.query.filter_by(id=calib.shelf_zone_id, workspace_id=workspace_id).first()
                if zone and zone.status == 'ACTIVE':
                    return zone, calib

        return None
