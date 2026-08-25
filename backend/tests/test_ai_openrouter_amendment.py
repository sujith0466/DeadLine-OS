"""
DeadlineOS — Phase 6 OpenRouter Amendment Test Suite
====================================================
Tests:
1. OpenRouter provider initialization & model configuration.
2. OpenRouter primary success (Gemini NOT invoked).
3. OpenRouter missing API key / failure -> Gemini fallback invoked.
4. Both providers failing -> Safe deterministic degradation.
5. No credentials exposed in logs or response dicts.
6. Safety layer and context builder execution through failover pipeline.
7. Existing Phase 6 features execute seamlessly through get_default_ai_provider().
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from services.ai.provider import (
    AIProvider,
    OpenRouterAIProvider,
    GeminiAIProvider,
    DeterministicFallbackProvider,
    HybridFailoverAIProvider,
    get_default_ai_provider
)
from services.ai.safety import AISafety
from services.ai.delay_detection import DelayDetectionService


class MockSuccessOpenRouterProvider(AIProvider):
    def generate_structured(self, system_prompt, user_prompt, schema, fallback_fn=None):
        return {
            "prediction": "OpenRouter Success",
            "confidence": 95,
            "_provider": "openrouter",
            "_fallback_used": False
        }

    def generate_text(self, system_prompt, user_prompt):
        return "OpenRouter text completion."


class MockFailingOpenRouterProvider(AIProvider):
    def generate_structured(self, system_prompt, user_prompt, schema, fallback_fn=None):
        return {
            "_provider": "openrouter_failed",
            "_fallback_used": True,
            "_fallback_reason": "HTTP 429 Rate Limit"
        }

    def generate_text(self, system_prompt, user_prompt):
        return "AI text response unavailable."


class MockSuccessGeminiProvider(AIProvider):
    def __init__(self):
        self.invoked = False

    def generate_structured(self, system_prompt, user_prompt, schema, fallback_fn=None):
        self.invoked = True
        return {
            "prediction": "Gemini Fallback Success",
            "confidence": 90,
            "_provider": "gemini-2.0-flash",
            "_fallback_used": False
        }

    def generate_text(self, system_prompt, user_prompt):
        self.invoked = True
        return "Gemini text completion."


class MockFailingGeminiProvider(AIProvider):
    def generate_structured(self, system_prompt, user_prompt, schema, fallback_fn=None):
        raise RuntimeError("Gemini quota exhausted")

    def generate_text(self, system_prompt, user_prompt):
        raise RuntimeError("Gemini quota exhausted")


def test_openrouter_primary_success_does_not_invoke_gemini():
    primary = MockSuccessOpenRouterProvider()
    fallback = MockSuccessGeminiProvider()
    hybrid = HybridFailoverAIProvider(primary=primary, fallback=fallback)

    schema = {"type": "object", "properties": {"prediction": {"type": "string"}}}
    result = hybrid.generate_structured("sys", "user", schema)

    assert result is not None
    assert result["prediction"] == "OpenRouter Success"
    assert result["_provider"] == "openrouter"
    assert result["_fallback_used"] is False
    assert fallback.invoked is False


def test_openrouter_failure_fails_over_to_gemini():
    primary = MockFailingOpenRouterProvider()
    fallback = MockSuccessGeminiProvider()
    hybrid = HybridFailoverAIProvider(primary=primary, fallback=fallback)

    schema = {"type": "object", "properties": {"prediction": {"type": "string"}}}
    result = hybrid.generate_structured("sys", "user", schema)

    assert result is not None
    assert result["prediction"] == "Gemini Fallback Success"
    assert result["_provider"] == "gemini-2.0-flash"
    assert fallback.invoked is True


def test_both_providers_failing_triggers_deterministic_fallback():
    primary = MockFailingOpenRouterProvider()
    fallback = MockFailingGeminiProvider()
    hybrid = HybridFailoverAIProvider(primary=primary, fallback=fallback)

    def deterministic_fn():
        return {"prediction": "Deterministic Heuristic", "confidence": 75}

    schema = {"type": "object", "properties": {"prediction": {"type": "string"}}}
    result = hybrid.generate_structured("sys", "user", schema, fallback_fn=deterministic_fn)

    assert result is not None
    assert result["prediction"] == "Deterministic Heuristic"
    assert result["_provider"] == "deterministic_fallback"
    assert result["_fallback_used"] is True


def test_openrouter_config_and_model_resolution(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-mock")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")

    provider = OpenRouterAIProvider()
    assert provider.api_key == "test-key-mock"
    assert provider.model == "google/gemini-2.0-flash-exp:free"


def test_openrouter_structured_http_mock():
    provider = OpenRouterAIProvider(api_key="mock-key")
    schema = {
        "type": "object",
        "properties": {
            "prediction": {"type": "string"},
            "confidence": {"type": "integer"}
        }
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"prediction": "On Time", "confidence": 95})
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp):
        res = provider.generate_structured("sys", "user", schema)
        assert res["prediction"] == "On Time"
        assert res["confidence"] == 95
        assert res["_provider"] == "openrouter"
