#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Qwen LLM adapter

Integrates with Alibaba Cloud Qwen API, provides text generation and vector search capability.
"""

from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.llm.base_llm import BaseLLMCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("atomic.llm.qwen")


class QwenLLMCapability(BaseLLMCapability):
    """Qwen LLM capability adapter"""

    def _build_metadata(self) -> CapabilityMetadata:
        """Build capabilityMetadata"""
        return CapabilityMetadata(
            capability_id="llm.qwen",
            capability_name="Qwen LLM",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="Alibaba Cloud Qwen large language model, supports text generation and vector search",
            tags=["llm", "qwen", "embedding"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        """Validate input parameters"""
        if not request.payload:
            raise InvalidParameterError(message="LLM Request payload cannot be empty")

        action = request.payload.get("action", "chat")

        if action == "chat":
            if "messages" not in request.payload:
                raise InvalidParameterError(message="chat mode must provide messages parameter")
        elif action == "embedding":
            if "text" not in request.payload:
                raise InvalidParameterError(message="embedding mode must provide text parameter")
        elif action == "summarize":
            if "content" not in request.payload:
                raise InvalidParameterError(message="summarize mode must provide content parameter")
        else:
            raise InvalidParameterError(message=f"Unsupported action: {action}")

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """Execute LLM capability invocation"""
        await self.validate_input(request)

        action = request.payload.get("action", "chat")

        try:
            if action == "chat":
                messages = request.payload["messages"]
                temperature = request.payload.get("temperature", 0.7)
                max_tokens = request.payload.get("max_tokens")
                result = await self.chat_completion(messages, temperature, max_tokens)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"result": result},
                    message="LLM chat invocation success",
                )
            elif action == "embedding":
                text = request.payload["text"]
                vector = await self.embedding(text)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"vector": vector},
                    message="Text vectorization success",
                )
            elif action == "summarize":
                content = request.payload["content"]
                summary = await self._summarize(content)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"summary": summary},
                    message="Text summary generation success",
                )
        except Exception as e:
            logger.error(f"Qwen invocation failed: {e}")
            raise CapabilityInvokeError(
                message=f"Qwen invocation failed: {str(e)}",
                details={"action": action},
                cause=e,
            )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Chat completion interface

        Note: Currently a mock implementation. In actual deployment, connect to the real Qwen API.
        """
        config = get_config()

        # Mock implementation: return simulated response
        if config.ENV == "dev":
            logger.warning("Using mock mode to invoke Qwen, please configure real API Key in production environment")
            last_message = messages[-1]["content"] if messages else ""
            return f"[Mock Qwen Response] Received message: {last_message[:50]}... (simulated response)"

        # TODO: Connect to real Qwen API
        # import dashscope
        # response = dashscope.Generation.call(
        #     model=dashscope.Generation.Models.qwen_turbo,
        #     messages=messages,
        #     api_key=config.LLM_API_KEY,
        # )
        # return response["output"]["text"]

        raise CapabilityInvokeError(message="Qwen API not configured")

    async def embedding(self, text: str) -> List[float]:
        """
        Text vectorization interface

        Note: Currently a mock implementation. In actual deployment, connect to the real API.
        """
        config = get_config()

        if config.ENV == "dev":
            # Mock implementation: return random vector
            import random
            return [random.uniform(-1, 1) for _ in range(1536)]

        # TODO: Connect to real Qwen Embedding API
        raise CapabilityInvokeError(message="Qwen Embedding API Not configured")

    async def _summarize(self, content: str) -> str:
        """Text summary generation"""
        messages = [
            {"role": "system", "content": "Please generate a concise summary for the following content, within 200 characters."},
            {"role": "user", "content": content},
        ]
        return await self.chat_completion(messages, temperature=0.3)
