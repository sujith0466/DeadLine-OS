"""
DeadlineOS Business OS — Ingestion Artifact Model
=================================================
Stores metadata and object storage pointers for raw documents,
audio recordings, and raw text submissions.
"""

from database.db import db
from datetime import datetime, timezone
import uuid


class IngestionArtifact(db.Model):
    __tablename__ = 'business_ingestion_artifacts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    uploader_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    artifact_type = db.Column(db.String(20), nullable=False)  # DOCUMENT, AUDIO, TEXT_SNIPPET
    storage_path = db.Column(db.String(500), nullable=False)  # Relative cloud bucket key
    file_name = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False, default=0)
    mime_type = db.Column(db.String(100), nullable=False)
    sha256_hash = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='STORED')  # STORED, PROCESSED, FAILED, ARCHIVED

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    workspace = db.relationship('Workspace', backref=db.backref('artifacts', cascade='all, delete-orphan', lazy='dynamic'))
    uploader = db.relationship('User', backref=db.backref('uploaded_artifacts', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'uploader_user_id': self.uploader_user_id,
            'artifact_type': self.artifact_type,
            'storage_path': self.storage_path,
            'file_name': self.file_name,
            'file_size_bytes': self.file_size_bytes,
            'mime_type': self.mime_type,
            'sha256_hash': self.sha256_hash,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
