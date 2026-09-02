"""
DeadlineOS Business OS — Exchange Rate Registry Model (Phase C3.1)
==================================================================
SQLAlchemy ORM model for `business_exchange_rates`.
Stores deterministic foreign exchange rates with provenance and historical lock dates.
"""

import uuid
from datetime import datetime, timezone, date
from database.db import db


class BusinessExchangeRate(db.Model):
    """
    Represents an authoritative exchange rate for a currency pair on a specific effective date.
    """
    __tablename__ = 'business_exchange_rates'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey('business_workspaces.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    from_currency = db.Column(db.String(3), nullable=False)
    to_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Numeric(18, 6), nullable=False)
    effective_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    rate_source = db.Column(db.String(30), nullable=False, default='MANUAL_OVERRIDE')
    notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
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
        db.UniqueConstraint('workspace_id', 'from_currency', 'to_currency', 'effective_date', name='uq_biz_fx_ws_curr_date'),
        db.Index('idx_biz_fx_ws_pair', 'workspace_id', 'from_currency', 'to_currency'),
        db.CheckConstraint('rate > 0', name='chk_biz_fx_rate_positive'),
    )

    # Relationships
    workspace = db.relationship('Workspace', backref=db.backref('exchange_rates', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('recorded_exchange_rates', lazy='dynamic'))

    def serialize(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'from_currency': self.from_currency,
            'to_currency': self.to_currency,
            'rate': str(self.rate),
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'rate_source': self.rate_source,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'creator_name': (self.creator.full_name or self.creator.email) if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
