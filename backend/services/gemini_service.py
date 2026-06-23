"""
DeadlineOS — Gemini AI Service
================================
Central wrapper around the Google Generative AI SDK.

Responsibilities:
  • Provide a clean interface for all Gemini text and vision calls.
  • Enforce structured (JSON) output when a schema is supplied.
  • Implement retry logic with exponential back-off.
  • Cache identical prompts to reduce API cost and latency.
  • Stream responses for real-time UI feedback.

Usage (inside a Flask app context):
    from services.gemini_service import GeminiService
    gemini = GeminiService()
    result = gemini.generate_text("Summarise this task: ...")
    structured = gemini.generate_structured(system_prompt, user_prompt, schema)
"""

import base64
import hashlib
import json
import logging
import time
from typing import Any, Generator

import google.generativeai as genai
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Raised when the Gemini API returns an unrecoverable error."""


class GeminiService:
    """
    Singleton-style service for all Gemini API interactions.

    Instantiate once in app.py and share via Flask's `g` object or
    a module-level singleton pattern.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        vision_model: str = "gemini-2.0-flash",
        max_retries: int = 3,
        retry_delay: float = 1.5,
        cache_ttl: int = 300,
        cache_maxsize: int = 100,
        timeout: float = 15.0,
    ) -> None:
        """
        Parameters
        ----------
        api_key       : Google AI Studio / Gemini API key.
        model         : Default text model identifier.
        vision_model  : Model used for vision (image) requests.
        max_retries   : Number of retry attempts on transient errors.
        retry_delay   : Initial delay (seconds) between retries; doubles each attempt.
        cache_ttl     : Seconds before cached responses expire.
        cache_maxsize : Maximum number of cached responses to keep in memory.
        timeout       : Hard timeout in seconds for API calls to prevent hanging Gunicorn workers.
        """
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file: GEMINI_API_KEY=your_key_here"
            )

        # Configure the SDK once
        genai.configure(api_key=api_key)

        self._model_name = model
        self._vision_model_name = vision_model
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._timeout = timeout

        # In-memory TTL cache keyed by SHA-256 of the full prompt
        self._cache: TTLCache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)

        # Instantiate model objects
        self._text_model = genai.GenerativeModel(model_name=model)
        self._vision_model = genai.GenerativeModel(model_name=vision_model)

        logger.info(
            "GeminiService initialised | model=%s | vision_model=%s | timeout=%ss",
            model,
            vision_model,
            timeout,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(*parts: str) -> str:
        """Create a deterministic cache key from one or more strings."""
        combined = "|".join(parts)
        return hashlib.sha256(combined.encode()).hexdigest()

    def _call_with_retry(self, callable_fn, *args, **kwargs) -> Any:
        """
        Execute `callable_fn` with exponential back-off retry and strict timeout guard.

        Retries on:  any exception from the Gemini SDK or TimeoutError.
        Raises:      GeminiServiceError after all retries are exhausted.
        """
        import concurrent.futures
        
        delay = self._retry_delay
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(callable_fn, *args, **kwargs)
                    return future.result(timeout=self._timeout)
            except concurrent.futures.TimeoutError as exc:
                last_error = exc
                logger.warning(
                    "Gemini call timed out after %ss (attempt %d/%d)",
                    self._timeout,
                    attempt,
                    self._max_retries,
                )
                if attempt < self._max_retries:
                    time.sleep(delay)
                    delay *= 2  # exponential back-off
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini call failed (attempt %d/%d): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                if attempt < self._max_retries:
                    time.sleep(delay)
                    delay *= 2  # exponential back-off

        raise GeminiServiceError(
            f"Gemini API failed after {self._max_retries} attempts. Last Error: {last_error}"
        ) from last_error

    @staticmethod
    def _extract_json(text: str) -> dict:
        """
        Extract and parse JSON from a Gemini response.

        Handles the common case where the model wraps the JSON in a
        markdown code-fence:  ```json\n{...}\n```
        """
        # Strip markdown code fences if present
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.split("\n")
            # Remove first line (```json or ```) and last line (```)
            inner_lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            stripped = "\n".join(inner_lines)

        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini JSON response: %s\nRaw: %s", exc, text)
            raise GeminiServiceError(
                f"Gemini returned invalid JSON: {exc}\nRaw response: {text[:500]}"
            ) from exc

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> str:
        """
        Generate a plain-text response from Gemini.

        Parameters
        ----------
        prompt             : The user-facing prompt text.
        system_instruction : Optional system-level instruction (sets model persona).
        temperature        : Sampling temperature (0 = deterministic, 1 = creative).
        use_cache          : Whether to return a cached result if available.

        Returns
        -------
        str : The model's text response.
        """
        cache_key = self._cache_key("text", prompt, system_instruction or "", str(temperature))

        if use_cache and cache_key in self._cache:
            logger.debug("Cache HIT for generate_text (key=%s…)", cache_key[:12])
            return self._cache[cache_key]

        # Build generation config
        generation_config = genai.types.GenerationConfig(temperature=temperature)

        # Apply system instruction if provided
        model = (
            genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=system_instruction,
            )
            if system_instruction
            else self._text_model
        )

        def _call():
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
            )
            return response.text

        result: str = self._call_with_retry(_call)

        if use_cache:
            self._cache[cache_key] = result

        logger.debug("generate_text completed | chars=%d", len(result))
        return result

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
        use_cache: bool = True,
    ) -> dict:
        """
        Generate a structured JSON response from Gemini.

        All DeadlineOS agents call this method to get predictable,
        parseable outputs that can be stored in the database.

        Parameters
        ----------
        system_prompt : Agent persona and output format instructions.
        user_prompt   : Task-specific input data.
        schema        : Optional JSON Schema for response validation hint.
                        (Currently used as documentation; enforcement via prompt.)
        temperature   : Low temperature (0.2) for consistent structured outputs.
        use_cache     : Whether to return a cached result if available.

        Returns
        -------
        dict : Parsed JSON response from Gemini.
        """
        cache_key = self._cache_key("structured", system_prompt, user_prompt)

        if use_cache and cache_key in self._cache:
            logger.debug("Cache HIT for generate_structured (key=%s…)", cache_key[:12])
            return self._cache[cache_key]

        # Append strict JSON instruction to system prompt
        enhanced_system = (
            system_prompt.strip()
            + "\n\nCRITICAL: Your response MUST be valid JSON only. "
            "No markdown, no explanation outside the JSON object. "
            "Start your response with '{' and end with '}'."
        )

        # Append schema hint to user prompt if provided
        full_user_prompt = user_prompt
        if schema:
            schema_hint = json.dumps(schema, indent=2)
            full_user_prompt = (
                f"{user_prompt}\n\n"
                f"Adhere strictly to this JSON schema:\n{schema_hint}"
            )

        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=enhanced_system,
        )

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",  # Gemini structured output mode
        )

        def _call():
            response = model.generate_content(
                full_user_prompt,
                generation_config=generation_config,
            )
            return response.text

        raw_text: str = self._call_with_retry(_call)
        result: dict = self._extract_json(raw_text)

        if use_cache:
            self._cache[cache_key] = result

        logger.debug(
            "generate_structured completed | keys=%s",
            list(result.keys()),
        )
        return result

    def generate_vision(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/png",
        structured: bool = True,
        temperature: float = 0.2,
    ) -> dict | str:
        """
        Analyse an image using Gemini Vision and extract structured data.

        Parameters
        ----------
        image_bytes : Raw bytes of the image (PNG, JPEG, WEBP, etc.).
        prompt      : Instruction for what to extract from the image.
        mime_type   : MIME type of the image bytes.
        structured  : If True, attempt JSON parsing of the response.
        temperature : Sampling temperature.

        Returns
        -------
        dict if structured=True, str otherwise.
        """
        # Encode image to base64 for the Gemini multimodal API
        image_data = {
            "mime_type": mime_type,
            "data": base64.b64encode(image_bytes).decode("utf-8"),
        }

        if structured:
            enhanced_prompt = (
                prompt
                + "\n\nReturn ONLY valid JSON. No markdown fences. "
                "Start with '{' and end with '}'."
            )
        else:
            enhanced_prompt = prompt

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json" if structured else "text/plain",
        )

        def _call():
            response = self._vision_model.generate_content(
                [enhanced_prompt, image_data],
                generation_config=generation_config,
            )
            return response.text

        raw_text: str = self._call_with_retry(_call)

        if structured:
            return self._extract_json(raw_text)
        return raw_text

    def stream_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream a Gemini response token-by-token.

        Yields
        ------
        str : Each text chunk as it arrives from the API.

        Typical usage:
            for chunk in gemini.stream_response(prompt):
                socketio.emit("agent:chunk", {"text": chunk})
        """
        model = (
            genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=system_instruction,
            )
            if system_instruction
            else self._text_model
        )

        generation_config = genai.types.GenerationConfig(temperature=temperature)

        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            logger.error("Streaming error: %s", exc)
            raise GeminiServiceError(f"Streaming failed: {exc}") from exc

    # ── Utility ───────────────────────────────────────────────────────────────

    def health_check(self) -> dict:
        """
        Send a minimal prompt to verify the API key and connectivity.

        Returns
        -------
        dict with keys: status ("ok" | "error"), model, message
        """
        try:
            response = self._text_model.generate_content(
                'Reply with exactly: {"status": "ok"}',
                generation_config=genai.types.GenerationConfig(
                    temperature=0, max_output_tokens=20
                ),
            )
            return {
                "status": "ok",
                "model": self._model_name,
                "message": "Gemini API reachable",
                "raw": response.text.strip(),
            }
        except Exception as exc:
            logger.error("Gemini health check failed: %s", exc)
            return {
                "status": "error",
                "model": self._model_name,
                "message": str(exc),
            }

    def clear_cache(self) -> int:
        """Clear all cached responses. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        logger.info("GeminiService cache cleared (%d entries removed)", count)
        return count
