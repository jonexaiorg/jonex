#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Capability service reverse proxy

Sidecar invokes remote capability services via HTTP proxy, achieving decoupling from capability implementation.
Supports dynamically getting capability service endpoints from service discovery center.
"""

import os
import httpx
from typing import AsyncGenerator, Optional, Dict

from jonex_core.common import get_config, get_logger
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
    """Capability service reverse proxy"""

    def __init__(self):
        self.config = get_config()
        self.registry = get_service_registry()
        self.auth = get_internal_auth()
        # Statically configured capability service addresses (as fallback when service discovery fails)
        self._static_endpoints = {
            "knowledge_base": self.config.KNOWLEDGE_BASE_URL,
            "rag.lightrag": self.config.ATOMIC_RAG_URL,
        }

    @property
    def capability_endpoints(self) -> Dict[str, str]:
        """Get all configured capability endpoints (static configuration)"""
        return self._static_endpoints

    async def invoke_capability(
        self,
        capability_id: str,
        payload: Dict,
        tenant_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Forward invocation to the corresponding Capability service

        Args:
            capability_id: Full capability ID (e.g.: business.knowledge_base.v1)
            payload: Invocation parameters
            tenant_id: Tenant ID
            user_id: User ID (optional)
            request_id: Request ID (optional)

        Returns:
            Result returned by Capability service

        Raises:
            HTTPException: Raised when invocation fails
        """
        service_name = self._extract_service_name(capability_id)
        endpoint = await self._get_capability_endpoint(service_name)

        logger.info(
            f"[Proxy] Forward capability invocation: {capability_id} -> {endpoint}, "
            f"request_id={request_id}, tenant={tenant_id}"
        )

        timeout = float(os.getenv("SIDECAR_PROXY_TIMEOUT", "120"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                # Generate internal service authentication token
                internal_token = self.auth.generate_token("sidecar")

                response = await client.post(
                    f"{endpoint}/invoke",
                    json={
                        "capability_id": capability_id,
                        "payload": payload,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
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
                    f"[Proxy] Capability invocation completed: {capability_id}, "
                    f"success={result.get('success', True)}, latency={response.elapsed.total_seconds() * 1000:.2f}ms"
                )

                return result

            except httpx.TimeoutException:
                logger.error(f"Capability service invocation timed out: {capability_id} -> {endpoint}")
                raise CapabilityTimeoutError(
                    message=f"Capability service invocation timed out: {capability_id}",
                    details={"endpoint": endpoint},
                )
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Capability service returned error: {capability_id}, "
                    f"status={e.response.status_code}, detail={e.response.text[:200]}"
                )
                raise UpstreamServiceError(
                    message=f"Capability service returned error: HTTP {e.response.status_code}",
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
                    hint = f"Container '{service_name}' not started or unresolvable"
                elif "Connection refused" in msg:
                    hint = f"Container '{service_name}' started but port not ready"
                elif "ConnectError" in msg:
                    hint = f"Connection '{service_name}' failed"
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
        request_id: Optional[str] = None,
    ):
        """Stream forward capability invocation, yields NDJSON line by line"""
        service_name = self._extract_service_name(capability_id)
        endpoint = await self._get_capability_endpoint(service_name)

        logger.info(
            f"[Proxy] Stream forwarding: {capability_id} -> {endpoint}, "
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
    ) -> AsyncGenerator[str, None]:
        """Streaming RAG query, directly invokes the capability service streaming query endpoint /query/stream"""
        endpoint = await self._get_capability_endpoint("rag.lightrag")

        logger.info(
            f"[Proxy] Streaming RAG query: -> {endpoint}/query/stream, "
            f"query={query[:80]}, tenant={tenant_id}"
        )

        timeout = float(os.getenv("SIDECAR_PROXY_TIMEOUT", "120"))
        params = {"query": query, "mode": mode, "top_k": str(top_k), "tenant_id": tenant_id}

        async with httpx.AsyncClient(timeout=timeout) as client:
            internal_token = self.auth.generate_token("sidecar")
            async with client.stream(
                "GET",
                f"{endpoint}/query/stream",
                params=params,
                headers={"Authorization": f"Bearer {internal_token}"},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield line

    def _extract_service_name(self, capability_id: str) -> str:
        """
        Extract service name from capability ID

        Format: {type}.{name}.{version}
        business.knowledge_base.v1 -> knowledge_base
        atomic.rag.lightrag.v1  -> rag.lightrag
        """
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
        """
        Get capability service endpoint

        Prefer getting endpoint from service discovery center, fall back to static configuration if unavailable

        Args:
            service_name: Service name

        Returns:
            Service endpoint URL

        Raises:
            HTTPException: Raised when service is not configured
        """
        # Prefer getting from service discovery
        try:
            endpoint = await self.registry.discover(service_name)
            if endpoint:
                logger.debug(f"Got endpoint from service discovery: {service_name} -> {endpoint}")
                return endpoint
        except Exception as e:
            logger.warning(f"Service discovery failed, using static configuration: {e}")

        # Service discovery failed, use static configuration
        endpoint = self._static_endpoints.get(service_name)
        if not endpoint:
            raise CapabilityNotFoundError(
                message=f"Capability service not configured: {service_name}",
                details={"service": service_name},
            )

        logger.debug(f"Using static configured endpoint: {service_name} -> {endpoint}")
        return endpoint


# Global singleton
_proxy_instance: Optional[CapabilityProxy] = None


def get_capability_proxy() -> CapabilityProxy:
    """
    Get capability service proxy instance (singleton)

    Returns:
        CapabilityProxy instance
    """
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = CapabilityProxy()
    return _proxy_instance
