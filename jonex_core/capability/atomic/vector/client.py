#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Vector Client Abstract + Factory

Business and domain code obtains clients through `get_vector_client()` instead of instantiating concrete adapters directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.locator import CapabilityMode, get_locator
from jonex_core.common import get_config, get_logger

logger = get_logger("capability.client.vector")

VECTOR_CAPABILITY_ID = "atomic.vector.milvus.v1"


class VectorClient(ABC):
    """Interface for vector retrieval clients."""

    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        ...

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        ...


# ============================================================
# Local
# ============================================================
class LocalVectorClient(VectorClient):
    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        from jonex_core.capability.atomic.vector.milvus_adapter import (
            MilvusVectorCapability,
        )

        self._adapter = MilvusVectorCapability()
        self._options = options or {}

    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        return await self._adapter.insert(collection_name, vectors, metadatas)

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        return await self._adapter.search(collection_name, query_vector, top_k)

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        return await self._adapter.delete(collection_name, ids)


# ============================================================
# Remote
# ============================================================
class RemoteVectorClient(VectorClient):
    def __init__(
        self,
        endpoint: str,
        capability_id: str = VECTOR_CAPABILITY_ID,
        tenant_id: str = "system",
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._capability_id = capability_id
        self._tenant_id = tenant_id
        self._timeout = (options or {}).get("timeout", 30.0)

    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        result = await self._invoke({
            "action": "insert",
            "collection_name": collection_name,
            "vectors": vectors,
            "metadatas": metadatas,
        })
        return bool((result.get("data") or {}).get("success"))

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        result = await self._invoke({
            "action": "search",
            "collection_name": collection_name,
            "query_vector": query_vector,
            "top_k": top_k,
        })
        return (result.get("data") or {}).get("results", [])

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        result = await self._invoke({
            "action": "delete",
            "collection_name": collection_name,
            "ids": ids,
        })
        return bool((result.get("data") or {}).get("success"))

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
                message=f"Remote vector retrieval timed out: {self._capability_id}",
                details={"endpoint": self._endpoint},
                cause=e,
            )
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"Remote vector retrieval failed: HTTP {e.response.status_code}",
                details={
                    "capability_id": self._capability_id,
                    "upstream_status": e.response.status_code,
                    "upstream_body": e.response.text[:200],
                },
                cause=e,
            )


# ============================================================
# Mock: in-memory implementation for unit tests
# ============================================================
class MockVectorClient(VectorClient):
    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        bucket = self._store.setdefault(collection_name, [])
        metadatas = metadatas or [{} for _ in vectors]
        for i, v in enumerate(vectors):
            bucket.append({
                "id": f"mock_{collection_name}_{len(bucket)}",
                "vector": v,
                "metadata": metadatas[i] if i < len(metadatas) else {},
            })
        return True

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        bucket = self._store.get(collection_name, [])
        # Return the first top_k items with decreasing simulated scores.
        return [
            {"id": item["id"], "score": max(0.0, 1.0 - i * 0.1), "metadata": item["metadata"]}
            for i, item in enumerate(bucket[:top_k])
        ]

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        bucket = self._store.get(collection_name)
        if not bucket:
            return True
        self._store[collection_name] = [item for item in bucket if item["id"] not in ids]
        return True


# ============================================================
# Factory
# ============================================================
def get_vector_client(
    *,
    capability_id: str = VECTOR_CAPABILITY_ID,
    tenant_id: str = "system",
) -> VectorClient:
    spec = get_locator().get_spec(capability_id)

    if spec.mode == CapabilityMode.MOCK:
        logger.debug(f"Vector client = MOCK ({capability_id})")
        return MockVectorClient(spec.options)

    if spec.mode == CapabilityMode.REMOTE:
        endpoint = spec.endpoint or get_config().SIDECAR_URL
        logger.debug(f"Vector client = REMOTE ({capability_id}, endpoint={endpoint})")
        return RemoteVectorClient(
            endpoint=endpoint,
            capability_id=capability_id,
            tenant_id=tenant_id,
            options=spec.options,
        )

    logger.debug(f"Vector client = LOCAL ({capability_id})")
    return LocalVectorClient(spec.options)
