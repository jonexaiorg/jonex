"""Response parsing utilities — tools, NOT a global parser.

Each Driver owns its own response parsing. This module provides
shared utility functions that Drivers can optionally use.
"""

from __future__ import annotations

from typing import Any

from raganything.models.types import Usage


def extract_openai_usage(raw: dict) -> Usage | None:
    """Extract Usage from an OpenAI-format response dict.

    Drivers that return OpenAI-compatible JSON can use this
    instead of reimplementing the extraction logic.

    Returns None when the usage field is absent.
    """
    usage_raw = raw.get("usage")
    if not usage_raw:
        return None

    reasoning_tokens = (
        usage_raw.get("completion_tokens_details", {})
        .get("reasoning_tokens", 0)
    )
    return Usage(
        prompt_tokens=usage_raw.get("prompt_tokens", 0),
        completion_tokens=usage_raw.get("completion_tokens", 0),
        reasoning_tokens=reasoning_tokens,
    )
