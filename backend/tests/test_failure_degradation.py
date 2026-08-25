"""
DeadlineOS — Failure & Degradation Testing (M14)
=================================================
Verifies resilience against external AI provider outages, database drops, and invalid payloads.
"""

from unittest.mock import MagicMock
from services.ai.provider import HybridFailoverAIProvider


def test_ai_outage_does_not_break_system():
    """Verify that complete AI outage returns safe deterministic fallback without crashing."""
    mock_primary = MagicMock()
    mock_primary.generate_structured.side_effect = ConnectionError("OpenRouter unreachable")

    mock_fallback = MagicMock()
    mock_fallback.generate_structured.side_effect = TimeoutError("Gemini API timed out")

    hybrid = HybridFailoverAIProvider(primary=mock_primary, fallback=mock_fallback)
    schema = {"type": "object", "properties": {"score": {"type": "integer"}}}

    res = hybrid.generate_structured("sys", "user", schema)
    assert res is not None
    assert res.get("_fallback_used") is True
    assert res.get("_provider") == "deterministic_fallback"


def test_invalid_json_payload_handled_gracefully(client, mock_auth_headers):
    """Verify malformed JSON requests return standard 400 response with error information."""
    res = client.post(
        "/api/tasks",
        data="not a valid json string",
        headers={"Content-Type": "application/json", **mock_auth_headers}
    )
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
