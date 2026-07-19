

import logging
import os
from typing import Any, Optional

from sqlalchemy import or_, select

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.audit import schedule_emit
from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import ResourceConflictError, ResourceNotFoundError
from jonex_core.common.neo4j_client import get_neo4j_driver
from jonex_core.common.object_storage import build_object_key, get_object_storage, get_object_storage_for
from jonex_core.common.tenant import require_tenant

from ..models import DocStatus, KnowledgeDocument, OntologyStatus
from ..models.data_source import KnowledgeDataSource
from ..repository import FolderRepository, KnowledgeDocumentRepository, OntologyGraphRepository
from ..dtos import DocumentListRequest, DocumentScopeRequest, DocumentUploadRequest, SetDocumentFolderRequest

logger = logging.getLogger(__name__)


def _payload(model_or_dict: Any) -> dict[str, Any]:
    if isinstance(model_or_dict, dict):
        return model_or_dict
    if hasattr(model_or_dict, "model_dump"):
        return model_or_dict.model_dump(exclude_none=True)
    return model_or_dict.dict(exclude_none=True)


def _audit_user_id(user_id: Optional[str]) -> Optional[int]:

    if user_id and user_id.isdigit():
        return int(user_id)
    return None


class DocumentService:



    _FILE_ACCESS_TYPE = "file"

    async def _require_file_data_source_id(self, tenant_id: str, kb_id: str) -> str:

        async with get_db_session() as session:
            ds = (
                await session.execute(
                    select(KnowledgeDataSource)
                    .where(
                        KnowledgeDataSource.tenant_id == tenant_id,
                        KnowledgeDataSource.knowledge_base_id == kb_id,
                        KnowledgeDataSource.access_type == self._FILE_ACCESS_TYPE,
                        KnowledgeDataSource.is_deleted == 0,
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()
        if ds is None:
            raise ResourceNotFoundError(
                message="No file upload data source is configured for this knowledge base. Add one in Data Source Settings before uploading",
                details={"knowledge_base_id": kb_id, "access_type": self._FILE_ACCESS_TYPE},
            )
        return ds.id

    async def upload_document(self, tenant_id: str, request: DocumentUploadRequest | dict, *, user_id: Optional[str] = None, username: Optional[str] = None, ip: Optional[str] = None) -> dict:
        tenant_id = require_tenant(tenant_id)
        data = _payload(request)
        req = DocumentUploadRequest(**data)
        metadata = dict(req.metadata or {})



        if not metadata.get("data_source_id"):
            metadata["data_source_id"] = await self._require_file_data_source_id(tenant_id, req.knowledge_base_id)
            metadata.setdefault("source", self._FILE_ACCESS_TYPE)

        data_source_type = metadata.get("source")

        storage_key = req.storage_key or req.file_path
        storage_backend = req.storage_backend

        if storage_backend == "local" and os.getenv("OBJECT_STORAGE_BACKEND", "local") == "cos":
            storage_backend = "cos"




        if storage_backend == "cos":
            file_path = req.file_path or storage_key
        else:
            file_path = get_object_storage().fs_path(storage_key) or req.file_path or storage_key

        doc_id = req.doc_id or None
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.create(
                KnowledgeDocument(
                    id=doc_id,
                    tenant_id=tenant_id,
                    file_name=req.file_name,
                    file_path=file_path,
                    file_size=req.file_size,
                    mime_type=req.mime_type,
                    knowledge_base_id=req.knowledge_base_id,
                    storage_backend=storage_backend,
                    storage_key=storage_key,
                    status=DocStatus.PARSING.value,
                    ontology_status=OntologyStatus.PENDING.value,
                    folder_id=req.folder_id,
                    extra_metadata=metadata,
                    data_source_type=data_source_type,
                )
            )
            doc_id = doc.id
            doc_dict = doc.to_dict()

        uid = _audit_user_id(user_id)
        schedule_emit({
            "tenant_id": tenant_id,
            "user_id": uid,
            "username": username,
            "ip": ip,
            "log_type": "OPERATION",
            "action": "document.upload",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": "document",
            "resource_id": str(doc_id),
            "request_params": {"file_name": req.file_name, "knowledge_base_id": req.knowledge_base_id},
        })
        schedule_emit({
            "tenant_id": tenant_id,
            "user_id": uid,
            "username": username,
            "ip": ip,
            "log_type": "TASK",
            "action": "document.parse",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": "document",
            "resource_id": str(doc_id),
        })


        if storage_backend == "cos":
            exists = await get_object_storage().head_object(storage_key)
            if not exists:
                raise ResourceNotFoundError(
                    message=f"COS object does not exist or the upload is incomplete: {storage_key}",
                    details={"storage_key": storage_key},
                )


        schema = None
        try:
            from .ontology_compiler import OntologyCompiler
            compiler = OntologyCompiler()
            schema = await compiler.get_compiled_schema(tenant_id, req.knowledge_base_id, auto_compile=True)
            if schema is None:
                logger.warning("No compiled schema available for KB %s after auto-compile", req.knowledge_base_id)
        except Exception as exc:
            logger.warning("Failed to ensure compiled schema for KB %s: %s", req.knowledge_base_id, exc)

        try:
            rag_result = await get_rag_client().insert(
                file_path=file_path,
                tenant_id=tenant_id,
                knowledge_base_id=req.knowledge_base_id,
                document_id=doc_id,
                ontology_schema=schema,
                storage_backend=storage_backend,
                storage_key=storage_key,
            )
        except Exception as exc:
            logger.exception("Knowledge document ingestion failed: %s", doc_id)
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                doc = await repo.get_required(doc_id, tenant_id)
                await repo.set_status(doc, DocStatus.FAILED, error_message=str(exc))
                doc_dict = doc.to_dict()
            schedule_emit({
                "tenant_id": tenant_id,
                "user_id": uid,
                "username": username,
                "ip": ip,
                "log_type": "TASK",
                "action": "document.parse_failed",
                "outcome": "FAILED",
                "service_name": "knowledge_base",
                "resource": "document",
                "resource_id": str(doc_id),
                "error_message": str(exc)[:1000],
            })
            return doc_dict

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(doc_id, tenant_id)
            status = DocStatus.READY if not rag_result.get("task_id") else DocStatus.PARSING
            await repo.set_status(
                doc,
                status,
                rag_task_id=rag_result.get("task_id"),
                rag_doc_ids=rag_result.get("doc_ids") or rag_result.get("document_ids") or [],
            )
            doc.extra_metadata = {**(doc.extra_metadata or {}), "rag_result": rag_result}
            doc_dict = doc.to_dict()

        if status == DocStatus.READY:
            schedule_emit({
                "tenant_id": tenant_id,
                "user_id": uid,
                "username": username,
                "ip": ip,
                "log_type": "TASK",
                "action": "document.parse_done",
                "outcome": "SUCCESS",
                "service_name": "knowledge_base",
                "resource": "document",
                "resource_id": str(doc_id),
            })

        return doc_dict

    async def generate_upload_url(
        self, tenant_id: str, kb_id: str, file_name: str, content_type: str | None = None,
    ) -> dict:

        from uuid import uuid4

        tenant_id = require_tenant(tenant_id)
        doc_id = str(uuid4())
        storage_key = build_object_key(tenant_id, kb_id, doc_id, file_name)

        storage = get_object_storage()
        try:
            upload_url = await storage.presigned_put_url(storage_key, expires=300)
        except Exception:

            upload_url = None

        return {
            "doc_id": doc_id,
            "storage_key": storage_key,
            "upload_url": upload_url,
            "storage_backend": os.getenv("OBJECT_STORAGE_BACKEND", "local"),
        }

    async def get_raw_location(self, tenant_id: str, document_id: str) -> dict:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)

        backend = (doc.storage_backend or "local").strip().lower()
        presigned = ""
        if backend == "cos":
            presigned = await get_object_storage_for("cos").presigned_url(doc.storage_key, tenant_id)
        return {
            "storage_backend": backend,
            "storage_key": doc.storage_key,
            "mime_type": doc.mime_type or "application/octet-stream",
            "file_name": doc.file_name,
            "presigned_url": presigned or "",
        }

    async def get_raw_url(self, tenant_id: str, document_id: str) -> str:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
        storage = get_object_storage()
        return await storage.presigned_url(doc.storage_key, tenant_id)

    async def get_raw_content(self, tenant_id: str, document_id: str) -> dict:

        import base64
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
        storage = get_object_storage()
        raw = await storage.get_bytes(doc.storage_key)
        return {
            "content": base64.b64encode(raw).decode("ascii"),
            "mime_type": doc.mime_type or "application/octet-stream",
            "file_name": doc.file_name,
        }

    async def list_documents(self, tenant_id: str, request: DocumentListRequest | dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = DocumentListRequest(**_payload(request))
        offset = (req.page - 1) * req.page_size

        conditions = []
        if req.status:
            conditions.append(KnowledgeDocument.status == req.status)
        if req.ontology_status:
            conditions.append(KnowledgeDocument.ontology_status == req.ontology_status)
        if req.keyword:
            pattern = f"%{req.keyword}%"
            conditions.append(
                or_(
                    KnowledgeDocument.file_name.ilike(pattern),
                    KnowledgeDocument.file_path.ilike(pattern),
                )
            )
        if req.folder_id:
            conditions.append(KnowledgeDocument.folder_id == req.folder_id)
        conditions.append(KnowledgeDocument.knowledge_base_id == req.knowledge_base_id)

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            items = await repo.list_all(
                tenant_id=tenant_id,
                offset=offset,
                limit=req.page_size,
                extra_conditions=conditions,
            )
            total = await repo.count(tenant_id=tenant_id, extra_conditions=conditions)

        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }

    async def get_document(
        self,
        tenant_id: str,
        document_id: str,
        request: DocumentScopeRequest | dict,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = DocumentScopeRequest(**_payload(request))
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != req.knowledge_base_id:
                raise ResourceNotFoundError(message="Knowledge document not found")
            return doc.to_dict()

    async def delete_document(
        self,
        tenant_id: str,
        document_id: str,
        request: DocumentScopeRequest | dict,
        *,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = DocumentScopeRequest(**_payload(request))
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != req.knowledge_base_id:
                raise ResourceNotFoundError(message="Knowledge document not found")
            if doc.status == DocStatus.DELETING.value:
                raise ResourceConflictError(message="Knowledge document is being deleted")
            if doc.status in (DocStatus.PENDING.value, DocStatus.PARSING.value):
                raise ResourceConflictError(message="Knowledge document is being parsed. Wait for parsing to complete before deleting it")
            await repo.set_status(doc, DocStatus.DELETING)
            rag_doc_ids = list(doc.rag_doc_ids or [])
            kb_id = doc.knowledge_base_id or ""
            file_name = doc.file_name or ""



        if not rag_doc_ids and file_name and kb_id:
            rag_doc_ids = await self._lookup_rag_doc_ids(
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                file_name=file_name,
                document_id=document_id,
            )

        if rag_doc_ids:
            logger.info(
                "Deleting %d LightRAG documents for doc %s: %s",
                len(rag_doc_ids), document_id, rag_doc_ids[:10],
            )
        else:
            logger.warning(
                "No LightRAG doc_ids found for document %s (file_name=%s), "
                "LightRAG cleanup will be skipped",
                document_id, file_name,
            )

        for rag_doc_id in rag_doc_ids:
            try:
                await get_rag_client().delete(
                    rag_doc_id, tenant_id=tenant_id, knowledge_base_id=kb_id
                )
            except Exception:
                logger.warning("Failed to delete RAG document %s", rag_doc_id, exc_info=True)


        try:
            gdao = OntologyGraphRepository(get_neo4j_driver())
            await gdao.delete_by_document(tenant_id, document_id)
        except Exception:
            logger.warning("Neo4j cleanup failed for document %s", document_id, exc_info=True)

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
            await repo.set_status(doc, DocStatus.DELETED)
            await repo.delete_soft(doc, tenant_id)

        schedule_emit({
            "tenant_id": tenant_id,
            "user_id": _audit_user_id(user_id),
            "username": username,
            "ip": ip,
            "log_type": "OPERATION",
            "action": "document.delete",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": "document",
            "resource_id": str(document_id),
        })

        return {"id": document_id, "deleted": True}

    async def set_document_folder(
        self, tenant_id: str, document_id: str, req: SetDocumentFolderRequest | dict
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        data = _payload(req)
        folder_id = data.get("folder_id")
        knowledge_base_id = data.get("knowledge_base_id")

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(message="Knowledge document not found")

            if folder_id:

                folder_repo = FolderRepository(session)
                folder = await folder_repo.get_required(folder_id, tenant_id)
                if folder.knowledge_base_id != knowledge_base_id:
                    raise ResourceNotFoundError(
                        message="Folder does not belong to this knowledge base",
                        details={"folder_id": folder_id, "knowledge_base_id": knowledge_base_id},
                    )

            doc.folder_id = folder_id
            await session.commit()
            return doc.to_dict()

    async def _lookup_rag_doc_ids(
        self,
        *,
        tenant_id: str,
        knowledge_base_id: str,
        file_name: str,
        document_id: str,
    ) -> list[str]:

        import re

        try:
            result = await get_rag_client().get_storage_documents(
                knowledge_base_id=knowledge_base_id,
                tenant_id=tenant_id,
                keyword=file_name,
                page=1,
                page_size=500,
            )
        except Exception as e:
            logger.warning(
                "Storage lookup failed for doc %s during delete: %s", document_id, e
            )
            return []

        items = result.get("items", [])
        total = result.get("total", len(items))
        if total > len(items):
            logger.warning(
                "Storage fallback during delete: total %d exceeds page size for doc %s",
                total, document_id,
            )

        matched = []
        for item in items:
            fp = item.get("file_path") or ""
            m = re.search(r'doc=([a-f0-9-]+)\|', fp)
            if m and m.group(1) == document_id:
                matched.append(item)
        if not matched:
            matched = [
                item for item in items
                if (
                    item.get("file_name") == file_name
                    or (item.get("file_name") or "").endswith("_" + file_name)
                )
            ]

        if not matched:
            logger.info(
                "Storage fallback miss during delete: doc_id=%s, file_name=%s, total=%d",
                document_id, file_name, len(items),
            )
            return []

        rag_doc_ids = [item["id"] for item in matched if item.get("id")]
        logger.info(
            "Storage fallback hit during delete: doc_id=%s, found %d LightRAG doc_ids",
            document_id, len(rag_doc_ids),
        )
        return rag_doc_ids


__all__ = ["DocumentService"]
