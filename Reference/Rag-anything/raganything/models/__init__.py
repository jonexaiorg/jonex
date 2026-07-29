"""RAGAnything Model Adapter Layer.

Provides:
  - ModelCapability / ModelSpec / ModelResponse: core data types
  - BoundModel: structured model instance (replaces callable + attributes anti-pattern)
  - BaseModelDriver + drivers: API protocol abstraction
  - ModelRegistry: model_id → BoundModel resolution
"""

from raganything.models.adapters import base64_caption_adapter, legacy_llm_adapter, legacy_vlm_adapter
from raganything.models.driver import BaseModelDriver
from raganything.models.transformers import (
    LLMResponseTransformer,
    NoOpTransformer,
    TokenHubTransformer,
    get_transformer,
)
from raganything.models.parser import extract_openai_usage
from raganything.models.registry import BINDING_ALIASES, ModelRegistry
from raganything.models.types import (
    BoundModel,
    ModelAuthError,
    ModelCapability,
    ModelContentFilterError,
    ModelDriverError,
    ModelRateLimitError,
    ModelResponse,
    ModelServerError,
    ModelSpec,
    ModelTimeoutError,
    RetryPolicy,
    ToolCall,
    Usage,
)

__all__ = [
    # Types
    "BoundModel",
    "ModelCapability",
    "ModelResponse",
    "ModelSpec",
    "RetryPolicy",
    "ToolCall",
    "Usage",
    # Adapters
    "base64_caption_adapter",
    "legacy_llm_adapter",
    "legacy_vlm_adapter",
    # Driver
    "BaseModelDriver",
    # Registry
    "BINDING_ALIASES",
    "ModelRegistry",
    # Errors
    "ModelAuthError",
    "ModelContentFilterError",
    "ModelDriverError",
    "ModelRateLimitError",
    "ModelServerError",
    "ModelTimeoutError",
    # Transformers
    "LLMResponseTransformer",
    "NoOpTransformer",
    "TokenHubTransformer",
    "get_transformer",
    # Utils
    "extract_openai_usage",
]
