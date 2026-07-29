"""LLM response transformers — post-process LLM output for LightRAG compatibility.

**When transformers fire:**

  Every LLM call through ``legacy_llm_adapter`` passes through the transformer::

      LightRAG extract_entities / aquery / ...
        → use_llm_func_with_cache(prompt, use_llm_func)
          → use_llm_func(prompt, system_prompt)       # legacy_llm_adapter wrapper
            → bound.complete(messages)                 # driver HTTP call
            → transformer.transform(response.text)     # ← HERE, every LLM call
            → return cleaned text

  The transformer is set once during ``ModelFactory.build()`` and tied to the
  adapter for the lifetime of the RAGAnything instance.  LightRAG and all
  downstream consumers are unaware of its existence.

**How transformers are selected:**

  ``get_transformer(binding, model_id=None)`` uses a two-level lookup::

    1. ``(binding, model_id)`` —  model-specific (most precise)
    2. ``binding``             —  protocol-level (driver binding string)
    3. ``NoOpTransformer``     —  fallback (passthrough)

  Example:
    - ``binding="tokenhub", model="deepseek-v4-flash-202605"``
      → ``TokenHubTransformer``  (matched by binding="tokenhub")

  To add a new transformer::

      from raganything.models.transformers import BINDING_TRANSFORMERS

      # Protocol-level (all models on this binding)
      BINDING_TRANSFORMERS["milvus_proxy"] = MilvusTransformer()

      # Model-specific (only for a particular model_id)
      BINDING_TRANSFORMERS[("openai", "gpt-4o-mini")] = Gpt4oTransformer()
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any


class LLMResponseTransformer(ABC):
    """Base class for post-processing LLM responses.

    Subclasses implement provider-specific formatting fixes to ensure
    LightRAG can parse entity/relation extraction output.

    Lifecycle:
      1. Created during ``ModelFactory.build()``.
      2. Passed to ``legacy_llm_adapter(bound, transformer=...)``.
      3. ``transform()`` is called on EVERY LLM response before returning
         to LightRAG.
    """

    @abstractmethod
    def transform(self, text: str, context: dict[str, Any] | None = None) -> str:
        """Transform raw LLM response text.

        Args:
            text: Raw response text from the LLM.
            context: Optional metadata dict with keys:
                - model_id: str
                - binding: str
                - prompt: str (the user prompt sent to LLM)

        Returns:
            Cleaned text ready for LightRAG parsing.
        """
        ...


class NoOpTransformer(LLMResponseTransformer):
    """Pass-through transformer — no modification.  Default for most drivers."""

    def transform(self, text: str, context: dict[str, Any] | None = None) -> str:
        return text


class TokenHubTransformer(LLMResponseTransformer):
    """Fixes deepseek-v4 responses for LightRAG compatibility.

    Known issues with deepseek-v4-flash-202605 via TokenHub:
      1. Completion delimiter ``<|COMPLETE|>`` may be missing.
      2. Truncated last line when ``max_tokens`` is too low.
      3. Thinking/reasoning blocks (``<thinking>...</thinking>``) leak into
         the response text.
      4. Whitespace around ``<|#|>`` tuple delimiters.

    All fixes are non-destructive — they only add missing markers or
    remove noise that LightRAG cannot parse.
    """

    COMPLETION_DELIMITER = "<|COMPLETE|>"
    TUPLE_DELIMITER = "<|#|>"

    def transform(self, text: str, context: dict[str, Any] | None = None) -> str:
        if not text:
            return text

        # 1. Strip leading/trailing whitespace
        text = text.strip()
        if not text:
            return text

        # 2. Remove <thinking> blocks (deepseek may emit reasoning as XML)
        text = self._remove_thinking_blocks(text)

        # 3. Remove truncated trailing line (incomplete entity/relation)
        #    Deepseek sometimes cuts off mid-line when max_tokens is exhausted.
        text = self._remove_truncated_trailing_line(text)

        # 4. Ensure completion delimiter is present
        if self.COMPLETION_DELIMITER not in text:
            text = text.rstrip() + "\n" + self.COMPLETION_DELIMITER

        # 5. Normalize whitespace around tuple delimiters in entity/relation lines
        text = self._normalize_delimiters(text)

        return text

    # ── Internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _remove_thinking_blocks(text: str) -> str:
        """Remove <thinking>...</thinking> blocks from deepseek output."""
        return re.sub(
            r"<thinking[^>]*>.*?</thinking>",
            "",
            text,
            flags=re.DOTALL,
        ).strip()

    def _remove_truncated_trailing_line(self, text: str) -> str:
        """Drop the last line if it looks like a truncated entity/relation.

        A truncated line is one that starts with 'entity' or 'relation'
        but contains fewer than the expected number of ``<|#|>`` delimiters
        (3 for entity, 4 for relation).
        """
        lines = text.split("\n")
        if not lines:
            return text

        last = lines[-1].strip()
        if not last:
            return text

        # Only inspect entity/relation lines
        if last.startswith("entity"):
            expected_delimiters = 3  # entity<|#|>name<|#|>type<|#|>desc
        elif last.startswith("relation"):
            expected_delimiters = 4  # relation<|#|>src<|#|>tgt<|#|>kw<|#|>desc
        else:
            return text  # Not an entity/relation line — keep it

        # Count complete delimiters
        if last.count(self.TUPLE_DELIMITER) < expected_delimiters:
            # Truncated — remove this line
            return "\n".join(lines[:-1]).rstrip()

        return text

    @staticmethod
    def _normalize_delimiters(text: str) -> str:
        """Collapse whitespace around tuple delimiters."""
        lines = text.split("\n")
        normalized: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("entity") or stripped.startswith("relation"):
                stripped = re.sub(
                    r"\s*" + re.escape(TokenHubTransformer.TUPLE_DELIMITER) + r"\s*",
                    TokenHubTransformer.TUPLE_DELIMITER,
                    stripped,
                )
            normalized.append(stripped if stripped else line)
        return "\n".join(normalized)


# ── Transformer registry ──────────────────────────────────────────────────

# Two-level lookup: (binding, model_id) → transformer (model-specific),
# or binding → transformer (protocol-level).
# Keys can be str (binding) or tuple[str, str] (binding, model_id).
BINDING_TRANSFORMERS: dict[str | tuple[str, str], LLMResponseTransformer] = {
    "tokenhub": TokenHubTransformer(),
    # Examples for future additions:
    # "openai": NoOpTransformer(),                         # protocol-level
    # ("openai", "gpt-4o-mini"): SomeFixingTransformer(),  # model-specific
}

_noop = NoOpTransformer()


def get_transformer(
    binding: str,
    model_id: str | None = None,
) -> LLMResponseTransformer:
    """Return the transformer for a given binding and optional model_id.

    Lookup order:
      1. ``(binding, model_id)`` — model-specific (most precise)
      2. ``binding``              — protocol-level
      3. ``NoOpTransformer``     — fallback

    Args:
        binding: Driver binding string (e.g. "tokenhub", "openai").
        model_id: Optional model identifier for finer-grained selection.

    Returns:
        Transformer instance (never None).
    """
    if model_id:
        key: tuple[str, str] = (binding, model_id)
        if key in BINDING_TRANSFORMERS:
            return BINDING_TRANSFORMERS[key]
    return BINDING_TRANSFORMERS.get(binding, _noop)


def register_transformer(
    binding: str,
    transformer: LLMResponseTransformer,
    model_id: str | None = None,
) -> None:
    """Register a transformer for a binding (and optionally a specific model).

    Args:
        binding: Driver binding string.
        transformer: Transformer instance.
        model_id: If provided, register for this specific model only.
    """
    if model_id:
        BINDING_TRANSFORMERS[(binding, model_id)] = transformer
    else:
        BINDING_TRANSFORMERS[binding] = transformer
