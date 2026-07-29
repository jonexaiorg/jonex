"""BaseModelDriver — abstract API protocol adapter with image normalization."""

from __future__ import annotations

import base64 as b64
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from raganything.models.types import ModelCapability, ModelResponse, ModelSpec


class BaseModelDriver(ABC):
    """Abstract driver for a model API protocol.

    Each subclass encapsulates one API protocol (OpenAI, Gemini, etc.).
    ``bindings`` declares which protocol aliases this driver handles.
    ``ModelRegistry`` uses ``BINDING_ALIASES`` to route ``models.env``
    bindings to the correct driver.

    Parsing responsibility lives entirely in each driver (no global parser).
    """

    bindings: tuple[str, ...] = ()  # subclass MUST override
    # Example: ("openai", "vllm", "ollama", "lmstudio")

    # ── Core interface ─────────────────────────────────────────────────

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        spec: "ModelSpec",
        **kwargs,
    ) -> "ModelResponse":
        """Send request → parse raw response → normalized ModelResponse.

        Args:
            messages: OpenAI-format message list with images already normalized.
            spec: Model deployment info (host, api_key, capability).
            **kwargs: Passthrough (max_tokens, temperature, ...).

        Returns:
            Normalized ModelResponse.

        Raises:
            ModelAuthError, ModelRateLimitError, ModelTimeoutError,
            ModelServerError, ModelContentFilterError
        """

    # ── Image normalization ────────────────────────────────────────────

    def normalize_images(
        self,
        messages: list[dict],
        cap: "ModelCapability",
    ) -> list[dict]:
        """Convert image references in messages based on model capability.

        Conventions:
          - ``file:///absolute/path`` → read file → base64 data URI (if model needs base64)
          - ``data:image/...;base64,...`` → passthrough (if model supports base64)
          - ``https://...`` → passthrough (if model supports url)

        Default implementation handles the common cases.
        Subclasses can override for provider-specific behavior.
        """
        from raganything.models.types import ModelDriverError

        result: list[dict] = []
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                result.append(msg)
                continue

            new_parts: list[dict] = []
            for part in content:
                if part.get("type") != "image_url":
                    new_parts.append(part)
                    continue

                url = part["image_url"].get("url", "")

                if url.startswith("file://"):
                    if not cap.supports_vision:
                        raise ModelDriverError(
                            "Model does not support vision — cannot process images"
                        )
                    # Check capability FIRST, then access the file
                    if cap.supports_vision_path:
                        new_parts.append(part)
                    elif cap.supports_vision_base64:
                        path = url[7:]  # strip "file://"
                        try:
                            with open(path, "rb") as f:
                                img_b64 = b64.b64encode(f.read()).decode()
                        except FileNotFoundError:
                            raise ModelDriverError(
                                f"Image file not found: {path}"
                            )
                        new_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}",
                            },
                        })
                    else:
                        raise ModelDriverError(
                            "Model does not support image input from file path"
                        )

                elif url.startswith("data:"):
                    if cap.supports_vision_base64:
                        new_parts.append(part)
                    else:
                        raise ModelDriverError(
                            "Model does not support base64 images. Upload to URL first."
                        )

                elif url.startswith("http"):
                    if cap.supports_vision_url:
                        new_parts.append(part)
                    else:
                        raise ModelDriverError(
                            "Model does not support URL images."
                        )

                else:
                    # Unknown scheme — pass through and let the API decide
                    new_parts.append(part)

            result.append({**msg, "content": new_parts})

        return result
