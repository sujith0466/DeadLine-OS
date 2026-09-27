"""
DeadlineOS Business OS — Visual Observation Model (Phase C4.1)
==============================================================
SQLAlchemy ORM model for `business_visual_observations`.
Represents immutable, probabilistic computer vision inferences, detected items,
bounding boxes, visual counts, and anomaly records.
"""

import uuid
from datetime import datetime, timezone
from database.db import db


class BusinessVisualObservation(db.Model):
    """
    Represents an inference record captured by a camera/sensor observing a physical shelf.
    Probabilistic sensor observation — NEVER direct authoritative inventory truth.
    """
    __tablename__ = 'business_visual_observations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    location_id = db.Column(
        db.String(36),
        db.ForeignKey('business_locations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    shelf_zone_id = db.Column(
        db.String(36),
        db.ForeignKey('business_shelf_zones.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    artifact_id = db.Column(
        db.String(36),
        db.ForeignKey('business_ingestion_artifacts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    capture_timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    capture_device = db.Column(db.String(100), nullable=True)  # e.g., "CAM-AISLE-01", "MOBILE_IOS"

    # Model Provenance
    model_provider = db.Column(db.String(50), nullable=False, default='gemini')
    model_name = db.Column(db.String(100), nullable=False, default='gemini-2.0-flash')
    inference_latency_ms = db.Column(db.Integer, nullable=True)

    # Detected items array with bounding boxes, labels, confidence
    detected_items = db.Column(db.JSON, nullable=False, default=list)
    matched_product_id = db.Column(
        db.String(36),
        db.ForeignKey('business_products.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Quantitative Visual Estimates
    visual_count = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    visual_facings = db.Column(db.Integer, nullable=False, default=0)
    overall_confidence = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)

    # Anomaly Status
    anomaly_detected = db.Column(db.Boolean, nullable=False, default=False, index=True)
    anomaly_type = db.Column(db.String(50), nullable=False, default='NONE')
    # NONE, EMPTY_SHELF, MISPLACED_PRODUCT, OUT_OF_STOCK, FACING_DEFICIT, UNKNOWN_OBJECT, DAMAGED_PACKAGING

    # Snapshot of System Inventory at Capture Time
    system_stock_at_capture = db.Column(db.Numeric(15, 2), nullable=True)
    discrepancy_quantity = db.Column(db.Numeric(15, 2), nullable=True)

    # Review Lifecycle
    status = db.Column(db.String(30), nullable=False, default='PROCESSED', index=True)
    # PROCESSED, REVIEW_REQUIRED, RECONCILED, DISMISSED

    staged_extraction_id = db.Column(
        db.String(36),
        db.ForeignKey('business_staged_extractions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    operational_alert_id = db.Column(
        db.String(36),
        db.ForeignKey('business_operational_alerts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    reviewed_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)

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

    __table_args__ = (
        db.Index('idx_biz_obs_ws_loc_time', 'workspace_id', 'location_id', 'capture_timestamp'),
        db.Index('idx_biz_obs_ws_zone', 'workspace_id', 'shelf_zone_id'),
        db.Index('idx_biz_obs_ws_anomaly', 'workspace_id', 'anomaly_detected', 'status'),
        db.Index('idx_biz_obs_ws_prod', 'workspace_id', 'matched_product_id'),
        db.Index('idx_biz_obs_ws_artifact', 'workspace_id', 'artifact_id'),
        db.CheckConstraint("visual_count >= 0", name='chk_biz_obs_count'),
        db.CheckConstraint("visual_facings >= 0", name='chk_biz_obs_facings'),
        db.CheckConstraint("overall_confidence >= 0 AND overall_confidence <= 100", name='chk_biz_obs_conf'),
        db.CheckConstraint("status IN ('PROCESSED', 'REVIEW_REQUIRED', 'RECONCILED', 'DISMISSED')", name='chk_biz_obs_status'),
        db.CheckConstraint("anomaly_type IN ('NONE', 'EMPTY_SHELF', 'MISPLACED_PRODUCT', 'OUT_OF_STOCK', 'FACING_DEFICIT', 'UNKNOWN_OBJECT', 'DAMAGED_PACKAGING')", name='chk_biz_obs_anomaly_type')
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('visual_observations', lazy='dynamic', cascade='all, delete-orphan'))
    location = db.relationship('BusinessLocation', backref=db.backref('visual_observations', lazy='dynamic', cascade='all, delete-orphan'))
    shelf_zone = db.relationship('BusinessShelfZone', backref=db.backref('observations', lazy='dynamic'))
    artifact = db.relationship('IngestionArtifact', backref=db.backref('visual_observations', lazy='dynamic'))
    matched_product = db.relationship('BusinessProduct', backref=db.backref('visual_observations', lazy='dynamic'))
    staged_extraction = db.relationship('StagedExtraction', backref=db.backref('source_visual_observations', lazy='dynamic'))
    operational_alert = db.relationship('BusinessOperationalAlert', backref=db.backref('source_visual_observations', lazy='dynamic'))
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_user_id])

    def serialize(self) -> dict:
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'shelf_zone_id': self.shelf_zone_id,
            'shelf_zone_code': self.shelf_zone.zone_code if self.shelf_zone else None,
            'artifact_id': self.artifact_id,
            'capture_timestamp': self.capture_timestamp.isoformat() if self.capture_timestamp else None,
            'capture_device': self.capture_device,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'inference_latency_ms': self.inference_latency_ms,
            'detected_items': self.detected_items,
            'matched_product_id': self.matched_product_id,
            'matched_product_sku': self.matched_product.sku if self.matched_product else None,
            'matched_product_name': self.matched_product.name if self.matched_product else None,
            'visual_count': str(self.visual_count),
            'visual_facings': self.visual_facings,
            'overall_confidence': str(self.overall_confidence),
            'anomaly_detected': self.anomaly_detected,
            'anomaly_type': self.anomaly_type,
            'system_stock_at_capture': str(self.system_stock_at_capture) if self.system_stock_at_capture is not None else None,
            'discrepancy_quantity': str(self.discrepancy_quantity) if self.discrepancy_quantity is not None else None,
            'status': self.status,
            'staged_extraction_id': self.staged_extraction_id,
            'operational_alert_id': self.operational_alert_id,
            'reviewed_by_user_id': self.reviewed_by_user_id,
            'reviewed_by_name': self.reviewer.full_name if self.reviewer and self.reviewer.full_name else (self.reviewer.email if self.reviewer else None),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_notes': self.review_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
