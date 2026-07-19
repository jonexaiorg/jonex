#!/usr/bin/python3



from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.locator import CapabilityMode, get_locator
from jonex_core.common import (
    CapabilityInvokeError,
    InvalidParameterError,
    get_config,
    get_logger,
    require_tenant,
)

logger = get_logger("capability.client.rag")


RAG_CAPABILITY_ID = "atomic.rag.lightrag.v1"


def require_knowledge_base(knowledge_base_id: Optional[str]) -> str:
    return (knowledge_base_id or "").strip()


class RAGClient(ABC):


    @abstractmethod
    async def insert(
        self,
        file_path: str,
        tenant_id: str,
        output_dir: Optional[str] = None,
        *,
        knowledge_base_id: str,
        document_id: Optional[str] = None,
        ontology_schema: Optional[dict] = None,
        storage_backend: str = "local",
        storage_key: Optional[str] = None,
    ) -> dict:

        pass

    @abstractmethod
    async def query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> str:

        pass

    @abstractmethod
    async def query_detailed(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> dict:

        pass

    @abstractmethod
    async def delete(
        self,
        doc_id: str,
        tenant_id: str,
        *,
        knowledge_base_id: str = "",
    ) -> bool:

        pass

    @abstractmethod
    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str,
    ) -> dict:

        pass



    @abstractmethod
    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> dict:

        pass

    @abstractmethod
    async def get_storage_documents(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:

        pass

    @abstractmethod
    async def get_storage_entities(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:

        pass

    @abstractmethod
    async def get_storage_relationships(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:

        pass

    @abstractmethod
    async def get_storage_graph_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> dict:

        pass

    @abstractmethod
    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:

        pass

    @abstractmethod
    async def get_document_parse_result(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        document_id: Optional[str] = None,
    ) -> dict:

        pass

    @abstractmethod
    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:

        pass





class LocalRAGClient(RAGClient):


    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:

        from jonex_core.capability.atomic.rag.lightrag_adapter import LightRAGAdapter

        self._adapter = LightRAGAdapter()
        self._options = options or {}
        logger.info("RAG Client initialized in LOCAL mode")

    async def _ensure_initialized(self):

        if not self._adapter._initialized:
            await self._adapter.initialize()

    async def insert(
        self,
        file_path: str,
        tenant_id: str,
        output_dir: Optional[str] = None,
        *,
        knowledge_base_id: str,
        document_id: Optional[str] = None,
        ontology_schema: Optional[dict] = None,
        storage_backend: str = "local",
        storage_key: Optional[str] = None,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        await self._ensure_initialized()
        return await self._adapter.insert(
            file_path=file_path,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            output_dir=output_dir,
            document_id=document_id,
            ontology_schema=ontology_schema,
            storage_backend=storage_backend,
            storage_key=storage_key or file_path,
        )

    async def query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> str:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        await self._ensure_initialized()
        return await self._adapter.query(
            query,
            tenant_id,
            mode,
            top_k,
            knowledge_base_id=knowledge_base_id,
            trace_id=trace_id,
        )

    async def query_detailed(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        await self._ensure_initialized()
        return await self._adapter.query_detailed(
            query,
            tenant_id,
            mode,
            top_k,
            knowledge_base_id=knowledge_base_id,
            trace_id=trace_id,
        )

    async def delete(
        self,
        doc_id: str,
        tenant_id: str,
        *,
        knowledge_base_id: str = "",
    ) -> bool:
        tenant_id = require_tenant(tenant_id)
        await self._ensure_initialized()
        return await self._adapter.delete(
            doc_id, tenant_id, knowledge_base_id=knowledge_base_id
        )

    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        return await self._adapter.get_task_status(task_id, tenant_id)



    def _build_scope(self, knowledge_base_id: str, tenant_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        return {
            "knowledge_base_id": knowledge_base_id,
            "tenant_id": tenant_id,
            "scope_mode": "knowledge_base",
        }

    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter._reader().get_summary(
            self._build_scope(knowledge_base_id, tenant_id)
        )

    async def get_storage_documents(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter._reader().get_documents(
            self._build_scope(knowledge_base_id, tenant_id),
            page=page, page_size=page_size, keyword=keyword, status=status,
        )

    async def get_storage_entities(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter._reader().get_entities(
            self._build_scope(knowledge_base_id, tenant_id),
            page=page, page_size=page_size, keyword=keyword,
            entity_type=entity_type, file_path=file_path, document_id=document_id,
        )

    async def get_storage_relationships(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter._reader().get_relationships(
            self._build_scope(knowledge_base_id, tenant_id),
            page=page, page_size=page_size, keyword=keyword,
            file_path=file_path, document_id=document_id,
            source_entity=source_entity, target_entity=target_entity,
        )

    async def get_storage_graph_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter._reader().get_graph_summary(
            self._build_scope(knowledge_base_id, tenant_id)
        )

    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        return await self._adapter._reader().get_graph(
            self._build_scope(knowledge_base_id, tenant_id),
            limit=limit, keyword=keyword, file_path=file_path, document_id=document_id,
        )

    async def get_document_parse_result(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        document_id: Optional[str] = None,
    ) -> dict:
        await self._ensure_initialized()
        scope = self._build_scope(knowledge_base_id, tenant_id)
        if document_id:
            scope["document_ids"] = [document_id]
        return await self._adapter._reader().get_document_parse_result(
            scope
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





class RemoteRAGClient(RAGClient):


    def __init__(
        self,
        endpoint: str,
        capability_id: str = RAG_CAPABILITY_ID,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        import httpx

        timeout = float(os.getenv("RAG_CLIENT_TIMEOUT", "120"))
        self._client = httpx.AsyncClient(
            base_url=endpoint.rstrip("/"),
            headers={"X-API-Key": get_config().SIDECAR_API_KEY},
            timeout=(options or {}).get("timeout", timeout),
        )
        self._capability_id = capability_id
        logger.info(f"RAG Client initialized in REMOTE mode, endpoint={endpoint}")

    def _build_scope(self, knowledge_base_id: str, tenant_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        return {
            "knowledge_base_id": knowledge_base_id,
            "tenant_id": tenant_id,
            "scope_mode": "knowledge_base",
        }

    async def insert(
        self,
        file_path: str,
        tenant_id: str,
        output_dir: Optional[str] = None,
        *,
        knowledge_base_id: str,
        document_id: Optional[str] = None,
        ontology_schema: Optional[dict] = None,
        storage_backend: str = "local",
        storage_key: Optional[str] = None,
    ) -> dict:
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        payload: dict = {
            "action": "insert",
            "file_path": file_path,
            "output_dir": output_dir,
            "knowledge_base_id": knowledge_base_id,
            "storage_backend": storage_backend,
            "storage_key": storage_key or file_path,
        }
        if document_id:
            payload["document_id"] = document_id
        if ontology_schema:
            payload["ontology_schema"] = ontology_schema
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> str:
        result = await self.query_detailed(
            query=query, tenant_id=tenant_id, mode=mode, top_k=top_k,
            knowledge_base_id=knowledge_base_id, trace_id=trace_id,
        )
        return result["answer"]

    async def query_detailed(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> dict:
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        payload: dict = {
            "action": "query",
            "query": query,
            "mode": mode,
            "top_k": top_k,
            "knowledge_base_id": knowledge_base_id,
            "trace_id": trace_id,
        }
        resp = await self._invoke(payload, tenant_id)
        data = resp["data"]
        return {
            "answer": data.get("answer", ""),
            "references": data.get("references", []),
        }

    async def delete(
        self,
        doc_id: str,
        tenant_id: str,
        *,
        knowledge_base_id: str = "",
    ) -> bool:
        payload = {
            "action": "delete",
            "doc_id": doc_id,
            "knowledge_base_id": knowledge_base_id,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]["success"]

    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str,
    ) -> dict:
        payload = {
            "action": "get_task_status",
            "task_id": task_id,
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]



    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> dict:
        payload = {
            "action": "get_storage_summary",
            "knowledge_base_id": knowledge_base_id,
            "scope": self._build_scope(knowledge_base_id, tenant_id),
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_storage_documents(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "action": "get_storage_documents",
            "knowledge_base_id": knowledge_base_id,
            "scope": self._build_scope(knowledge_base_id, tenant_id),
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
        tenant_id: str,
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
            "scope": self._build_scope(knowledge_base_id, tenant_id),
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
        tenant_id: str,
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
            "scope": self._build_scope(knowledge_base_id, tenant_id),
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
        tenant_id: str,
    ) -> dict:
        payload = {
            "action": "get_storage_graph_summary",
            "knowledge_base_id": knowledge_base_id,
            "scope": self._build_scope(knowledge_base_id, tenant_id),
        }
        resp = await self._invoke(payload, tenant_id)
        return resp["data"]

    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "action": "get_storage_graph",
            "knowledge_base_id": knowledge_base_id,
            "scope": self._build_scope(knowledge_base_id, tenant_id),
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
        tenant_id: str,
        document_id: Optional[str] = None,
    ) -> dict:
        payload = {
            "action": "get_document_parse_result",
            "knowledge_base_id": knowledge_base_id,
            "scope": self._build_scope(knowledge_base_id, tenant_id),
        }
        if document_id:
            payload["document_id"] = document_id
            payload["scope"]["document_ids"] = [document_id]
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

        tenant_id = require_tenant(tenant_id)
        payload = dict(payload)
        payload["tenant_id"] = tenant_id
        body = {
            "capability_id": self._capability_id,
            "payload": payload,
            "tenant_id": tenant_id,
        }
        resp = await self._client.post(
            "/invoke",
            json=body,
            headers={"X-Tenant-ID": tenant_id},
        )
        resp.raise_for_status()
        result = resp.json()



        action = payload.get("action", "unknown")
        if not isinstance(result, dict) or not result.get("success", False):
            message = (
                result.get("message") if isinstance(result, dict) else None
            ) or "RAG 能力调用失败"
            raise CapabilityInvokeError(
                message=f"RAG[{action}] 调用失败: {message}",
                details={"action": action},
            )
        if result.get("data") is None:
            raise CapabilityInvokeError(
                message=f"RAG[{action}] 返回空数据（data=null）",
                details={"action": action},
            )
        return result





class MockRAGClient(RAGClient):


    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        self._tasks: Dict[str, dict] = {}
        self._docs: set[str] = set()
        logger.info("RAG Client initialized in MOCK mode")

    async def insert(
        self,
        file_path: str,
        tenant_id: str,
        output_dir: Optional[str] = None,
        *,
        knowledge_base_id: str,
        document_id: Optional[str] = None,
        ontology_schema: Optional[dict] = None,
        storage_backend: str = "local",
        storage_key: Optional[str] = None,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "knowledge_base_id": knowledge_base_id,
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
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> str:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return f"[MOCK RAG 回答] 关于'{query}'的回答：这是来自 Mock 的测试回复。"

    async def query_detailed(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {
            "answer": f"[MOCK RAG 回答] 关于'{query}'的回答：这是来自 Mock 的测试回复。",
            "references": [],
        }

    async def delete(
        self,
        doc_id: str,
        tenant_id: str,
        *,
        knowledge_base_id: str = "",
    ) -> bool:
        tenant_id = require_tenant(tenant_id)
        key = f"{tenant_id}:{doc_id}"
        if key in self._docs:
            self._docs.remove(key)
            return True
        return False

    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        task = self._tasks.get(task_id)
        if task and task.get("tenant_id") != tenant_id:
            return {
                "task_id": task_id,
                "status": "not_found",
                "progress": 0.0,
                "error": "task not found",
            }
        return task or {
            "task_id": task_id,
            "status": "not_found",
            "progress": 0.0,
            "error": "task not found",
        }



    async def get_storage_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = require_knowledge_base(knowledge_base_id)
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
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def get_storage_entities(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def get_storage_relationships(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def get_storage_graph_summary(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {
            "nodes_count": 0, "edges_count": 0,
            "entity_type_count": 0, "relation_type_count": 0,
            "avg_degree": 0, "entity_type_distribution": [], "relation_distribution": [],
        }

    async def get_storage_graph(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {"nodes": [], "edges": []}

    async def get_document_parse_result(
        self,
        knowledge_base_id: str,
        tenant_id: str,
        document_id: Optional[str] = None,
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {
            "document_id": document_id,
            "summary": {},
            "documents": [],
            "entities": [],
            "relationships": [],
        }

    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:
        require_tenant(tenant_id)
        require_knowledge_base(knowledge_base_id)
        return {"status": "completed", "task_id": str(uuid.uuid4())}





def get_rag_client(
    capability_id: str = RAG_CAPABILITY_ID,
) -> RAGClient:

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
        )

    raise ValueError(f"不支持的 RAG 能力模式：{spec.mode}")
