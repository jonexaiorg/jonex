"""Core data types for the model adapter layer.

SSOT principle:
  - ModelCapability describes inherent model capabilities (immutable per model)
  - ModelSpec describes a deployed instance (host, api_key, retry policy)
  - ModelResponse is the normalized return value
  - response parser is NOT independently configured — derived from capability.supports_thinking
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from raganything.models.driver import BaseModelDriver


# ── Usage (first-class, not buried in metadata) ─────────────────────────


@dataclass
class Usage:
    """Token usage — first-class citizen for billing, rate-limiting, monitoring."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0  # thinking models only


# ── ToolCall (reserved for future function-calling) ─────────────────────


@dataclass
class ToolCall:
    """Reserved: structured tool/function call output."""

    id: str = ""
    name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)


# ── ModelResponse (normalized return) ────────────────────────────────────


@dataclass
class ModelResponse:
    """Normalized model response.

    Attributes:
        text: Primary text content.
        reasoning: Thinking/reasoning chain (None for non-thinking models).
        usage: Token usage (None when unavailable).
        tool_calls: Reserved for function calling.
        metadata: Model name, finish_reason, elapsed time, etc.
            ``raw`` field only populated when ``MODEL_DEBUG_RAW=true``.
    """

    text: str
    reasoning: Optional[str] = None
    usage: Optional[Usage] = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# ── ModelCapability (inherent model properties — single source of truth) ──


@dataclass
class ModelCapability:
    """Immutable model capabilities — SSOT for what a model supports.

    All boolean fields default to the most conservative value.
    A missing models.yaml entry produces this exact object (safe default).
    """

    # ── Modality support ─────────────────────────────────────────────
    supports_vision: bool = False
    supports_audio: bool = False
    supports_text: bool = True  # always True

    # ── Vision input methods (when supports_vision=True) ─────────────
    supports_vision_base64: bool = True  # data:image/jpeg;base64,...
    supports_vision_url: bool = True  # https://... (COS pre-signed etc.)
    supports_vision_path: bool = False  # file:///... (local models only)

    # ── Protocol capabilities ────────────────────────────────────────
    supports_system_prompt: bool = True
    supports_thinking: bool = False  # drives parser: False→standard, True→thinking

    # ── Capacity constraints ─────────────────────────────────────────
    max_context_tokens: int = 32768
    max_output_tokens: int = 4096

    # NOTE: supports_streaming removed (YAGNI — no streaming demand yet).
    #       recommended_temperature removed (task-level hyperparameter, not capability).
    #       model_family/version removed (display metadata, belongs in ModelSpec.metadata).


# ── ModelSpec (deployed instance) ────────────────────────────────────────


@dataclass
class RetryPolicy:
    """Per-model retry configuration."""

    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    retryable_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)


@dataclass
class ModelSpec:
    """Deployed model instance — connection info + inherent capability.

    Attributes:
        model_id: User-facing identifier (e.g. "qwen3-72b").
        binding: Protocol binding (e.g. "vllm") — resolves to driver via BINDING_ALIASES.
        host: API base URL.
        api_key: Authentication key (from env var, not hardcoded).
        capability: Immutable model capabilities (SSOT).
        retry: Retry policy for transient failures.
        metadata: Display metadata (family, version, description) — not used for routing.
    """

    model_id: str
    binding: str  # "vllm", "ollama", "openai", "gemini", ...
    host: str
    api_key: str = ""
    capability: ModelCapability = field(default_factory=ModelCapability)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    metadata: dict[str, Any] = field(default_factory=dict)
    extra_headers: dict[str, str] = field(default_factory=dict)  # [jonex] metering headers (X-Jonex-*)

    # NOTE: response_parser removed (derived from supports_thinking).
    #       driver removed (resolved from binding via registry).


# ── BoundModel (structured object — replaces callable + attribute anti-pattern) ─


@dataclass
class BoundModel:
    """A model instance bound to a specific endpoint.

    Callers receive a structured object — capability queries and invocation
    are cleanly separated.  The ``__call__`` interface provides backward
    compatibility with the existing callable convention.

    Usage::

        llm = registry.bind("qwen3-72b")
        print(llm.capability.max_context_tokens)  # 32768
        resp = await llm.complete([{"role": "user", "content": "Hello"}])
        print(resp.text)
    """

    spec: ModelSpec
    driver: "BaseModelDriver"

    @property
    def capability(self) -> ModelCapability:
        """The model's inherent capabilities."""
        return self.spec.capability

    async def complete(self, messages: list[dict], **kw: Any) -> ModelResponse:
        """Send messages and return a normalized response.

        Args:
            messages: OpenAI-format message list.
                ``[{"role":"user","content":[{"type":"text","text":"..."},
                 {"type":"image_url","image_url":{"url":"file:///path"}}]}]``
            **kw: Passthrough kwargs (max_tokens, temperature, ...).

        Returns:
            Normalized ModelResponse with text, reasoning, usage.

        Raises:
            ModelAuthError, ModelRateLimitError, ModelTimeoutError,
            ModelServerError, ModelContentFilterError
        """
        # 1. Image normalization (driver handles file:// → base64 conversion)
        normalized = self.driver.normalize_images(messages, self.capability)

        # 2. Dispatch to driver
        return await self.driver.complete(normalized, self.spec, **kw)

    async def __call__(self, messages: list[dict], **kw: Any) -> ModelResponse:
        """Backward-compatible callable interface."""
        return await self.complete(messages, **kw)


# ── Error hierarchy ─────────────────────────────────────────────────────


class ModelDriverError(Exception):
    """Base exception for model driver layer."""


class ModelAuthError(ModelDriverError):
    """Authentication/authorization failure (401, 403)."""


class ModelRateLimitError(ModelDriverError):
    """Rate limit exceeded (429)."""


class ModelTimeoutError(ModelDriverError, TimeoutError):
    """Request timeout."""


class ModelServerError(ModelDriverError):
    """Server-side error (5xx)."""


class ModelContentFilterError(ModelDriverError):
    """Content safety filter triggered — finish_reason=content_filter, text empty."""
