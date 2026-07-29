"""EchoDriver — non-OpenAI mock driver for validating abstraction boundaries.

Returns a synthetic response from a fictional "Echo" API format:
  {"echo": {"response": "...", "tokens_used": N}}

Purpose: prove that the ``complete(messages, spec, **kw) -> ModelResponse``
signature can accommodate non-OpenAI APIs BEFORE implementing a real one.
"""

from __future__ import annotations

from raganything.models.driver import BaseModelDriver
from raganything.models.types import ModelResponse, ModelSpec, Usage


class EchoDriver(BaseModelDriver):
    """Mock driver simulating a non-OpenAI API protocol.

    Used in Phase 2b to validate that the abstract driver boundary
    is correctly shaped for heterogeneous backends.
    """

    bindings = ("echo",)

    async def complete(
        self,
        messages: list[dict],
        spec: ModelSpec,
        **kwargs,
    ) -> ModelResponse:
        """Echo the last user message with model prefix."""
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    user_content = content
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            user_content = part.get("text", "")
                        elif isinstance(part, dict) and part.get("type") == "image_url":
                            url = part.get("image_url", {}).get("url", "")[:50]
                            user_content += f"[image: {url}] "

        # Simulate non-OpenAI response format
        response_text = user_content if user_content else "(empty)"
        word_count = len(user_content.split()) if user_content else 0

        return ModelResponse(
            text=response_text,
            usage=Usage(
                prompt_tokens=word_count,
                completion_tokens=len(response_text.split()),
            ),
            metadata={
                "model": spec.model_id,
                "driver": "EchoDriver",
                "simulated": True,
            },
        )
