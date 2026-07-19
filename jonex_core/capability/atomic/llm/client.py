#!/usr/bin/python3



from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.locator import CapabilityMode, get_locator
from jonex_core.common import get_config, get_logger, require_tenant

logger = get_logger("capability.client.llm")


LLM_CAPABILITY_ID = "atomic.llm.qwen.v1"


class LLMClient(ABC):


    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        ""

    @abstractmethod
    async def embedding(self, text: str) -> List[float]:
        ""





class LocalLLMClient(LLMClient):


    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:

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





class RemoteLLMClient(LLMClient):


    def __init__(
        self,
        endpoint: str,
        tenant_id: str,
        capability_id: str = LLM_CAPABILITY_ID,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._capability_id = capability_id
        self._tenant_id = require_tenant(tenant_id)
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

        payload = dict(payload)
        payload["tenant_id"] = self._tenant_id
        request_body = {
            "capability_id": self._capability_id,
            "tenant_id": self._tenant_id,
            "payload": payload,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._endpoint}/invoke",
                    json=request_body,
                    headers={"X-Tenant-ID": self._tenant_id},
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException as e:
            raise CapabilityTimeoutError(
                message=f"LLM 远程调用超时: {self._capability_id}",
                details={"endpoint": self._endpoint},
                cause=e,
            )
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"LLM 远程调用失败: HTTP {e.response.status_code}",
                details={
                    "capability_id": self._capability_id,
                    "upstream_status": e.response.status_code,
                    "upstream_body": e.response.text[:200],
                },
                cause=e,
            )





class MockLLMClient(LLMClient):


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





def get_llm_client(
    *,
    capability_id: str = LLM_CAPABILITY_ID,
    tenant_id: Optional[str] = None,
) -> LLMClient:

    spec = get_locator().get_spec(capability_id)

    if spec.mode == CapabilityMode.MOCK:
        logger.debug(f"LLM client = MOCK ({capability_id})")
        return MockLLMClient(spec.options)

    if spec.mode == CapabilityMode.REMOTE:
        tenant_id = require_tenant(tenant_id)
        endpoint = spec.endpoint or get_config().SIDECAR_URL
        logger.debug(f"LLM client = REMOTE ({capability_id}, endpoint={endpoint})")
        return RemoteLLMClient(
            endpoint=endpoint,
            tenant_id=tenant_id,
            capability_id=capability_id,
            options=spec.options,
        )

    logger.debug(f"LLM client = LOCAL ({capability_id})")
    return LocalLLMClient(spec.options)
