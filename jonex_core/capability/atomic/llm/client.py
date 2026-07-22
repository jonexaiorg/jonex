#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
LLM Client Abstract + Factory

Business/domain code unified through `get_llm_client()` to get LLMClient, no longer new specific adapter.
- LOCAL: Directly invoke local adapter in-process (Default uses QwenLLMCapability)
- REMOTE: Invoke independent LLM capability service via Sidecar reverse proxy
- MOCK: Offline/test stub, no external dependencies

Replace provider (Qwen -> DeepSeek, etc.) only need to extend LocalLLMClient.factory or modify manifest endpoint.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.locator import CapabilityMode, get_locator
from jonex_core.common import get_config, get_logger

logger = get_logger("capability.client.llm")

# Currently used capability_id (can be overridden in manifest)
LLM_CAPABILITY_ID = "atomic.llm.qwen.v1"


class LLMClient(ABC):
    """LLM Client contract: domain/business code only depends on this interface"""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Chat completion"""

    @abstractmethod
    async def embedding(self, text: str) -> List[float]:
        """Text vectorization"""


# ============================================================
# Local: Direct in-process adapter
# ============================================================
class LocalLLMClient(LLMClient):
    """Direct connection to local adapter"""

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        # Lazy import to avoid loading heavy dependencies in REMOTE/MOCK mode
        from jonex_core.capability.atomic.llm.qwen_adapter import QwenLLMCapability

        self._adapter = QwenLLMCapability()
        self._options = options or {}

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        return await self._adapter.chat_completion(messages, temperature, max_tokens)

    async def embedding(self, text: str) -> List[float]:
        return await self._adapter.embedding(text)


# ============================================================
# Remote: Via Sidecar reverse proxy
# ============================================================
class RemoteLLMClient(LLMClient):
    """Invoke remote LLM service via Sidecar reverse proxy"""

    def __init__(
        self,
        endpoint: str,
        capability_id: str = LLM_CAPABILITY_ID,
        tenant_id: str = "system",
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._capability_id = capability_id
        self._tenant_id = tenant_id
        self._timeout = (options or {}).get("timeout", 30.0)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "action": "chat",
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        result = await self._invoke(payload)
        data = result.get("data") or {}
        return data.get("result", "")

    async def embedding(self, text: str) -> List[float]:
        result = await self._invoke({"action": "embedding", "text": text})
        data = result.get("data") or {}
        return data.get("vector", [])

    async def _invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        import httpx

        from jonex_core.common.exceptions import (
            CapabilityTimeoutError,
            UpstreamServiceError,
        )

        request_body = {
            "capability_id": self._capability_id,
            "tenant_id": self._tenant_id,
            "payload": payload,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._endpoint}/invoke", json=request_body)
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException as e:
            raise CapabilityTimeoutError(
                message=f"LLM remote invocation timed out: {self._capability_id}",
                details={"endpoint": self._endpoint},
                cause=e,
            )
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"LLM remote invocation failed: HTTP {e.response.status_code}",
                details={
                    "capability_id": self._capability_id,
                    "upstream_status": e.response.status_code,
                    "upstream_body": e.response.text[:200],
                },
                cause=e,
            )


# ============================================================
# Mock: Test stub
# ============================================================
class MockLLMClient(LLMClient):
    """Stub implementation with no external dependencies"""

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        self._embedding_dim = (options or {}).get("embedding_dim", 1536)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"[Mock LLM] {last[:80]}"

    async def embedding(self, text: str) -> List[float]:
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        return [rng.uniform(-1, 1) for _ in range(self._embedding_dim)]


# ============================================================
# Factory
# ============================================================
def get_llm_client(
    *,
    capability_id: str = LLM_CAPABILITY_ID,
    tenant_id: str = "system",
) -> LLMClient:
    """Returns the corresponding client based on the capability_runtime manifest.

    Usage for business/domain code:
        client = get_llm_client()
        text = await client.chat_completion([...])
    """
    spec = get_locator().get_spec(capability_id)

    if spec.mode == CapabilityMode.MOCK:
        logger.debug(f"LLM client = MOCK ({capability_id})")
        return MockLLMClient(spec.options)

    if spec.mode == CapabilityMode.REMOTE:
        endpoint = spec.endpoint or get_config().SIDECAR_URL
        logger.debug(f"LLM client = REMOTE ({capability_id}, endpoint={endpoint})")
        return RemoteLLMClient(
            endpoint=endpoint,
            capability_id=capability_id,
            tenant_id=tenant_id,
            options=spec.options,
        )

    logger.debug(f"LLM client = LOCAL ({capability_id})")
    return LocalLLMClient(spec.options)
