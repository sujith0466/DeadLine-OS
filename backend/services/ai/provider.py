"""
DeadlineOS — AI Provider Abstraction & Failover Architecture
============================================================
Defines the AIProvider interface and concrete implementations:
  1. OpenRouterAIProvider  (PRIMARY - configurable model, default free tier)
  2. GeminiAIProvider      (FALLBACK - Google Generative AI)
  3. DeterministicFallbackProvider (OFFLINE / ZERO-LLM SAFE DEGRADATION)
  4. HybridFailoverAIProvider (Orchestrates OpenRouter -> Gemini -> Heuristic Fallback)
"""

import abc
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Callable
from utils.timezone import utc_now

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


class AIProvider(abc.ABC):
    """Abstract interface for all AI / LLM inference providers."""

    @abc.abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        fallback_fn: Optional[Callable[[], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generates schema-conforming structured JSON output."""
        pass

    @abc.abstractmethod
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Generates plain text completion."""
        pass


class OpenRouterAIProvider(AIProvider):
    """
    Primary AI Provider integrating OpenRouter API.
    Supports configurable models with default free tier routing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 15.0,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
        self.timeout = timeout
        self.base_url = base_url

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        fallback_fn: Optional[Callable[[], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        from services.ai.safety import AISafety

        AISafety.assert_prompt_safe(f"{system_prompt}\n{user_prompt}")

        if not self.api_key:
            logger.info("OpenRouter API key not configured. Passing to fallback.")
            if fallback_fn:
                return fallback_fn()
            return AISafety.build_generic_fallback(schema)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://deadlineos.com",
            "X-Title": "DeadlineOS"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nYou MUST respond strictly in valid JSON matching the schema."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            resp = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code != 200:
                error_msg = f"OpenRouter HTTP {resp.status_code}"
                logger.warning(f"{error_msg}: {resp.text[:120]}")
                raise RuntimeError(error_msg)

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("OpenRouter returned empty choices list.")

            content_text = choices[0].get("message", {}).get("content", "{}")
            parsed = json.loads(content_text)
            validated = AISafety.validate_and_sanitize_response(parsed, schema)
            validated["_provider"] = "openrouter"
            validated["_model"] = self.model
            validated["_fallback_used"] = False
            return validated
        except Exception as e:
            logger.warning(f"OpenRouter generation error: {e}")
            if fallback_fn:
                result = fallback_fn()
            else:
                result = AISafety.build_generic_fallback(schema)
            result["_provider"] = "openrouter_failed"
            result["_fallback_used"] = True
            result["_fallback_reason"] = str(e)
            return result

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        from services.ai.safety import AISafety

        AISafety.assert_prompt_safe(f"{system_prompt}\n{user_prompt}")

        if not self.api_key:
            return "OpenRouter API key not configured."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://deadlineos.com",
            "X-Title": "DeadlineOS"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            resp = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code != 200:
                raise RuntimeError(f"OpenRouter HTTP {resp.status_code}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenRouter text generation failed: {e}")
            return "AI text response unavailable."


class GeminiAIProvider(AIProvider):
    """Fallback AI Provider integrating Google Generative AI (Gemini 2.0)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model
        self._client = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        fallback_fn: Optional[Callable[[], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        from services.ai.safety import AISafety

        AISafety.assert_prompt_safe(f"{system_prompt}\n{user_prompt}")

        if not self._client or not self.api_key:
            logger.info("Gemini provider unavailable. Invoking deterministic fallback.")
            if fallback_fn:
                return fallback_fn()
            return AISafety.build_generic_fallback(schema)

        try:
            prompt_content = f"{system_prompt}\n\nUSER DATA:\n{user_prompt}\n\nRespond strictly in valid JSON conforming to the schema."
            response = self._client.generate_content(
                prompt_content,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = response.text or "{}"
            parsed = json.loads(raw_text)
            validated = AISafety.validate_and_sanitize_response(parsed, schema)
            validated["_provider"] = "gemini-2.0-flash"
            validated["_fallback_used"] = False
            return validated
        except Exception as e:
            logger.warning(f"Gemini generation error: {e}. Executing fallback.")
            if fallback_fn:
                result = fallback_fn()
            else:
                result = AISafety.build_generic_fallback(schema)
            result["_provider"] = "deterministic_fallback"
            result["_fallback_used"] = True
            result["_fallback_reason"] = str(e)
            return result

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        from services.ai.safety import AISafety
        AISafety.assert_prompt_safe(f"{system_prompt}\n{user_prompt}")

        if not self._client or not self.api_key:
            return "AI service is currently operating in deterministic offline mode."

        try:
            response = self._client.generate_content(f"{system_prompt}\n\n{user_prompt}")
            return response.text or ""
        except Exception as e:
            logger.warning(f"Gemini text generation failed: {e}")
            return "AI recommendation unavailable. Please review current tasks manually."


class DeterministicFallbackProvider(AIProvider):
    """Deterministic, zero-LLM provider for offline, testing, or high-reliability modes."""

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        fallback_fn: Optional[Callable[[], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        from services.ai.safety import AISafety
        if fallback_fn:
            result = fallback_fn()
        else:
            result = AISafety.build_generic_fallback(schema)
        result["_provider"] = "deterministic_heuristic"
        result["_fallback_used"] = True
        return result

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "Deterministic baseline response."


class HybridFailoverAIProvider(AIProvider):
    """
    Orchestrates the priority hierarchy:
      1. OpenRouter (PRIMARY)
      2. Gemini     (FALLBACK)
      3. Deterministic Heuristic Safe Degradation
    """

    def __init__(
        self,
        primary: Optional[AIProvider] = None,
        fallback: Optional[AIProvider] = None
    ):
        self.primary = primary or OpenRouterAIProvider()
        self.fallback = fallback or GeminiAIProvider()

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        fallback_fn: Optional[Callable[[], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        # 1. Attempt Primary (OpenRouter)
        try:
            primary_res = self.primary.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
                fallback_fn=None
            )
            # Check if primary succeeded without internal fallback triggering
            if primary_res and not primary_res.get("_fallback_used", False):
                return primary_res
            primary_error = primary_res.get("_fallback_reason", "OpenRouter unavailable")
        except Exception as e:
            primary_error = str(e)
            logger.warning(f"Primary AI Provider failed: {primary_error}")

        # 2. Attempt Fallback (Gemini)
        logger.info(f"Failing over to Gemini fallback provider (reason: {primary_error})")
        try:
            fallback_res = self.fallback.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
                fallback_fn=fallback_fn
            )
            if fallback_res and not fallback_res.get("_fallback_used", False):
                fallback_res["_fallback_triggered"] = True
                fallback_res["_primary_failure_reason"] = primary_error
                return fallback_res
            return fallback_res
        except Exception as e:
            logger.warning(f"Fallback AI Provider failed: {e}. Executing final safe degradation.")
            from services.ai.safety import AISafety
            if fallback_fn:
                res = fallback_fn()
            else:
                res = AISafety.build_generic_fallback(schema)
            res["_provider"] = "deterministic_fallback"
            res["_fallback_used"] = True
            res["_fallback_reason"] = f"Primary: {primary_error} | Fallback: {str(e)}"
            return res

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            res = self.primary.generate_text(system_prompt, user_prompt)
            if res and not res.startswith("OpenRouter API key not configured") and not res.startswith("AI text response unavailable"):
                return res
        except Exception as e:
            logger.warning(f"Primary text generation failed: {e}")

        try:
            return self.fallback.generate_text(system_prompt, user_prompt)
        except Exception as e:
            logger.warning(f"Fallback text generation failed: {e}")
            return "Deterministic baseline response."


def get_default_ai_provider() -> AIProvider:
    """Returns the standard production HybridFailoverAIProvider."""
    return HybridFailoverAIProvider()
