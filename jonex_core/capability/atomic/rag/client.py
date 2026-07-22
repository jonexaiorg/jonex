#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
RAG Client Abstract + Factory

Business/domain code unified through `get_rag_client()` to get RAGClient, no longer new specific adapter.
- LOCAL: In-process direct call to local LightRAG adapter
- REMOTE: Invoke independent atomic-rag service via Sidecar reverse proxy
- MOCK: Offline/test stub, no external dependencies

Replace implementation (LightRAG -> Milvus + FAISS) only need to extend LocalRAGClient.factory or modify manifest endpoint.
"""

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.locator import CapabilityMode, get_locator
from jonex_core.common import get_config, get_logger

logger = get_logger("capability.client.rag")

# Currently used capability_id (can be overridden in manifest)
RAG_CAPABILITY_ID = "atomic.rag.lightrag.v1"


class RAGClient(ABC):
    """RAG Client contract: domain/business code only depends on this interface"""

    @abstractmethod
    async def insert(
        self,
        file_path: str,
        tenant_id: str = "default",
        output_dir: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        """Insert document into RAG index, immediately return task_id

        Returns:
            {"task_id": str, "status": "pending", "file_path": str}
        """
        pass

    @abstractmethod
    async def query(
        self,
        query: str,
        tenant_id: str = "default",
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        """RAG query, returns answer string"""
        pass

    @abstractmethod
    async def delete(
        self,
        doc_id: str,
        tenant_id: str = "default",
    ) -> bool:
        """Delete document, returns whether success"""
        pass

    @abstractmethod
    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str = "default",
    ) -> dict:
        """Query async task status

        Returns:
            {
                "task_id": str,
                "status": "pending" | "processing" | "completed" | "failed",
                "progress": float,
                "error": str | None
            }
        """
        pass

    # ── storage reader methods ──────────────────────────────────

    @abstractmethod
    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        """Get knowledge base storage summary statistics"""
        pass

    @abstractmethod
    async def get_storage_documents(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """Get knowledge base document list (paginated)"""
        pass

    @abstractmethod
    async def get_storage_entities(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        """Get knowledge base entity list (paginated)"""
        pass

    @abstractmethod
    async def get_storage_relationships(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:
        """Get knowledge base relation list (paginated)"""
        pass

    @abstractmethod
    async def get_storage_graph_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        """Get knowledge graph summary statistics"""
        pass

    @abstractmethod
    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        """Get knowledge graph nodes and edges data"""
        pass

    @abstractmethod
    async def get_document_parse_result(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        """Get document parse result (aggregated summary + documents + entities + relationships)"""
        pass

    @abstractmethod
    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:
        """Re-trigger document ontology extraction (force_ontology_only mode)"""
        pass


# ============================================================
# Local: Direct in-process adapter
# ============================================================
class LocalRAGClient(RAGClient):
    """Direct connection to local LightRAG adapter (only available inside atomic-rag container)"""

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        # Lazy import to avoid loading heavy dependencies in REMOTE/MOCK mode
        from jonex_core.capability.atomic.rag.lightrag_adapter import LightRAGAdapter

        self._adapter = LightRAGAdapter()
        self._options = options or {}
        logger.info("RAG Client initialization: LOCAL mode")

    async def _ensure_initialized(self):
        """Lazy initialize adapter (_task_queue / parser / HTTP client / workers)"""
        if not self._adapter._initialized:
            await self._adapter.initialize()

    async def insert(
        self,
        file_path: str,
        tenant_id: str = "default",
        output_dir: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter.insert(
            file_path, tenant_id, output_dir,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )

    async def query(
        self,
        query: str,
        tenant_id: str = "default",
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        await self._ensure_initialized()
        return await self._adapter.query(query, tenant_id, mode, top_k)

    async def delete(
        self,
        doc_id: str,
        tenant_id: str = "default",
    ) -> bool:
        await self._ensure_initialized()
        return await self._adapter.delete(doc_id, tenant_id)

    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str = "default",
    ) -> dict:
        return await self._adapter.get_task_status(task_id, tenant_id)

    # ── storage reader delegations ──────────────────────────

    def _build_scope(self, knowledge_base_id: str, tenant_id: str) -> dict:
        return {
            "knowledge_base_id": knowledge_base_id,
            "tenant_id": tenant_id,
            "scope_mode": "knowledge_base",
        }

    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        await self._ensure_initialized()
        return self._adapter._storage_reader.get_summary(
            self._build_scope(knowledge_base_id, tenant_id)
        )

    async def get_storage_documents(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return self._adapter._storage_reader.get_documents(
            self._build_scope(knowledge_base_id, tenant_id),
            page=page, page_size=page_size, keyword=keyword, status=status,
        )

    async def get_storage_entities(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return self._adapter._storage_reader.get_entities(
            self._build_scope(knowledge_base_id, tenant_id),
            page=page, page_size=page_size, keyword=keyword,
            entity_type=entity_type, file_path=file_path, document_id=document_id,
        )

    async def get_storage_relationships(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return self._adapter._storage_reader.get_relationships(
            self._build_scope(knowledge_base_id, tenant_id),
            page=page, page_size=page_size, keyword=keyword,
            file_path=file_path, document_id=document_id,
            source_entity=source_entity, target_entity=target_entity,
        )

    async def get_storage_graph_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        await self._ensure_initialized()
        return self._adapter._storage_reader.get_graph_summary(
            self._build_scope(knowledge_base_id, tenant_id)
        )

    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return self._adapter._storage_reader.get_graph(
            self._build_scope(knowledge_base_id, tenant_id),
            limit=limit, keyword=keyword, file_path=file_path, document_id=document_id,
        )

    async def get_document_parse_result(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        await self._ensure_initialized()
        return self._adapter._storage_reader.get_document_parse_result(
            self._build_scope(knowledge_base_id, tenant_id)
        )

    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter.retry_ontology_extract(
            document_id, knowledge_base_id, tenant_id, file_path=file_path,
        )


# ============================================================
# Remote: Via Sidecar reverse proxy
# ============================================================
class RemoteRAGClient(RAGClient):
    """Invoke atomic-rag service via Sidecar reverse proxy (business layer uses this)"""

    def __init__(
        self,
        endpoint: str,
        capability_id: str = RAG_CAPABILITY_ID,
        tenant_id: str = "system",
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        import httpx

        timeout = float(os.getenv("RAG_CLIENT_TIMEOUT", "120"))
        self._client = httpx.AsyncClient(
            base_url=endpoint.rstrip("/"),
            headers={"X-API-Key": "jonex_test_gateway"},
            timeout=(options or {}).get("timeout", timeout),
        )
        self._capability_id = capability_id
        self._tenant_id = tenant_id
        logger.info(f"RAG Client initialization: REMOTE mode, endpoint={endpoint}")

    async def insert(
        self,
        file_path: str,
        tenant_id: str = "default",
        output_dir: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "action": "insert",
            "file_path": file_path,
            "output_dir": output_dir,
        }
        if knowledge_base_id:
            payload["knowledge_base_id"] = knowledge_base_id
        if document_id:
            payload["document_id"] = document_id
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def query(
        self,
        query: str,
        tenant_id: str = "default",
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        payload = {
            "action": "query",
            "query": query,
            "mode": mode,
            "top_k": top_k,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]["answer"]

    async def delete(
        self,
        doc_id: str,
        tenant_id: str = "default",
    ) -> bool:
        payload = {
            "action": "delete",
            "doc_id": doc_id,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]["success"]

    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str = "default",
    ) -> dict:
        payload = {
            "action": "get_task_status",
            "task_id": task_id,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    # ── storage reader (via sidecar → atomic-rag) ──────────

    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        payload = {
            "action": "get_storage_summary",
            "knowledge_base_id": knowledge_base_id,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_storage_documents(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "action": "get_storage_documents",
            "knowledge_base_id": knowledge_base_id,
            "page": page,
            "page_size": page_size,
        }
        if keyword:
            payload["keyword"] = keyword
        if status:
            payload["status"] = status
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_storage_entities(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "action": "get_storage_entities",
            "knowledge_base_id": knowledge_base_id,
            "page": page,
            "page_size": page_size,
        }
        if keyword:
            payload["keyword"] = keyword
        if entity_type:
            payload["entity_type"] = entity_type
        if file_path:
            payload["file_path"] = file_path
        if document_id:
            payload["document_id"] = document_id
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_storage_relationships(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "action": "get_storage_relationships",
            "knowledge_base_id": knowledge_base_id,
            "page": page,
            "page_size": page_size,
        }
        if keyword:
            payload["keyword"] = keyword
        if file_path:
            payload["file_path"] = file_path
        if document_id:
            payload["document_id"] = document_id
        if source_entity:
            payload["source_entity"] = source_entity
        if target_entity:
            payload["target_entity"] = target_entity
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_storage_graph_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        payload = {
            "action": "get_storage_graph_summary",
            "knowledge_base_id": knowledge_base_id,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "action": "get_storage_graph",
            "knowledge_base_id": knowledge_base_id,
            "limit": limit,
        }
        if keyword:
            payload["keyword"] = keyword
        if file_path:
            payload["file_path"] = file_path
        if document_id:
            payload["document_id"] = document_id
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_document_parse_result(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        payload = {
            "action": "get_document_parse_result",
            "knowledge_base_id": knowledge_base_id,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:
        payload = {
            "action": "retry_ontology_extract",
            "document_id": document_id,
            "knowledge_base_id": knowledge_base_id,
            "file_path": file_path,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def _invoke(self, payload: dict, tenant_id: str) -> dict:
        """Unified invoke Sidecar /invoke interface"""
        body = {
            "capability_id": self._capability_id,
            "payload": payload,
            "tenant_id": tenant_id or self._tenant_id,
        }
        resp = await self._client.post("/invoke", json=body)
        resp.raise_for_status()
        return resp.json()


# ============================================================
# Mock: Test / offline stub
# ============================================================
class MockRAGClient(RAGClient):
    """In-memory stub implementation, for unit tests and offline development"""

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        self._tasks: Dict[str, dict] = {}
        self._docs: set[str] = set()
        logger.info("RAG Client initialization: MOCK mode")

    async def insert(
        self,
        file_path: str,
        tenant_id: str = "default",
        output_dir: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "progress": 1.0,
            "error": None,
        }
        self._docs.add(f"{tenant_id}:{file_path}")
        return {
            "task_id": task_id,
            "status": "pending",
            "file_path": file_path,
        }

    async def query(
        self,
        query: str,
        tenant_id: str = "default",
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        return f"[MOCK RAG answer] Answer about '{query}': This is a test reply from Mock."

    async def delete(
        self,
        doc_id: str,
        tenant_id: str = "default",
    ) -> bool:
        key = f"{tenant_id}:{doc_id}"
        if key in self._docs:
            self._docs.remove(key)
            return True
        return False

    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str = "default",
    ) -> dict:
        return self._tasks.get(task_id, {
            "task_id": task_id,
            "status": "not_found",
            "progress": 0.0,
            "error": "task not found",
        })

    # ── storage reader (mock: empty data) ──────────────────

    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        return {
            "knowledge_base_id": knowledge_base_id,
            "tenant_id": tenant_id,
            "source": "mock",
            "scope_mode": "knowledge_base",
            "status": "storage_missing",
            "documents_count": 0,
            "processed_documents_count": 0,
            "failed_documents_count": 0,
            "chunks_count": 0,
            "entities_count": 0,
            "relationships_count": 0,
            "compile_versions_count": 0,
            "last_updated_at": None,
            "storage_files": {},
        }

    async def get_storage_documents(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def get_storage_entities(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def get_storage_relationships(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def get_storage_graph_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        return {
            "nodes_count": 0, "edges_count": 0,
            "entity_type_count": 0, "relation_type_count": 0,
            "avg_degree": 0, "entity_type_distribution": [], "relation_distribution": [],
        }

    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        return {"nodes": [], "edges": []}

    async def get_document_parse_result(
        self,
        knowledge_base_id: str,
        tenant_id: str = "default",
    ) -> dict:
        return {"summary": {}, "documents": [], "entities": [], "relationships": []}

    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:
        return {"status": "completed", "task_id": str(uuid.uuid4())}


# ============================================================
# Factory: returns corresponding client based on runtime manifest
# ============================================================
def get_rag_client(
    capability_id: str = RAG_CAPABILITY_ID,
    tenant_id: str = "default",
) -> RAGClient:
    """Get RAG Client (business/domain code unified invoke this entry point)"""
    spec = get_locator().get_spec(capability_id)

    if spec.mode == CapabilityMode.MOCK:
        return MockRAGClient()

    if spec.mode == CapabilityMode.LOCAL:
        return LocalRAGClient()

    if spec.mode == CapabilityMode.REMOTE:
        cfg = get_config()
        return RemoteRAGClient(
            endpoint=spec.endpoint or cfg.SIDECAR_URL or "http://sidecar:8000",
            capability_id=capability_id,
            tenant_id=tenant_id,
        )

    raise ValueError(f"Unsupported RAG capability mode: {spec.mode}")
