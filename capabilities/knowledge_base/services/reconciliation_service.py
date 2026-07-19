

import logging
import time
from datetime import datetime

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.audit import schedule_emit
from jonex_core.common.database import get_db_session
from jonex_core.common.neo4j_client import get_neo4j_driver

from ..models import DocStatus, OntologyStatus
from ..repository import KnowledgeDocumentRepository, OntologyGraphRepository

logger = logging.getLogger(__name__)

MAX_ONTOLOGY_RETRIES = 3


class ReconciliationService:




    async def reconcile_documents(self, limit: int = 50) -> dict:

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            docs = await repo.list_by_status_for_reconciliation(DocStatus.PARSING, limit=limit)

        updated, failed, skipped = 0, 0, 0
        for doc in docs:
            try:
                result = await self._reconcile_one(doc)
                if result == "updated":
                    updated += 1
                elif result == "skipped":
                    skipped += 1
            except Exception:
                failed += 1
                logger.warning("Failed to reconcile document %s", doc.id, exc_info=True)

        return {"checked": len(docs), "updated": updated, "skipped": skipped, "failed": failed}

    async def reconcile_ontology(self, limit: int = 50) -> dict:

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            docs = await repo.list_by_ontology_status_for_reconciliation(
                [OntologyStatus.PENDING, OntologyStatus.FAILED, OntologyStatus.EXTRACTING],
                limit=limit,
            )

        queued = 0
        for doc in docs:
            try:
                if await self._retry_ontology_one(doc):
                    queued += 1
            except Exception:
                logger.warning("Ontology retry failed for doc %s", doc.id, exc_info=True)

        return {"checked": len(docs), "queued": queued}



    async def _reconcile_one(self, doc) -> str:

        if not doc.rag_task_id:
            return await self._handle_not_found(doc)

        try:
            status_info = await get_rag_client().get_task_status(
                task_id=doc.rag_task_id,
                tenant_id=doc.tenant_id,
            )
        except Exception as e:
            logger.warning("Reconcile query failed for doc %s: %s", doc.id, e)
            return "skipped"

        rag_status = status_info.get("status") or status_info.get("state", "")

        if rag_status == "completed":
            return await self._handle_completed(doc, status_info)
        elif rag_status == "failed":
            return await self._handle_failed(doc, status_info)
        elif rag_status == "not_found":
            return await self._handle_not_found(doc)
        else:

            logger.debug(
                "Reconcile→keep PARSING: doc_id=%s, rag_status=%s, progress=%s",
                doc.id, rag_status, status_info.get("progress"),
            )
            return "skipped"

    async def _handle_completed(self, doc, status_info: dict, reconcile_source: str = "first") -> str:

        ont_status = status_info.get("ontology_status", "pending")
        ont_data = status_info.get("ontology_data")
        ont_error = status_info.get("ontology_error")
        kb_id = (doc.knowledge_base_id or (doc.extra_metadata or {}).get("knowledge_base_id", ""))

        worker_timings = status_info.get("stage_timings") or {}
        worker_total_ms = worker_timings.get("worker_total_ms")


        neo4j_ok = True
        neo4j_write_ms = None
        if ont_status == "completed" and ont_data:
            _t_neo4j = time.perf_counter()
            try:
                gdao = OntologyGraphRepository(get_neo4j_driver())



                await gdao.delete_by_document(doc.tenant_id, doc.id)

                gdao.reset_endpoint_cache()

                hash_cache = await gdao.get_embedding_hashes(doc.tenant_id, kb_id)
                for ent in ont_data.get("entities", []):
                    await gdao.merge_entity(doc.tenant_id, kb_id, doc.id, ent, hash_cache=hash_cache)
                for rel in ont_data.get("relations", []):
                    await gdao.merge_relation(doc.tenant_id, kb_id, doc.id, rel)
                neo4j_write_ms = int((time.perf_counter() - _t_neo4j) * 1000)
                logger.info(
                    "Ontology written: doc_id=%s, entities=%d, relations=%d",
                    doc.id,
                    len(ont_data.get("entities", [])),
                    len(ont_data.get("relations", [])),
                )
            except Exception as e:
                neo4j_write_ms = int((time.perf_counter() - _t_neo4j) * 1000)
                logger.error("Neo4j ontology write failed for doc %s: %s", doc.id, e)
                neo4j_ok = False


        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            await repo.set_status(
                doc,
                DocStatus.READY,
                rag_doc_ids=status_info.get("lightrag_doc_ids") or status_info.get("doc_ids") or [],
            )

            if ont_status == "completed" and neo4j_ok:
                await repo.set_ontology_status(doc, OntologyStatus.READY)
            elif ont_status == "failed":
                await repo.set_ontology_status(doc, OntologyStatus.FAILED, error=ont_error or "本体抽取失败")
            elif not neo4j_ok:
                await repo.set_ontology_status(doc, OntologyStatus.FAILED, error="Neo4j 本体写入失败")

            await session.commit()



        e2e_ready_ms = None
        if doc.created_at is not None:
            e2e_ready_ms = int((datetime.utcnow() - doc.created_at).total_seconds() * 1000)

        logger.info("Reconcile→READY: doc_id=%s, chunks=%d", doc.id,
                     len(status_info.get("lightrag_doc_ids") or status_info.get("doc_ids") or []))
        logger.info(
            "reconcile_timing doc_id=%s source=%s neo4j_write_ms=%s e2e_ready_ms=%s worker_total_ms=%s",
            doc.id,
            reconcile_source,
            neo4j_write_ms,
            e2e_ready_ms,
            worker_total_ms,
            extra={
                "event": "reconcile_timing",
                "tenant_id": doc.tenant_id,
                "knowledge_base_id": kb_id,
                "document_id": str(doc.id),
                "status": "ready",
                "reconcile_source": reconcile_source,
                "neo4j_write_ms": neo4j_write_ms,
                "e2e_ready_ms": e2e_ready_ms,
                "worker_total_ms": worker_total_ms,
                **{k: v for k, v in worker_timings.items() if k != "worker_total_ms"},
            },
        )
        schedule_emit({
            "tenant_id": doc.tenant_id,
            "log_type": "TASK",
            "action": "document.parse_done",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": "document",
            "resource_id": str(doc.id),
            "duration_ms": worker_total_ms,
            "request_params": {
                "reconcile_source": reconcile_source,
                "neo4j_write_ms": neo4j_write_ms,
                "e2e_ready_ms": e2e_ready_ms,
            },
        })
        return "updated"

    async def _handle_failed(self, doc, status_info: dict) -> str:


        rag_doc_ids = await self._verify_via_storage(doc)
        if rag_doc_ids:
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                await repo.set_status(doc, DocStatus.READY, rag_doc_ids=rag_doc_ids)
                await session.commit()
            logger.info("Reconcile→READY(via failed-task storage fallback): doc_id=%s", doc.id)
            return "updated"

        error_msg = status_info.get("error") or status_info.get("message") or "RAG 解析失败"
        worker_total_ms = (status_info.get("stage_timings") or {}).get("worker_total_ms")
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            await repo.set_status(doc, DocStatus.FAILED, error_message=error_msg)
            await session.commit()
        logger.info("Reconcile->FAILED: doc_id=%s, error=%s", doc.id, error_msg)
        schedule_emit({
            "tenant_id": doc.tenant_id,
            "log_type": "TASK",
            "action": "document.parse_failed",
            "outcome": "FAILED",
            "service_name": "knowledge_base",
            "resource": "document",
            "resource_id": str(doc.id),
            "error_message": error_msg[:1000],
            "duration_ms": worker_total_ms,
        })
        return "updated"

    async def _handle_not_found(self, doc) -> str:

        _t_fallback = time.perf_counter()
        rag_doc_ids = await self._verify_via_storage(doc)
        storage_fallback_ms = int((time.perf_counter() - _t_fallback) * 1000)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            if rag_doc_ids is not None:
                await repo.set_status(doc, DocStatus.READY, rag_doc_ids=rag_doc_ids)
                await session.commit()
                logger.info(
                    "Reconcile→READY(via storage fallback): doc_id=%s, chunks=%d",
                    doc.id, len(rag_doc_ids),
                )
                schedule_emit({
                    "tenant_id": doc.tenant_id,
                    "log_type": "TASK",
                    "action": "document.parse_recover",
                    "outcome": "SUCCESS",
                    "service_name": "knowledge_base",
                    "resource": "document",
                    "resource_id": str(doc.id),
                    "duration_ms": storage_fallback_ms,
                })
            else:
                err = (
                    f"RAG 任务状态丢失（可能 atomic-rag 容器已重启），"
                    f"原 task_id={doc.rag_task_id}，请删除文档后重新上传"
                )
                await repo.set_status(doc, DocStatus.FAILED, error_message=err)
                await session.commit()
                logger.info("Reconcile→FAILED(task lost): doc_id=%s, task_id=%s", doc.id, doc.rag_task_id)
                schedule_emit({
                    "tenant_id": doc.tenant_id,
                    "log_type": "TASK",
                    "action": "document.parse_recover",
                    "outcome": "FAILED",
                    "service_name": "knowledge_base",
                    "resource": "document",
                    "resource_id": str(doc.id),
                    "error_message": err[:1000],
                    "duration_ms": storage_fallback_ms,
                })
        return "updated"



    async def _retry_ontology_one(self, doc) -> bool:

        kb_id = (doc.knowledge_base_id or (doc.extra_metadata or {}).get("knowledge_base_id", ""))


        try:
            from .ontology_compiler import OntologyCompiler
            schema = await OntologyCompiler().get_compiled_schema(doc.tenant_id, kb_id, auto_compile=True)
            if schema is None:
                logger.warning(
                    "Ontology retry skipped - no compiled schema for doc %s (KB %s)",
                    doc.id, kb_id,
                )
                return False
        except Exception as e:
            logger.warning("Compiled schema check failed for doc %s, proceeding anyway: %s", doc.id, e)


        retry_count = doc.ontology_retry_count or 0
        if retry_count >= MAX_ONTOLOGY_RETRIES:
            logger.warning(
                "Ontology retry limit reached (%d/%d) for doc %s, marking failed",
                retry_count, MAX_ONTOLOGY_RETRIES, doc.id,
            )
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                await repo.set_ontology_status(
                    doc, OntologyStatus.FAILED,
                    error=f"本体重试次数已达上限 ({retry_count}/{MAX_ONTOLOGY_RETRIES})",
                )
                await session.commit()
            return False









        if doc.ontology_status == OntologyStatus.EXTRACTING.value and doc.rag_task_id:
            try:
                status_info = await get_rag_client().get_task_status(
                    task_id=doc.rag_task_id,
                    tenant_id=doc.tenant_id,
                )
                rag_status = status_info.get("status") or status_info.get("state", "")
                if rag_status in ("processing", "pending"):
                    logger.debug("Ontology retry task still running: doc_id=%s, task_id=%s", doc.id, doc.rag_task_id)
                    return False
                if rag_status == "completed":
                    ont_status = status_info.get("ontology_status")
                    if ont_status == "completed" and status_info.get("ontology_data"):

                        await self._handle_completed(doc, status_info, reconcile_source="ontology_retry")
                        return True

                    ont_error = status_info.get("ontology_error") or status_info.get("error") or "无候选实体"
                    if retry_count + 1 >= MAX_ONTOLOGY_RETRIES:
                        async with get_db_session() as session:
                            repo = KnowledgeDocumentRepository(session)
                            await repo.set_ontology_status(doc, OntologyStatus.FAILED, error=ont_error)
                            await session.commit()
                        logger.warning("Ontology retry exhausted for doc %s: %s", doc.id, ont_error)
                        return False

            except Exception as e:
                logger.warning("Task status query failed for doc %s, skipping: %s", doc.id, e)
                return False


        try:
            result = await get_rag_client().retry_ontology_extract(
                document_id=doc.id,
                knowledge_base_id=kb_id,
                tenant_id=doc.tenant_id,
                file_path=doc.file_path,
            )
        except Exception as e:
            logger.warning("Retry ontology extract failed for doc %s: %s", doc.id, e)
            return False

        if not result:
            logger.warning("Retry ontology extract returned empty for doc %s (kb_id may be missing)", doc.id)
            return False

        retry_task_id = result.get("task_id", "")
        if not retry_task_id:
            logger.warning("Retry ontology did not return task_id for doc %s", doc.id)
            return False

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            await repo.set_ontology_status(doc, OntologyStatus.EXTRACTING, increment_retry=True)
            await repo.set_status(doc, doc.status, rag_task_id=retry_task_id)
            await session.commit()

        logger.info("Ontology retry queued: doc_id=%s, new_task_id=%s", doc.id, retry_task_id)
        return True



    async def _verify_via_storage(self, doc) -> list[str] | None:

        import re

        kb_id = (doc.knowledge_base_id or (doc.extra_metadata or {}).get("knowledge_base_id", ""))

        try:
            result = await get_rag_client().get_storage_documents(
                knowledge_base_id=kb_id,
                tenant_id=doc.tenant_id,
                keyword=doc.file_name,
                page=1,
                page_size=500,
            )
        except Exception as e:
            logger.warning("Storage lookup failed for doc %s: %s", doc.id, e)
            return None

        items = result.get("items", [])
        total = result.get("total", len(items))
        if total > len(items):
            logger.warning(
                "Storage fallback: total %d exceeds page size for doc %s, may miss rag_doc_ids",
                total, doc.id,
            )



        matched = []
        for item in items:
            fp = item.get("file_path") or ""
            m = re.search(r'doc=([a-f0-9-]+)\|', fp)
            if m and m.group(1) == doc.id:
                matched.append(item)
        if not matched:

            matched = [
                item for item in items
                if (
                    item.get("file_name") == doc.file_name
                    or (item.get("file_name") or "").endswith("_" + doc.file_name)
                )
            ]

        if not matched:
            raw_items = [
                {
                    "file_name": i.get("file_name"),
                    "file_path": (i.get("file_path") or "")[:120],
                    "status": i.get("status"),
                }
                for i in items[:5]
            ]
            logger.info(
                "Storage fallback miss: doc_id=%s, file_name=%s, total=%d, sample(5)=%s",
                doc.id, doc.file_name, len(items), raw_items,
            )
            return None

        rag_doc_ids = [item["id"] for item in matched if item.get("id")]
        logger.info("Storage fallback hit: doc_id=%s, rag_doc_ids=%s", doc.id, rag_doc_ids)
        return rag_doc_ids


__all__ = ["ReconciliationService"]
