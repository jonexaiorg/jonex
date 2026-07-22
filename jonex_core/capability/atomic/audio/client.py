#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
ASR Client Abstract + Factory
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.locator import CapabilityMode, get_locator
from jonex_core.common import get_config, get_logger

logger = get_logger("capability.client.asr")

ASR_CAPABILITY_ID = "atomic.audio.asr.v1"


class ASRClient(ABC):
    """ASR Client contract"""

    @abstractmethod
    async def transcribe(self, audio_url: str) -> str:
        ...

    @abstractmethod
    async def transcribe_file(self, file_path: str) -> str:
        ...


# ============================================================
# Local
# ============================================================
class LocalASRClient(ASRClient):
    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        from jonex_core.capability.atomic.audio.asr_adapter import ASRCapability

        self._adapter = ASRCapability()
        self._options = options or {}

    async def transcribe(self, audio_url: str) -> str:
        return await self._adapter.transcribe(audio_url)

    async def transcribe_file(self, file_path: str) -> str:
        return await self._adapter.transcribe_file(file_path)


# ============================================================
# Remote
# ============================================================
class RemoteASRClient(ASRClient):
    def __init__(
        self,
        endpoint: str,
        capability_id: str = ASR_CAPABILITY_ID,
        tenant_id: str = "system",
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._capability_id = capability_id
        self._tenant_id = tenant_id
        self._timeout = (options or {}).get("timeout", 60.0)

    async def transcribe(self, audio_url: str) -> str:
        result = await self._invoke({"action": "transcribe", "audio_url": audio_url})
        return (result.get("data") or {}).get("text", "")

    async def transcribe_file(self, file_path: str) -> str:
        result = await self._invoke({"action": "transcribe_file", "file_path": file_path})
        return (result.get("data") or {}).get("text", "")

    async def _invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        import httpx

        from jonex_core.common.exceptions import (
            CapabilityTimeoutError,
            UpstreamServiceError,
        )

        body = {
            "capability_id": self._capability_id,
            "tenant_id": self._tenant_id,
            "payload": payload,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._endpoint}/invoke", json=body)
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException as e:
            raise CapabilityTimeoutError(
                message=f"ASR remote invocation timed out: {self._capability_id}",
                details={"endpoint": self._endpoint},
                cause=e,
            )
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"ASR remote invocation failed: HTTP {e.response.status_code}",
                details={
                    "capability_id": self._capability_id,
                    "upstream_status": e.response.status_code,
                    "upstream_body": e.response.text[:200],
                },
                cause=e,
            )


# ============================================================
# Mock
# ============================================================
class MockASRClient(ASRClient):
    async def transcribe(self, audio_url: str) -> str:
        return f"[Mock ASR] transcribe url={audio_url}"

    async def transcribe_file(self, file_path: str) -> str:
        return f"[Mock ASR] transcribe file={file_path}"


# ============================================================
# Factory
# ============================================================
def get_asr_client(
    *,
    capability_id: str = ASR_CAPABILITY_ID,
    tenant_id: str = "system",
) -> ASRClient:
    spec = get_locator().get_spec(capability_id)

    if spec.mode == CapabilityMode.MOCK:
        logger.debug(f"ASR client = MOCK ({capability_id})")
        return MockASRClient()

    if spec.mode == CapabilityMode.REMOTE:
        endpoint = spec.endpoint or get_config().SIDECAR_URL
        logger.debug(f"ASR client = REMOTE ({capability_id}, endpoint={endpoint})")
        return RemoteASRClient(
            endpoint=endpoint,
            capability_id=capability_id,
            tenant_id=tenant_id,
            options=spec.options,
        )

    logger.debug(f"ASR client = LOCAL ({capability_id})")
    return LocalASRClient(spec.options)
