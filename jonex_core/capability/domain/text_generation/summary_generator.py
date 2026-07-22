#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Text summary generation domain capability

Orchestrates atomic capabilities via LLMClient.
"""

from typing import Optional

from jonex_core.capability.atomic.llm.client import LLMClient, get_llm_client
from jonex_core.capability.domain.base import DomainCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)
from jonex_core.common import get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("domain.text.summary")

_PROMPTS = {
    "short":
        "Please generate a very brief summary for the following content, within 50 characters:\n\n{content}\n\nSummary: ",
    "medium":
        "Please generate a concise summary for the following content, within 200 characters, retaining key information:\n\n{content}\n\nSummary: ",
    "detailed":
        "Please generate a detailed summary for the following content, within 500 characters, retaining all important information:\n\n{content}\n\nDetailed summary: ",
    "bullet_points":
        "Please extract key points from the following content as a bulleted list, retaining all key information:\n\n{content}\n\nKey points: ",
}


class SummaryGeneratorCapability(DomainCapability):
    """Text summary generation domain capability"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__()
        self.llm_client: LLMClient = llm_client or get_llm_client()

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="text.summary_generator",
            capability_name="Text summary generation",
            capability_type=CapabilityType.DOMAIN,
            version="v1",
            description="Specialized text summary generation capability, supports summaries of different lengths and styles",
            tags=["text", "summary"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        if not request.payload:
            raise InvalidParameterError(message="Summary generation request payload cannot be empty")
        action = request.payload.get("action", "medium")
        if action not in _PROMPTS:
            raise InvalidParameterError(message=f"Unsupported action: {action}")
        if "content" not in request.payload:
            raise InvalidParameterError(message="content parameter must be provided")
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        await self.validate_input(request)

        action = request.payload.get("action", "medium")
        content = request.payload["content"]

        try:
            logger.info(
                f"Generate summary: action={action}, content_length={len(content)}"
            )
            prompt = _PROMPTS[action].format(content=content)
            summary = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            return CapabilityResponse.ok(
                request_id=request.request_id,
                data={
                    "summary": summary,
                    "summary_type": action,
                    "original_length": len(content),
                    "summary_length": len(summary),
                },
                message="Text summary generation succeeded",
            )
        except CapabilityInvokeError:
            raise
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise CapabilityInvokeError(
                message=f"Summary generation failed: {e}",
                details={"action": action, "content_length": len(content)},
                cause=e,
            )
