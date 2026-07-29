#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
LLM Client 抽象 + 工厂

业务/领域代码统一通过 `get_llm_client()` 获取 LLMClient，不再 new 具体适配器。
- LOCAL：进程内直接调用本地适配器（默认走 QwenLLMCapability）
- REMOTE：通过 Sidecar 反代调用独立 LLM 能力服务
- MOCK：离线/测试桩，不依赖任何外部资源

替换提供方（Qwen → DeepSeek 等）只需扩展 LocalLLMClient.factory 或修改清单 endpoint。
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.locator import CapabilityMode, get_locator
from jonex_core.common import get_config, get_logger, require_tenant
from jonex_core.common.i18n import translate

logger = get_logger("capability.client.llm")

# 当前使用的 capability_id（清单中可覆盖）
LLM_CAPABILITY_ID = "atomic.llm.qwen.v1"


class LLMClient(ABC):
    """LLM 客户端契约：领域/业务代码只依赖此接口"""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """聊天补全"""

    @abstractmethod
    async def embedding(self, text: str) -> List[float]:
        """文本向量化"""


# ============================================================
# Local：直连进程内适配器
# ============================================================
class LocalLLMClient(LLMClient):
    """直连本地适配器"""

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        # 延迟导入避免在 REMOTE/MOCK 模式下加载重依赖
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
# Remote：通过 Sidecar 反代
# ============================================================
class RemoteLLMClient(LLMClient):
    """通过 Sidecar 反代调用远程 LLM 服务

    TODO(G3.2): 当 #3（平台 LLMClient）有真实流量时，base_url 改指 llm-gateway:8787。
    当前 endpoint 来自 capability locator，指向 Sidecar；后续应改为直连网关的 OpenAI 兼容端点。
    """

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
                message=translate("err.capability.llm_timeout", params={"capability_id": self._capability_id}, fallback=f"LLM 远程调用超时: {self._capability_id}"),
                details={"endpoint": self._endpoint},
                cause=e,
            )
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=translate("err.capability.llm_upstream_error", params={"status": str(e.response.status_code)}, fallback=f"LLM 远程调用失败: HTTP {e.response.status_code}"),
                details={
                    "capability_id": self._capability_id,
                    "upstream_status": e.response.status_code,
                    "upstream_body": e.response.text[:200],
                },
                cause=e,
            )


# ============================================================
# Mock：测试桩
# ============================================================
class MockLLMClient(LLMClient):
    """无外部依赖的桩实现"""

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
# 工厂
# ============================================================
def get_llm_client(
    *,
    capability_id: str = LLM_CAPABILITY_ID,
    tenant_id: Optional[str] = None,
) -> LLMClient:
    """根据 capability_runtime 清单返回对应 Client。

    业务/领域代码用法：
        client = get_llm_client()
        text = await client.chat_completion([...])
    """
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
