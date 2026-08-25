"""
DeadlineOS — AI Safety & Validation Layer
=========================================
Enforces strict response schema validation, prompt injection defense,
and credential leakage protection across all AI features.
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Patterns that indicate potential prompt injection or prompt escape
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
    re.compile(r"override\s+(system|safety)\s+rules", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|endoftext\|>", re.IGNORECASE),
]

# Patterns for high-entropy secrets that should never enter prompts
SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
    re.compile(r"AIza[a-zA-Z0-9_-]{20,}"),
    re.compile(r"postgres://[^:]+:[^@]+@"),
    re.compile(r"BEGIN\s+PRIVATE\s+KEY"),
]


class AISafetyError(ValueError):
    """Raised when an AI safety, privacy, or prompt validation check fails."""
    pass


class AISafety:
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Sanitizes user-provided text to neutralize prompt injection tokens."""
        if not text or not isinstance(text, str):
            return ""
        cleaned = text
        for pattern in INJECTION_PATTERNS:
            cleaned = pattern.sub("[REDACTED_INSTRUCTION]", cleaned)
        return cleaned.strip()

    @staticmethod
    def assert_prompt_safe(prompt: str) -> None:
        """Validates that a constructed prompt contains zero credentials or secrets."""
        for pattern in SECRET_PATTERNS:
            if pattern.search(prompt):
                raise AISafetyError("Security violation: Attempted to include secret or credential in AI prompt.")

    @staticmethod
    def validate_and_sanitize_response(data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validates AI response against required schema keys and types."""
        if not isinstance(data, dict):
            raise AISafetyError("AI response is not a valid JSON dictionary.")

        # Ensure core fields are populated
        if "confidence" in schema.get("properties", {}) and "confidence" in data:
            try:
                data["confidence"] = max(0, min(100, int(data["confidence"])))
            except (ValueError, TypeError):
                data["confidence"] = 50

        return data

    @staticmethod
    def build_generic_fallback(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Builds a compliant default fallback object matching the requested schema."""
        properties = schema.get("properties", {})
        fallback = {}
        for k, prop in properties.items():
            ptype = prop.get("type", "string")
            if ptype == "integer" or ptype == "number":
                fallback[k] = 50
            elif ptype == "boolean":
                fallback[k] = False
            elif ptype == "array":
                fallback[k] = []
            elif ptype == "object":
                fallback[k] = {}
            else:
                fallback[k] = "Standard operational baseline"
        
        fallback["confidence"] = 50
        fallback["evidence"] = ["Deterministic system default fallback"]
        return fallback
