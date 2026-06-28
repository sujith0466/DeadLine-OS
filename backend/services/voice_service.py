"""
DeadlineOS — Voice Service
==========================
Receives transcripts, parses intent via VoiceCopilotAgent, and routes 
execution to the appropriate backend agents/services.
"""

from typing import Dict, Any
from services.local_intelligence.execution_engine import ExecutionEngine

class VoiceService:
    """
    Voice Intelligence interface. Acts as a thin client forwarding audio transcripts 
    to the Local Intelligence Engine.
    """

    @classmethod
    def process_voice_command(cls, transcript: str, gemini_service, user_id: str = None) -> Dict[str, Any]:
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        
        # Execute through the shared Intelligence Engine
        engine_result = ExecutionEngine.execute("voice", transcript, gemini_service, uid)
        
        return {
            "transcript": transcript,
            # Maintain backward compatibility with existing frontend expectations
            "nlu": {
                "intent": engine_result.get("intent"),
                "entities": engine_result.get("entities"),
                "confidence": engine_result.get("confidence"),
                "voice_response": engine_result.get("message")
            },
            "execution": {
                "status": engine_result.get("status"),
                "action": engine_result.get("action")
            },
            # Forward unified structure
            "structured_result": engine_result
        }

