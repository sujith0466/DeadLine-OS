"""
DeadlineOS Business OS — Visual Ingestion Service (Phase C4.1 Foundation)
========================================================================
Coordinates secure image capture uploads, sanitization (EXIF stripping,
magic bytes, dimension/decompression limits), workspace-isolated object storage
persistence, artifact tracking, and initial visual observation record creation.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from database.db import db
from models.business import (
    Workspace,
    BusinessLocation,
    BusinessShelfZone,
    IngestionArtifact,
    BusinessVisualObservation,
    AuditEvent
)
from services.business.storage_service import StorageService
from services.business.shelf_zone_service import ShelfZoneService
from services.business.audit_service import AuditService
from utils.errors import APIError


class VisionIngestionService:
    """
    Manages secure visual media ingestion and observation record creation.
    """

    @classmethod
    def ingest_shelf_capture(
        cls,
        workspace_id: str,
        location_id: str,
        actor_user_id: str,
        image_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        shelf_zone_id: Optional[str] = None,
        capture_device: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Securely ingests a shelf capture photo:
        1. Validates workspace and location ownership.
        2. Validates optional shelf zone.
        3. Sanitizes image (dimension check, decompression bomb check, EXIF stripping).
        4. Persists IngestionArtifact with SHA-256 hash.
        5. Persists BusinessVisualObservation foundation record.
        6. Logs forensic audit event.
        7. Returns observation details and signed image URL.
        """
        # 1. Validate Workspace
        ws = db.session.get(Workspace, workspace_id)
        if not ws or ws.status != 'ACTIVE':
            raise APIError("Active workspace required for image ingestion.", code="INVALID_WORKSPACE", status=400)

        # 2. Validate Location
        location = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id, status='ACTIVE').first()
        if not location:
            raise APIError("Location not found or inactive in this workspace.", code="LOCATION_NOT_FOUND", status=404)

        # 3. Validate Shelf Zone if provided
        shelf_zone = None
        if shelf_zone_id:
            shelf_zone = BusinessShelfZone.query.filter_by(
                id=shelf_zone_id,
                workspace_id=workspace_id,
                location_id=location_id
            ).first()
            if not shelf_zone:
                raise APIError(
                    "Shelf zone not found or does not belong to the specified location in this workspace.",
                    code="ZONE_NOT_FOUND",
                    status=404
                )

        # 4. Sanitize and Validate Image
        clean_bytes, img_meta = StorageService.validate_and_sanitize_image(
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type
        )

        artifact_id = str(uuid.uuid4())
        storage_path = StorageService.generate_shelf_capture_path(
            workspace_id=workspace_id,
            artifact_id=artifact_id,
            filename=filename
        )

        # 5. Create IngestionArtifact
        artifact = IngestionArtifact(
            id=artifact_id,
            workspace_id=workspace_id,
            uploader_user_id=actor_user_id,
            artifact_type='DOCUMENT',  # Reuses existing artifact_type enum
            storage_path=storage_path,
            file_name=filename,
            file_size_bytes=img_meta['size_bytes'],
            mime_type=img_meta['mime_type'],
            sha256_hash=img_meta['sha256'],
            status='STORED'
        )
        db.session.add(artifact)

        # 6. Create Visual Observation Foundation Record (Inference populated in C4.2)
        observation = BusinessVisualObservation(
            workspace_id=workspace_id,
            location_id=location_id,
            shelf_zone_id=shelf_zone.id if shelf_zone else None,
            artifact_id=artifact.id,
            capture_timestamp=datetime.now(timezone.utc),
            capture_device=capture_device or "MANUAL_UPLOAD",
            model_provider="unprocessed",
            model_name="unprocessed",
            detected_items=[],
            matched_product_id=shelf_zone.assigned_product_id if shelf_zone else None,
            visual_count=Decimal('0.00'),
            visual_facings=0,
            overall_confidence=Decimal('0.00'),
            anomaly_detected=False,
            anomaly_type='NONE',
            status='PROCESSED'
        )
        db.session.add(observation)
        db.session.commit()

        # 7. Generate 15-Minute Signed URL
        signed_url = StorageService.generate_signed_download_url(storage_path, expires_in_seconds=900)

        # 8. Log Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="VISUAL_CAPTURE_INGESTED",
            entity_type="business_visual_observation",
            entity_id=observation.id,
            after_state={
                'observation_id': observation.id,
                'artifact_id': artifact.id,
                'location_id': location_id,
                'shelf_zone_id': shelf_zone.id if shelf_zone else None,
                'sha256': img_meta['sha256'],
                'size_bytes': img_meta['size_bytes']
            },
            reason=f"Ingested visual capture '{filename}' for location {location.name}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        res = observation.serialize()
        res['image_signed_url'] = signed_url
        res['artifact'] = artifact.serialize()
        return res

    @classmethod
    def get_observation_by_id(cls, workspace_id: str, observation_id: str) -> Dict[str, Any]:
        """
        Retrieves a visual observation and generates a time-limited signed URL for its image.
        """
        obs = BusinessVisualObservation.query.filter_by(id=observation_id, workspace_id=workspace_id).first()
        if not obs:
            raise APIError("Visual observation not found in this workspace.", code="OBSERVATION_NOT_FOUND", status=404)

        data = obs.serialize()
        if obs.artifact and obs.artifact.storage_path:
            data['image_signed_url'] = StorageService.generate_signed_download_url(
                obs.artifact.storage_path,
                expires_in_seconds=900
            )
        else:
            data['image_signed_url'] = None

        return data

    @classmethod
    def list_observations(
        cls,
        workspace_id: str,
        location_id: Optional[str] = None,
        shelf_zone_id: Optional[str] = None,
        anomaly_only: bool = False,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lists visual observations with filtering and pagination.
        """
        query = BusinessVisualObservation.query.filter_by(workspace_id=workspace_id)

        if location_id:
            query = query.filter_by(location_id=location_id)
        if shelf_zone_id:
            query = query.filter_by(shelf_zone_id=shelf_zone_id)
        if anomaly_only:
            query = query.filter_by(anomaly_detected=True)
        if status:
            query = query.filter_by(status=status.upper())

        total_count = query.count()
        observations = query.order_by(BusinessVisualObservation.capture_timestamp.desc()).offset(offset).limit(limit).all()

        results = []
        for obs in observations:
            item = obs.serialize()
            if obs.artifact and obs.artifact.storage_path:
                item['image_signed_url'] = StorageService.generate_signed_download_url(
                    obs.artifact.storage_path,
                    expires_in_seconds=900
                )
            results.append(item)

        return results, total_count
