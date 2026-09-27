"""
DeadlineOS — Multimodal Vision Provider Abstraction & Failover
=============================================================
Defines the VisionAIProvider interface and concrete implementations:
  1. GeminiVisionProvider (PRIMARY - Google Gemini 2.0 Flash Multimodal)
  2. OpenRouterVisionProvider (FALLBACK - OpenRouter Multimodal Vision)
  3. DeterministicVisionFallbackProvider (SAFE DEGRADATION - Zero-LLM / Offline)
  4. HybridVisionFailoverProvider (Orchestrator with latency & provenance tracking)
"""

import abc
import os
import json
import time
import base64
import logging
import requests
from typing import Dict, Any, Optional, List
from services.ai.safety import AISafety

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_VISION_MODEL = "qwen/qwen-2.5-vl-72b-instruct:free"
DEFAULT_GEMINI_VISION_MODEL = "gemini-2.0-flash"
MAX_INFERENCE_TIMEOUT_SECONDS = 15.0


class VisionAIProvider(abc.ABC):
    """Abstract interface for all multimodal visual inference providers."""

    @abc.abstractmethod
    def extract_visual_data(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        zone_context: Optional[Dict[str, Any]] = None,
        catalog_hints: Optional[List[Dict[str, Any]]] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extracts structured object detections, counts, facings, and OCR snippets from an image.
        Returns standardized dictionary conforming to visual extraction schema.
        """
        pass


class GeminiVisionProvider(VisionAIProvider):
    """
    Primary multimodal vision provider using Google Gemini 2.0 Flash.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_GEMINI_VISION_MODEL,
        timeout: float = MAX_INFERENCE_TIMEOUT_SECONDS
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.timeout = timeout
        self._model = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(model_name=self.model_name)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini Vision model: {e}")

    def extract_visual_data(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        zone_context: Optional[Dict[str, Any]] = None,
        catalog_hints: Optional[List[Dict[str, Any]]] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.api_key or not self._model:
            raise RuntimeError("Gemini Vision API key not configured or model unavailable.")

        system_instruction = (
            "You are a high-precision retail & warehouse shelf monitoring vision assistant. "
            "Analyze the shelf photo. Identify all products, count total units, front facings, "
            "read packaging text/barcodes, and detect empty spots or damaged packaging. "
            "You MUST respond ONLY with valid JSON matching this schema:\n"
            "{\n"
            '  "detected_items": [\n'
            '    {"box_2d": [ymin, xmin, ymax, xmax], "label": "string", "brand": "string", "sku_candidate": "string", "barcode_detected": "string", "confidence": float_0_to_1, "is_front_facing": bool, "condition": "NORMAL"|"DAMAGED"}\n'
            '  ],\n'
            '  "visual_count": float,\n'
            '  "visual_facings": int,\n'
            '  "overall_confidence": float_0_to_1,\n'
            '  "ocr_text_snippets": ["string"],\n'
            '  "observed_shelf_condition": "CLEAN"|"CLUTTERED"|"EMPTY"|"DAMAGED"\n'
            "}"
        )

        user_prompt = "Perform complete shelf zone inventory count and facing analysis."
        if zone_context:
            user_prompt += f"\nShelf Zone Context: Code='{zone_context.get('zone_code')}', Type='{zone_context.get('zone_type')}'."
        if catalog_hints:
            hints_str = ", ".join([f"{h.get('sku')}: {h.get('name')}" for h in catalog_hints[:10]])
            user_prompt += f"\nExpected Catalog SKUs in this section: [{hints_str}]."

        # Validate prompt safety
        AISafety.assert_prompt_safe(f"{system_instruction}\n{user_prompt}")

        full_prompt = f"{system_instruction}\n\n{user_prompt}\n\nCRITICAL: Return ONLY a valid JSON object starting with '{{' and ending with '}}'."
        
        try:
            from PIL import Image as PILImg
            import io
            img_obj = PILImg.open(io.BytesIO(image_bytes))
            response = self._model.generate_content([full_prompt, img_obj])
        except Exception:
            image_part = {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
            response = self._model.generate_content([full_prompt, image_part])

        raw_text = "{}"
        try:
            raw_text = response.text
        except Exception:
            try:
                raw_text = response.candidates[0].content.parts[0].text
            except Exception:
                raw_text = "{}"
        # Robust JSON extraction from text/markdown
        raw_text = raw_text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        parsed["_provider"] = "gemini-2.0-flash"
        parsed["_model"] = self.model_name
        return parsed


class OpenRouterVisionProvider(VisionAIProvider):
    """
    Secondary multimodal vision provider integrating OpenRouter API with vision models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = MAX_INFERENCE_TIMEOUT_SECONDS,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_VISION_MODEL", DEFAULT_OPENROUTER_VISION_MODEL)
        self.timeout = timeout
        self.base_url = base_url

    def extract_visual_data(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        zone_context: Optional[Dict[str, Any]] = None,
        catalog_hints: Optional[List[Dict[str, Any]]] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OpenRouter API key not configured.")

        system_instruction = (
            "You are a warehouse shelf vision assistant. Analyze the shelf image and output ONLY valid JSON "
            "with detected_items (array of objects with label, confidence, is_front_facing, condition), "
            "visual_count (number), visual_facings (int), overall_confidence (float 0 to 1), and ocr_text_snippets (array)."
        )

        user_text = "Extract items, count, facings, and condition."
        if zone_context:
            user_text += f" Zone: {zone_context.get('zone_code')}."

        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_img}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://deadlineos.com",
            "X-Title": "DeadlineOS Vision"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            "response_format": {"type": "json_object"}
        }

        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"OpenRouter Vision HTTP {resp.status_code}: {resp.text[:100]}")

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("OpenRouter Vision returned empty choices.")

        content_text = choices[0].get("message", {}).get("content", "{}")
        parsed = json.loads(content_text)
        parsed["_provider"] = "openrouter"
        parsed["_model"] = self.model
        return parsed


class DeterministicVisionFallbackProvider(VisionAIProvider):
    """
    Deterministic offline fallback provider for zero-LLM safe degradation.
    Returns structured empty observation with confidence=0.00 to prevent system halt.
    """

    def extract_visual_data(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        zone_context: Optional[Dict[str, Any]] = None,
        catalog_hints: Optional[List[Dict[str, Any]]] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "detected_items": [],
            "visual_count": 0.0,
            "visual_facings": 0,
            "overall_confidence": 0.00,
            "ocr_text_snippets": [],
            "observed_shelf_condition": "UNKNOWN",
            "_provider": "deterministic_fallback",
            "_model": "deterministic-heuristic-v1",
            "_fallback_used": True,
            "_fallback_reason": kwargs.get("fallback_reason", "AI vision providers unavailable")
        }


class HybridVisionFailoverProvider(VisionAIProvider):
    """
    Orchestrates the multimodal vision priority hierarchy:
      1. Gemini 2.0 Flash Vision (PRIMARY)
      2. OpenRouter Vision (FALLBACK)
      3. Deterministic Fallback (SAFE DEGRADATION)
    Measures exact inference latency and guarantees provenance tracking.
    """

    def __init__(
        self,
        primary: Optional[VisionAIProvider] = None,
        secondary: Optional[VisionAIProvider] = None,
        fallback: Optional[VisionAIProvider] = None
    ):
        self.primary = primary or GeminiVisionProvider()
        self.secondary = secondary or OpenRouterVisionProvider()
        self.fallback = fallback or DeterministicVisionFallbackProvider()

    def extract_visual_data(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        zone_context: Optional[Dict[str, Any]] = None,
        catalog_hints: Optional[List[Dict[str, Any]]] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        primary_error = None
        secondary_error = None

        # 1. Attempt Primary (Gemini)
        try:
            res = self.primary.extract_visual_data(
                image_bytes=image_bytes,
                mime_type=mime_type,
                zone_context=zone_context,
                catalog_hints=catalog_hints,
                *args,
                **kwargs
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            res["inference_latency_ms"] = elapsed_ms
            res["model_provider"] = res.get("_provider", "gemini-2.0-flash")
            res["model_name"] = res.get("_model", "gemini-2.0-flash")
            return res
        except Exception as e:
            primary_error = str(e)
            logger.warning(f"Primary Gemini Vision provider failed: {primary_error}")

        # 2. Attempt Secondary (OpenRouter)
        try:
            res = self.secondary.extract_visual_data(
                image_bytes=image_bytes,
                mime_type=mime_type,
                zone_context=zone_context,
                catalog_hints=catalog_hints,
                *args,
                **kwargs
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            res["inference_latency_ms"] = elapsed_ms
            res["model_provider"] = res.get("_provider", "openrouter")
            res["model_name"] = res.get("_model", DEFAULT_OPENROUTER_VISION_MODEL)
            res["_fallback_triggered"] = True
            res["_primary_failure_reason"] = primary_error
            return res
        except Exception as e:
            secondary_error = str(e)
            logger.warning(f"Secondary OpenRouter Vision provider failed: {secondary_error}")

        # 3. Deterministic Safe Degradation
        res = self.fallback.extract_visual_data(
            image_bytes=image_bytes,
            mime_type=mime_type,
            zone_context=zone_context,
            catalog_hints=catalog_hints,
            fallback_reason=f"Primary: {primary_error} | Secondary: {secondary_error}",
            *args,
            **kwargs
        )
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        res["inference_latency_ms"] = elapsed_ms
        res["model_provider"] = "deterministic_fallback"
        res["model_name"] = "deterministic-heuristic-v1"
        return res
