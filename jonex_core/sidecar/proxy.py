#!/usr/bin/python3



import os
import httpx
from typing import AsyncGenerator, Optional, Dict

from jonex_core.common import get_config, get_logger, require_tenant
from jonex_core.common.exceptions import (
    CapabilityIdFormatError,
    CapabilityNotFoundError,
    CapabilityTimeoutError,
    UpstreamServiceError,
    ServiceUnavailableError,
)
from jonex_core.discovery import get_service_registry
from jonex_core.security import get_internal_auth

logger = get_logger("sidecar.proxy")


class CapabilityProxy:


    def __init__(self):
        self.config = get_config()
        self.registry = get_service_registry()
        self.auth = get_internal_auth()

        self._static_endpoints = {
            "knowledge_base": self.config.KNOWLEDGE_BASE_URL,
            "business_domain": self.config.BUSINESS_DOMAIN_URL,
            "rag.lightrag": self.config.ATOMIC_RAG_URL,
            "platform": self.config.PLATFORM_URL,
        }

    @property
    def capability_endpoints(self) -> Dict[str, str]:

        return self._static_endpoints

    async def invoke_capability(
        self,
        capability_id: str,
        payload: Dict,
        tenant_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip: Optional[str] = None,
        request_id: Optional[str] = None,
    ):

        tenant_id = require_tenant(tenant_id)
        service_name = self._extract_service_name(capability_id)
        endpoint = await self._get_capability_endpoint(service_name)

        logger.info(
            f"[Proxy] Forwarding capability call: {capability_id} -> {endpoint}, "
            f"request_id={request_id}, tenant={tenant_id}"
        )

        timeout = float(os.getenv("SIDECAR_PROXY_TIMEOUT", "120"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:

                internal_token = self.auth.generate_token("sidecar")

                response = await client.post(
                    f"{endpoint}/invoke",
                    json={
                        "capability_id": capability_id,
                        "payload": payload,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "username": username,
                        "ip": ip,
                        "request_id": request_id,
                    },
                    headers={
                        "X-Request-ID": request_id or "",
                        "X-Tenant-ID": tenant_id,
                        "Authorization": f"Bearer {internal_token}",
                    }
                )

                response.raise_for_status()
                result = response.json()

                logger.info(
                    f"[Proxy] Capability call completed: {capability_id}, "
                    f"success={result.get('success', True)}, latency={response.elapsed.total_seconds() * 1000:.2f}ms"
                )

                return result

            except httpx.TimeoutException:
                logger.error(f"Capability service call timed out: {capability_id} -> {endpoint}")
                raise CapabilityTimeoutError(
                    message=f"Capability service call timed out: {capability_id}",
                    details={"endpoint": endpoint},
                )
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Capability service returned an error: {capability_id}, "
                    f"status={e.response.status_code}, detail={e.response.text[:200]}"
                )
                raise UpstreamServiceError(
                    message=f"Capability service returned an error: HTTP {e.response.status_code}",
                    details={
                        "capability_id": capability_id,
                        "upstream_status": e.response.status_code,
                        "upstream_body": e.response.text[:200],
                    },
                    cause=e,
                )
            except Exception as e:
                msg = str(e)
                if "Name or service not known" in msg:
                    hint = f"容器 '{service_name}' 未启动或无法解析"
                elif "Connection refused" in msg:
                    hint = f"容器 '{service_name}' 已启动但端口未就绪"
                elif "ConnectError" in msg:
                    hint = f"连接 '{service_name}' 失败"
                else:
                    hint = msg
                logger.error(f"Capability service unavailable: {capability_id} -> {endpoint}, {hint}")
                raise ServiceUnavailableError(
                    message=f"Capability service unavailable: {service_name} ({hint})",
                    details={"service": service_name, "endpoint": endpoint, "hint": hint},
                    cause=e,
                )

    async def stream_invoke(
        self,
        capability_id: str,
        payload: Dict,
        tenant_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip: Optional[str] = None,
        request_id: Optional[str] = None,
    ):

        tenant_id = require_tenant(tenant_id)
        service_name = self._extract_service_name(capability_id)
        endpoint = await self._get_capability_endpoint(service_name)

        logger.info(
            f"[Proxy] Forwarding streaming call: {capability_id} -> {endpoint}, "
            f"request_id={request_id}, tenant={tenant_id}"
        )

        timeout = float(os.getenv("SIDECAR_PROXY_TIMEOUT", "120"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            internal_token = self.auth.generate_token("sidecar")
            async with client.stream(
                "POST",
                f"{endpoint}/invoke",
                json={
                    "capability_id": capability_id,
                    "payload": payload,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "username": username,
                    "ip": ip,
                    "request_id": request_id,
                },
                headers={
                    "X-Request-ID": request_id or "",
                    "X-Tenant-ID": tenant_id,
                    "Authorization": f"Bearer {internal_token}",
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield line

    async def stream_rag_query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        user_id: Optional[str] = None,
        knowledge_base_id: str = "",
    ) -> AsyncGenerator[str, None]:

        tenant_id = require_tenant(tenant_id)
        endpoint = await self._get_capability_endpoint("rag.lightrag")

        logger.info(
            f"[Proxy] Streaming RAG query: -> {endpoint}/query/stream, "
            f"query={query[:80]}, tenant={tenant_id}, kb={knowledge_base_id}"
        )

        timeout = float(os.getenv("SIDECAR_PROXY_TIMEOUT", "120"))
        params = {"query": query, "mode": mode, "top_k": str(top_k), "tenant_id": tenant_id}


        if knowledge_base_id:
            params["knowledge_base_id"] = knowledge_base_id

        async with httpx.AsyncClient(timeout=timeout) as client:
            internal_token = self.auth.generate_token("sidecar")
            async with client.stream(
                "GET",
                f"{endpoint}/query/stream",
                params=params,
                headers={
                    "Authorization": f"Bearer {internal_token}",
                    "X-Tenant-ID": tenant_id,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield line

    def _extract_service_name(self, capability_id: str) -> str:

        parts = capability_id.split(".")
        if len(parts) >= 3:
            return ".".join(parts[1:-1])
        if len(parts) == 2:
            return parts[1]
        raise CapabilityIdFormatError(
            message=f"Invalid capability ID format: {capability_id}",
            details={"capability_id": capability_id},
        )

    async def _get_capability_endpoint(self, service_name: str) -> str:


        endpoint = self._static_endpoints.get(service_name)
        if endpoint:
            logger.debug(f"Using statically configured endpoint: {service_name} -> {endpoint}")
            return endpoint


        try:
            endpoint = await self.registry.discover(service_name)
            if endpoint:
                logger.debug(f"Endpoint obtained from service discovery: {service_name} -> {endpoint}")
                return endpoint
        except Exception as e:
            logger.warning(f"Service discovery failed: {e}")

        raise CapabilityNotFoundError(
            message=f"Capability service is not configured: {service_name}",
            details={"service": service_name},
        )



_proxy_instance: Optional[CapabilityProxy] = None


def get_capability_proxy() -> CapabilityProxy:

    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = CapabilityProxy()
    return _proxy_instance
