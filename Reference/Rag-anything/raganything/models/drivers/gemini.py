"""GeminiDriver — Google Gemini API protocol adapter.

Gemini API differs from OpenAI in message format, system prompt placement,
and response structure. This driver proves the abstraction boundary
accommodates truly heterogeneous backends.

Gemini API docs: https://ai.google.dev/api/generate-content
"""

from __future__ import annotations

import base64 as b64
import json
import os
from typing import Any

import httpx

from raganything.models.driver import BaseModelDriver
from raganything.models.types import (
    ModelCapability,
    ModelContentFilterError,
    ModelDriverError,
    ModelResponse,
    ModelSpec,
    Usage,
)

# ── Gemini-specific constants ─────────────────────────────────────────


# Map common file extensions to MIME types for inlineData
_EXTENSION_MIME: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
}


def _guess_mime(path_or_url: str) -> str:
    """Guess MIME type from file extension."""
    for ext, mime in _EXTENSION_MIME.items():
        if path_or_url.lower().endswith(ext):
            return mime
    return "image/jpeg"  # safe default


# ── GeminiDriver ─────────────────────────────────────────────────────


class GeminiDriver(BaseModelDriver):
    """Driver for Google Gemini API (generateContent endpoint).

    Handles:
      - OpenAI-format messages → Gemini contents + systemInstruction
      - Image base64 → inlineData parts
      - Gemini response → normalized ModelResponse
      - Vision capability check (Gemini supports base64 + URL)
    """

    bindings = ("gemini",)

    # ── Core interface ──────────────────────────────────────────────

    async def complete(
        self,
        messages: list[dict],
        spec: ModelSpec,
        **kwargs,
    ) -> ModelResponse:
        """Send request to Gemini API → parse response."""
        # 1. Convert OpenAI messages to Gemini format
        body = self._build_request(messages, spec, **kwargs)

        # 2. Build URL (Gemini uses model in path, not as a JSON field)
        url = self._build_url(spec)

        # 3. Send HTTP request
        raw = await self._send_request(url, body, spec)

        # 4. Parse Gemini response → ModelResponse
        return self._parse_response(raw, spec)

    # ── Request building ────────────────────────────────────────────

    def _build_request(
        self, messages: list[dict], spec: ModelSpec, **kwargs
    ) -> dict:
        """Convert OpenAI-format messages to Gemini generateContent request."""
        contents: list[dict] = []
        system_instruction: dict | None = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # Gemini: system prompt goes to top-level systemInstruction
                system_text = content if isinstance(content, str) else ""
                system_instruction = {"parts": [{"text": system_text}]}
                continue

            # Map OpenAI roles to Gemini roles
            gemini_role = "model" if role == "assistant" else "user"

            if isinstance(content, str):
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}],
                })
            elif isinstance(content, list):
                parts = self._convert_parts(content)
                contents.append({"role": gemini_role, "parts": parts})

        request: dict[str, Any] = {"contents": contents}
        if system_instruction:
            request["systemInstruction"] = system_instruction

        # Generation config
        gen_config: dict[str, Any] = {}
        if "max_tokens" in kwargs:
            gen_config["maxOutputTokens"] = kwargs.pop("max_tokens")
        if "temperature" in kwargs:
            gen_config["temperature"] = kwargs.pop("temperature")
        if gen_config:
            request["generationConfig"] = gen_config

        return request

    def _convert_parts(self, content_parts: list[dict]) -> list[dict]:
        """Convert OpenAI content parts to Gemini parts."""
        parts: list[dict] = []
        for part in content_parts:
            if part.get("type") == "text":
                parts.append({"text": part.get("text", "")})
            elif part.get("type") == "image_url":
                url = part.get("image_url", {}).get("url", "")
                if url.startswith("data:"):
                    # data:image/jpeg;base64,ABC123...
                    header, data = url.split(",", 1) if "," in url else ("", url)
                    mime = "image/jpeg"
                    if ":" in header:
                        mime = header.split(":")[1].split(";")[0]
                    parts.append({
                        "inlineData": {"mimeType": mime, "data": data},
                    })
                elif url.startswith("file://"):
                    # Read local file → inlineData
                    path = url[7:]
                    mime = _guess_mime(path)
                    try:
                        with open(path, "rb") as f:
                            img_data = b64.b64encode(f.read()).decode()
                    except FileNotFoundError:
                        raise ModelDriverError(f"Image file not found: {path}")
                    parts.append({
                        "inlineData": {"mimeType": mime, "data": img_data},
                    })
                elif url.startswith("http"):
                    # Gemini also supports fileData with URL
                    mime = _guess_mime(url)
                    parts.append({
                        "fileData": {"mimeType": mime, "fileUri": url},
                    })
                else:
                    parts.append({"text": f"[image: {url}]"})
        return parts

    @staticmethod
    def _build_url(spec: ModelSpec) -> str:
        """Build Gemini API URL.

        Gemini uses the model name in the URL path and api_key as query param.
        """
        base = spec.host.rstrip("/")
        model = spec.model_id
        url = f"{base}/models/{model}:generateContent"
        if spec.api_key and "generativelanguage.googleapis.com" in base:
            # API key auth (simpler for dev)
            url += f"?key={spec.api_key}"
        return url

    async def _send_request(self, url: str, body: dict, spec: ModelSpec) -> dict:
        """Send HTTP request to Gemini API."""
        headers = {"Content-Type": "application/json"}
        # If not using API key auth, use Bearer token
        if "?key=" not in url and spec.api_key:
            headers["Authorization"] = f"Bearer {spec.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 401 or status == 403:
                    from raganything.models.types import ModelAuthError
                    raise ModelAuthError(
                        f"Gemini auth failed: {e.response.text[:200]}"
                    )
                elif status == 429:
                    from raganything.models.types import ModelRateLimitError
                    raise ModelRateLimitError(
                        f"Gemini rate limited: {e.response.text[:200]}"
                    )
                elif status >= 500:
                    from raganything.models.types import ModelServerError
                    raise ModelServerError(
                        f"Gemini server error {status}: {e.response.text[:200]}"
                    )
                raise ModelDriverError(
                    f"Gemini HTTP {status}: {e.response.text[:200]}"
                ) from e
            except httpx.TimeoutException:
                from raganything.models.types import ModelTimeoutError
                raise ModelTimeoutError("Gemini request timed out")

    # ── Response parsing ─────────────────────────────────────────────

    def _parse_response(self, raw: dict, spec: ModelSpec) -> ModelResponse:
        """Parse Gemini generateContent response → ModelResponse."""
        cap = spec.capability
        candidates = raw.get("candidates", [])

        if not candidates:
            # Check for prompt feedback (safety filter)
            feedback = raw.get("promptFeedback", {})
            if feedback.get("blockReason"):
                raise ModelContentFilterError(
                    f"Gemini blocked: {feedback.get('blockReason')}"
                )
            return ModelResponse(text="", metadata={"raw": raw})

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

        finish_reason = candidate.get("finishReason", "")
        if not text and finish_reason == "SAFETY":
            raise ModelContentFilterError(
                f"Gemini safety filter: {finish_reason}"
            )

        # Reasoning (if thinking model)
        reasoning = None
        if cap.supports_thinking:
            # Gemini thinking models may put thoughts in a separate part
            thoughts = [
                p.get("thought", "")
                for p in parts
                if "thought" in p
            ]
            if thoughts:
                reasoning = "\n".join(thoughts)

        # Usage
        usage_raw = raw.get("usageMetadata", {})
        usage = Usage(
            prompt_tokens=usage_raw.get("promptTokenCount", 0),
            completion_tokens=usage_raw.get("candidatesTokenCount", 0),
        ) if usage_raw else None

        # Metadata
        metadata: dict[str, Any] = {
            "model": raw.get("modelVersion", spec.model_id),
        }
        if finish_reason:
            metadata["finish_reason"] = finish_reason
        if os.getenv("MODEL_DEBUG_RAW", "").lower() in ("1", "true"):
            metadata["raw"] = raw

        return ModelResponse(
            text=text,
            reasoning=reasoning,
            usage=usage,
            metadata=metadata,
        )
