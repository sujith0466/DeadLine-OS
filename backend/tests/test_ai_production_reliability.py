"""
DeadlineOS — AI Production Reliability & Degradation Tests
===========================================================
Verifies OpenRouter Primary -> Gemini Fallback -> Deterministic Safe Fallback hierarchy.
"""

from unittest.mock import MagicMock, patch
from services.ai.provider import (
    HybridFailoverAIProvider,
    OpenRouterAIProvider,
    GeminiAIProvider,
    DeterministicFallbackProvider,
    get_default_ai_provider
)


def test_ai_provider_default_hierarchy():
    """Verify get_default_ai_provider constructs HybridFailover with OpenRouter primary and Gemini fallback."""
    provider = get_default_ai_provider()
    assert isinstance(provider, HybridFailoverAIProvider)
    assert isinstance(provider.primary, OpenRouterAIProvider)
    assert isinstance(provider.fallback, GeminiAIProvider)


def test_openrouter_primary_success():
    """Verify OpenRouter serves response as primary when available."""
    mock_primary = MagicMock()
    mock_primary.generate_structured.return_value = {
        "analysis": "Optimal",
        "_provider": "openrouter",
        "_fallback_used": False
    }
    mock_fallback = MagicMock()

    hybrid = HybridFailoverAIProvider(primary=mock_primary, fallback=mock_fallback)
    res = hybrid.generate_structured("sys", "user", {"type": "object"})

    assert res["_provider"] == "openrouter"
    assert res["_fallback_used"] is False
    mock_fallback.generate_structured.assert_not_called()


def test_openrouter_failover_to_gemini():
    """Verify fallback to Gemini when OpenRouter raises an exception or fails."""
    mock_primary = MagicMock()
    mock_primary.generate_structured.side_effect = RuntimeError("OpenRouter HTTP 429 Rate Limit")

    mock_fallback = MagicMock()
    mock_fallback.generate_structured.return_value = {
        "analysis": "Gemini Fallback Analysis",
        "_provider": "gemini-2.0-flash",
        "_fallback_used": False
    }

    hybrid = HybridFailoverAIProvider(primary=mock_primary, fallback=mock_fallback)
    res = hybrid.generate_structured("sys", "user", {"type": "object"})

    assert res["_provider"] == "gemini-2.0-flash"
    assert res["_fallback_triggered"] is True
    assert "429" in res["_primary_failure_reason"]


def test_both_providers_failover_to_deterministic():
    """Verify safe degradation to deterministic baseline when both LLMs are down."""
    mock_primary = MagicMock()
    mock_primary.generate_structured.side_effect = RuntimeError("OpenRouter offline")

    mock_fallback = MagicMock()
    mock_fallback.generate_structured.side_effect = RuntimeError("Gemini 503 Overloaded")

    def my_fallback():
        return {"action": "manual_review", "status": "safe"}

    hybrid = HybridFailoverAIProvider(primary=mock_primary, fallback=mock_fallback)
    res = hybrid.generate_structured("sys", "user", {"type": "object"}, fallback_fn=my_fallback)

    assert res["action"] == "manual_review"
    assert res["_provider"] == "deterministic_fallback"
    assert res["_fallback_used"] is True


def test_text_generation_failover_chain():
    """Verify text completion fails over from OpenRouter to Gemini to deterministic string."""
    mock_primary = MagicMock()
    mock_primary.generate_text.side_effect = Exception("Network timeout")

    mock_fallback = MagicMock()
    mock_fallback.generate_text.return_value = "Fallback recommendation."

    hybrid = HybridFailoverAIProvider(primary=mock_primary, fallback=mock_fallback)
    res = hybrid.generate_text("sys", "user")

    assert res == "Fallback recommendation."
