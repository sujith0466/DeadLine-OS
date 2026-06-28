import time
import logging
from typing import Optional, Dict, Any
from database.db import db
from models.telemetry import AgentExecutionLog

logger = logging.getLogger(__name__)

class TelemetryService:
    @staticmethod
    def log_execution(
        agent_name: str, 
        action: str, 
        status: str, 
        start_time: float, 
        confidence: int = 0, 
        metadata: Optional[Dict[str, Any]] = None,
        user_id: str = None
    ):
        """Persists agent execution data for downstream analytics."""
        try:
            from flask import g
            uid = user_id or getattr(g, "user_id", None)
            duration_ms = int((time.time() - start_time) * 1000)
            log = AgentExecutionLog(
                user_id=uid,
                agent_name=agent_name,
                action=action,
                status=status,
                confidence=confidence,
                execution_time_ms=duration_ms,
                metadata_payload=metadata or {}
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error("Failed to log agent execution telemetry: %s", e)
