import re
from database.db import db
from models.intelligence import CommandLog
from typing import Dict, Any

class LearningService:
    """
    Logs low-confidence and unknown commands anonymously for local intelligence improvement.
    """
    
    @classmethod
    def sanitize_transcript(cls, text: str) -> str:
        if not text:
            return ""
        # Redact common sensitive patterns (basic implementation)
        text = re.sub(r'(?i)(password|pass|jwt|token|secret)[\s:=]+[\w\-._]+', r'\1 [REDACTED]', text)
        return text

    @classmethod
    def log_command(cls, user_id: str, transcript: str, detected_intent: str, confidence: float, source: str, execution_outcome: str):
        if not transcript or len(transcript.strip()) == 0:
            return
            
        safe_transcript = cls.sanitize_transcript(transcript)
            
        try:
            log_entry = CommandLog(
                user_id=user_id,
                source=source,
                transcript=safe_transcript,
                detected_intent=detected_intent,
                confidence_score=confidence,
                execution_outcome=execution_outcome
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to log learning data: {e}")
            db.session.rollback()

    @classmethod
    def log_suggestion_outcome(cls, user_id: str, suggestion_id: str, source: str, accepted: bool):
        try:
            outcome = "accepted_suggestion" if accepted else "rejected_suggestion"
            log_entry = CommandLog(
                user_id=user_id,
                source=source,
                transcript=f"Suggestion interaction: {suggestion_id}",
                detected_intent="system_suggestion",
                confidence_score=100.0,
                execution_outcome=outcome
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to log suggestion outcome: {e}")
            db.session.rollback()

    @classmethod
    def log_correction(cls, user_id: str, original_transcript: str, corrected_intent: str, source: str):
        try:
            safe_transcript = cls.sanitize_transcript(original_transcript)
            log_entry = CommandLog(
                user_id=user_id,
                source=source,
                transcript=safe_transcript,
                detected_intent=corrected_intent,
                confidence_score=100.0,
                execution_outcome="user_correction"
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to log correction: {e}")
            db.session.rollback()
