"""
DeadlineOS Business OS — Staged Extraction Model
================================================
Stores candidate business records extracted from artifacts or text
awaiting human-in-the-loop verification.
"""

from database.db import db
from datetime import datetime, timezone
import uuid


class StagedExtraction(db.Model):
    __tablename__ = 'business_staged_extractions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    artifact_id = db.Column(
        db.String(36),
        db.ForeignKey('business_ingestion_artifacts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    created_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    reviewed_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    source_channel = db.Column(db.String(20), nullable=False)  # TEXT_PROMPT, VOICE_AUDIO, DOCUMENT_UPLOAD
    candidate_type = db.Column(db.String(50), nullable=False, default='EXPENSE')  # EXPENSE, INVOICE_RECEIVABLE, INVOICE_PAYABLE, PAYMENT_RECORD, NOTE
    status = db.Column(db.String(20), nullable=False, default='NEEDS_REVIEW', index=True)  # RECEIVED, PROCESSING, EXTRACTED, NEEDS_REVIEW, CONFIRMED, REJECTED, FAILED, EXPIRED

    raw_extracted_data = db.Column(db.JSON, nullable=True)
    normalized_data = db.Column(db.JSON, nullable=False, default=dict)
    confidence_score = db.Column(db.Integer, nullable=False, default=100)
    confidence_breakdown = db.Column(db.JSON, nullable=True)
    provenance_metadata = db.Column(db.JSON, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

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

    workspace = db.relationship('Workspace', backref=db.backref('staged_extractions', cascade='all, delete-orphan', lazy='dynamic'))
    artifact = db.relationship('IngestionArtifact', backref=db.backref('extractions', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('created_staged_items', lazy='dynamic'))
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_user_id], backref=db.backref('reviewed_staged_items', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'artifact_id': self.artifact_id,
            'created_by_user_id': self.created_by_user_id,
            'reviewed_by_user_id': self.reviewed_by_user_id,
            'source_channel': self.source_channel,
            'candidate_type': self.candidate_type,
            'status': self.status,
            'raw_extracted_data': self.raw_extracted_data,
            'normalized_data': self.normalized_data,
            'confidence_score': self.confidence_score,
            'confidence_breakdown': self.confidence_breakdown,
            'provenance_metadata': self.provenance_metadata,
            'rejection_reason': self.rejection_reason,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
