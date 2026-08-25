"""
DeadlineOS — Recovery Repository
================================
Data access layer for recovery audit records and user recovery preferences.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from database.db import db
from models.recovery import RecoveryRecord, RecoveryActionType
from utils.timezone import utc_now


class RecoveryRepository:
    """Repository for managing recovery audit records."""

    @classmethod
    def save_record(
        cls,
        user_id: str,
        action_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        schedule_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> RecoveryRecord:
        record = RecoveryRecord(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            schedule_id=schedule_id,
            details=details or {},
            created_at=utc_now()
        )
        db.session.add(record)
        db.session.commit()
        return record

    @classmethod
    def get_recent_records(cls, user_id: str, limit: int = 50) -> List[RecoveryRecord]:
        return (
            RecoveryRecord.query.filter_by(user_id=user_id)
            .order_by(RecoveryRecord.created_at.desc())
            .limit(limit)
            .all()
        )
