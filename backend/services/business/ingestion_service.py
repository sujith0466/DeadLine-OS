"""
DeadlineOS Business OS — Ingestion Service
==========================================
Coordinates raw artifact validation, object storage persistence,
duplicate fingerprinting, and audit logging.
"""

from database.db import db
from models.business import IngestionArtifact
from services.business.storage_service import StorageService
from services.business.audit_service import AuditService
from utils.errors import APIError
import uuid


class IngestionService:
    @staticmethod
    def store_artifact(
        workspace_id: str,
        uploader_user_id: str,
        file_bytes: bytes,
        filename: str,
        content_type: str = None,
        artifact_type: str = 'DOCUMENT',
        ip_address: str = None,
        user_agent: str = None
    ) -> IngestionArtifact:
        # 1. Validate file payload
        val_res = StorageService.validate_file(file_bytes, filename, content_type)
        sha256_hash = val_res['sha256']
        mime_type = val_res['mime_type']
        size_bytes = val_res['size_bytes']

        # 2. Check for duplicate SHA-256 within the active workspace
        existing_duplicate = IngestionArtifact.query.filter(
            IngestionArtifact.workspace_id == workspace_id,
            IngestionArtifact.sha256_hash == sha256_hash,
            IngestionArtifact.status.in_(['STORED', 'PROCESSED'])
        ).first()

        artifact_id = str(uuid.uuid4())
        storage_path = StorageService.generate_storage_path(workspace_id, artifact_id, filename)

        # 3. Create Artifact record
        artifact = IngestionArtifact(
            id=artifact_id,
            workspace_id=workspace_id,
            uploader_user_id=uploader_user_id,
            artifact_type=artifact_type.upper(),
            storage_path=storage_path,
            file_name=filename,
            file_size_bytes=size_bytes,
            mime_type=mime_type,
            sha256_hash=sha256_hash,
            status='STORED'
        )
        db.session.add(artifact)
        db.session.commit()

        # 4. Log Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=uploader_user_id,
            action='ARTIFACT_STORED',
            entity_type='INGESTION_ARTIFACT',
            entity_id=artifact.id,
            after_state=artifact.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return artifact, existing_duplicate is not None
