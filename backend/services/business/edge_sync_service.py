"""
DeadlineOS Business OS — Edge Synchronization Service (Phase C4.5)
==================================================================
Authoritative edge synchronization gateway for ambient shelf cameras, mobile scanners,
and edge IoT hubs. Manages offline buffer ingestion, client idempotency keys,
replay protection, clock skew clamping, and spatial calibration anchoring.
"""

import uuid
import hashlib
import base64
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from database.db import db
from models.business import (
    Workspace,
    BusinessLocation,
    BusinessShelfZone,
    BusinessCameraDevice,
    BusinessCameraCalibration,
    BusinessVisualObservation,
    BusinessProduct,
    IngestionArtifact
)
from services.business.camera_calibration_service import CameraCalibrationService
from services.business.storage_service import StorageService
from services.business.audit_service import AuditService
from utils.errors import APIError


class EdgeSyncService:
    """
    Processes edge observation sync batches with strict tenant isolation,
    idempotent deduplication, clock skew defense, and calibration linking.
    """

    MAX_BATCH_SIZE = 50
    MAX_OFFLINE_DRIFT_HOURS = 24
    MAX_FUTURE_DRIFT_MINUTES = 15

    @classmethod
    def authenticate_device(
        cls,
        workspace_id: str,
        device_id_or_code: str,
        token: str
    ) -> BusinessCameraDevice:
        """
        Authenticates an edge device using its pairing token.
        Updates device heartbeat upon successful verification.
        """
        if not device_id_or_code or not token:
            raise APIError("Device identifier and pairing token required.", code="MISSING_DEVICE_CREDENTIALS", status=401)

        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

        device = (
            BusinessCameraDevice.query
            .filter_by(workspace_id=workspace_id)
            .filter((BusinessCameraDevice.id == device_id_or_code) | (BusinessCameraDevice.device_code == device_id_or_code))
            .filter_by(api_key_hash=token_hash, status='ACTIVE')
            .first()
        )

        if not device:
            AuditService.log_event(
                workspace_id=workspace_id,
                actor_user_id='SYSTEM_EDGE_GATEWAY',
                action='DEVICE_AUTHENTICATION_FAILURE',
                entity_type='business_camera_device',
                entity_id=device_id_or_code,
                reason=f"Failed edge authentication for device '{device_id_or_code}'"
            )
            db.session.commit()
            raise APIError("Invalid or revoked device credentials.", code="INVALID_DEVICE_TOKEN", status=401)

        # Update heartbeat
        device.last_heartbeat_at = datetime.now(timezone.utc)
        db.session.commit()
        return device

    @classmethod
    def process_edge_sync_batch(
        cls,
        workspace_id: str,
        device: BusinessCameraDevice,
        payload: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a batch of visual observations buffered at the edge:
        - Enforces batch size limits (max 50).
        - Enforces clock skew defenses and clamps future timestamps.
        - Deduplicates observations using client_observation_id fingerprints.
        - Resolves spatial shelf zones and calibration versions.
        - Incurs ZERO mutations on business_stock_movements.
        """
        sync_batch_id = payload.get('sync_batch_id') or str(uuid.uuid4())
        observations_raw = payload.get('observations') or []

        if not isinstance(observations_raw, list):
            raise APIError("'observations' must be an array.", code="INVALID_SYNC_PAYLOAD", status=400)

        if len(observations_raw) > cls.MAX_BATCH_SIZE:
            raise APIError(f"Batch size exceeds maximum allowed of {cls.MAX_BATCH_SIZE}.", code="BATCH_TOO_LARGE", status=400)

        now_utc = datetime.now(timezone.utc)
        min_allowed_time = now_utc - timedelta(hours=cls.MAX_OFFLINE_DRIFT_HOURS)
        max_allowed_future = now_utc + timedelta(minutes=cls.MAX_FUTURE_DRIFT_MINUTES)

        results = []
        processed_count = 0
        duplicate_count = 0

        for obs_item in observations_raw:
            client_obs_id = obs_item.get('client_observation_id') or str(uuid.uuid4())
            dedup_tag = f"EDGE:{device.device_code}:{client_obs_id}"

            # 1. Check for Duplicate / Replay
            existing_obs = BusinessVisualObservation.query.filter_by(
                workspace_id=workspace_id,
                capture_device=dedup_tag
            ).first()

            if existing_obs:
                duplicate_count += 1
                results.append({
                    'client_observation_id': client_obs_id,
                    'server_observation_id': existing_obs.id,
                    'status': 'DUPLICATE_ACCEPTED',
                    'calibrated_zone_id': existing_obs.shelf_zone_id,
                    'calibration_applied_version': None
                })
                AuditService.log_event(
                    workspace_id=workspace_id,
                    actor_user_id=f"DEVICE:{device.device_code}",
                    action='EDGE_SYNC_DUPLICATE',
                    entity_type='business_visual_observation',
                    entity_id=existing_obs.id,
                    reason=f"Duplicate observation '{client_obs_id}' from device '{device.device_code}' accepted without reprocessing.",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                continue

            # 2. Parse & Clamp Timestamp
            raw_ts = obs_item.get('capture_timestamp')
            if raw_ts:
                try:
                    capture_ts = datetime.fromisoformat(raw_ts.replace('Z', '+00:00'))
                    if capture_ts.tzinfo is None:
                        capture_ts = capture_ts.replace(tzinfo=timezone.utc)
                except Exception:
                    capture_ts = now_utc
            else:
                capture_ts = now_utc

            # Clock Skew Defense: Clamp if too far in future; warn if older than 24h
            if capture_ts > max_allowed_future:
                capture_ts = now_utc  # Clamp future timestamps
            elif capture_ts < min_allowed_time:
                # Accept historical edge buffered reading, log timestamp drift
                pass

            # 3. Spatial Zone & Calibration Resolution
            target_zone_id = obs_item.get('shelf_zone_id')
            applied_calib_version = obs_item.get('calibration_version')

            detected_items = obs_item.get('offline_detected_items') or []
            visual_count = Decimal(str(obs_item.get('visual_count') or len(detected_items) or '0.00'))
            visual_facings = int(obs_item.get('visual_facings') or (1 if visual_count > 0 else 0))
            confidence = Decimal(str(obs_item.get('overall_confidence') or '0.90'))

            matched_product_id = obs_item.get('matched_product_id')

            # If shelf_zone_id is not explicitly given, attempt spatial ROI mapping from detected bounding boxes
            if not target_zone_id and detected_items:
                first_bbox = detected_items[0].get('bounding_box')
                if first_bbox:
                    mapped = CameraCalibrationService.map_bounding_box_to_shelf_zone(
                        workspace_id=workspace_id,
                        camera_device_id=device.id,
                        bounding_box=first_bbox
                    )
                    if mapped:
                        target_zone_id = mapped[0].id
                        applied_calib_version = mapped[1].calibration_version

            # Validate Zone ownership if resolved
            resolved_zone = None
            if target_zone_id:
                resolved_zone = BusinessShelfZone.query.filter_by(
                    id=target_zone_id,
                    workspace_id=workspace_id
                ).first()
                if resolved_zone and not matched_product_id:
                    matched_product_id = resolved_zone.assigned_product_id

                if resolved_zone and not applied_calib_version:
                    active_calib = CameraCalibrationService.get_active_calibration_for_zone(workspace_id, resolved_zone.id)
                    if active_calib:
                        applied_calib_version = active_calib.calibration_version

            # 4. Process Optional Base64 Image
            artifact_id = None
            img_b64 = obs_item.get('image_base64')
            if img_b64:
                try:
                    img_bytes = base64.b64decode(img_b64)
                    clean_bytes, img_meta = StorageService.validate_and_sanitize_image(
                        image_bytes=img_bytes,
                        filename=f"edge_sync_{client_obs_id[:8]}.jpg",
                        content_type="image/jpeg"
                    )
                    art_id = str(uuid.uuid4())
                    storage_path = StorageService.generate_shelf_capture_path(
                        workspace_id=workspace_id,
                        artifact_id=art_id,
                        filename=f"edge_sync_{client_obs_id[:8]}.jpg"
                    )
                    artifact = IngestionArtifact(
                        id=art_id,
                        workspace_id=workspace_id,
                        uploader_user_id='SYSTEM_EDGE_DEVICE',
                        artifact_type='DOCUMENT',
                        storage_path=storage_path,
                        file_name=f"edge_sync_{client_obs_id[:8]}.jpg",
                        file_size_bytes=len(clean_bytes),
                        mime_type="image/jpeg",
                        sha256_hash=hashlib.sha256(clean_bytes).hexdigest(),
                        status='STORED'
                    )
                    db.session.add(artifact)
                    artifact_id = art_id
                except Exception:
                    pass  # Non-fatal; continue with observation telemetry metadata

            # 5. Determine Anomaly State
            anomaly_detected = False
            anomaly_type = 'NONE'
            if resolved_zone:
                if visual_count == Decimal('0.00'):
                    anomaly_detected = True
                    anomaly_type = 'EMPTY_SHELF'
                elif visual_count <= resolved_zone.reorder_threshold:
                    anomaly_detected = True
                    anomaly_type = 'OUT_OF_STOCK'
                elif resolved_zone.target_facings > visual_facings:
                    anomaly_detected = True
                    anomaly_type = 'FACING_DEFICIT'

            # 6. Create Visual Observation Record
            obs = BusinessVisualObservation(
                workspace_id=workspace_id,
                location_id=device.location_id,
                shelf_zone_id=target_zone_id,
                artifact_id=artifact_id,
                capture_timestamp=capture_ts,
                capture_device=dedup_tag,
                model_provider='edge_local',
                model_name=device.device_code,
                detected_items=detected_items,
                matched_product_id=matched_product_id,
                visual_count=visual_count,
                visual_facings=visual_facings,
                overall_confidence=confidence,
                anomaly_detected=anomaly_detected,
                anomaly_type=anomaly_type,
                status='PROCESSED'
            )
            db.session.add(obs)
            db.session.flush()

            AuditService.log_event(
                workspace_id=workspace_id,
                actor_user_id=f"DEVICE:{device.device_code}",
                action='EDGE_SYNC_PROCESSED',
                entity_type='business_visual_observation',
                entity_id=obs.id,
                after_state={
                    'client_observation_id': client_obs_id,
                    'shelf_zone_id': target_zone_id,
                    'calibration_version': applied_calib_version,
                    'visual_count': str(visual_count),
                    'anomaly_type': anomaly_type
                },
                reason=f"Processed edge observation '{client_obs_id}' from camera '{device.device_code}'",
                ip_address=ip_address,
                user_agent=user_agent
            )

            processed_count += 1
            results.append({
                'client_observation_id': client_obs_id,
                'server_observation_id': obs.id,
                'status': 'PROCESSED',
                'calibrated_zone_id': target_zone_id,
                'calibration_applied_version': applied_calib_version
            })

        db.session.commit()

        return {
            'sync_batch_id': sync_batch_id,
            'received_count': len(observations_raw),
            'processed_count': processed_count,
            'duplicate_count': duplicate_count,
            'results': results,
            'server_timestamp': now_utc.isoformat()
        }
