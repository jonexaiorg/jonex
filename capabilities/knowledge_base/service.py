#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Knowledge base business capability Service layer (independent container deployment version)

Refactoring key points (critical differences from Gateway embedded version):
1. __init__ No longer accepts session / rag_client, each method manages DB session internally
2. Returns dict instead of ORM object (avoids detached issue after session close)
3. RAG invocation obtained via get_rag_client() factory RemoteRAGClient(->sidecar->atomic-rag)
"""

import asyncio
import re
from typing import List, Optional

import jieba

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common import get_db_session, get_logger
from jonex_core.common.exceptions import (
    InvalidParameterError,
    ResourceNotFoundError,
    TenantIsolationError,
    UpstreamServiceError,
)

from .dao import KnowledgeDocumentDAO, KnowledgeSearchHistoryDAO
from .models import DocStatus, KnowledgeSearchHistory, OntologyStatus
from .ontology_graph_dao import OntologyGraphDAO
from jonex_core.common.neo4j_client import get_neo4j_driver

logger = get_logger("business.knowledge_base")

ONTOLOGY_ROUTE_SCORE_MIN = 1.0


def _preprocess_query(query: str) -> str:
    """jieba tokenization -> per token Lucene escaping -> OR concatenation"""
    tokens = jieba.lcut(query)
    tokens = [t.strip() for t in tokens if t.strip()]
    if not tokens:
        return query
    escaped = [re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r'\\\1', t) for t in tokens]
    return " OR ".join(escaped)


class KnowledgeBaseService:
    """Knowledge base business service (stateless, each invocation creates its own DB session)"""

    MAX_ONTOLOGY_RETRIES = 3  # Max ontology retry count, after which mark failed and no longer retry

    def __init__(self):
        # RAG client obtained via factory, adapts to LOCAL/REMOTE/MOCK mode
        self.rag = get_rag_client()
        self._reconcile_task: Optional[asyncio.Task] = None
        self._running = False

    async def upload_document(
        self,
        tenant_id: str,
        file_name: str,
        file_path: str,
        file_size: int = 0,
        mime_type: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
    ) -> dict:
        """Upload document: create business record + submit RAG parsing task"""
        if not tenant_id or tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")

        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)

            doc = await dao.create(
                tenant_id=tenant_id,
                file_name=file_name,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                extra_metadata={"knowledge_base_id": knowledge_base_id} if knowledge_base_id else None,
            )
            await session.flush()

            # Submit RAG task
            try:
                result = await self.rag.insert(
                    file_path=file_path,
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    document_id=doc.id,
                )
                await dao.update_status(
                    doc_id=doc.id,
                    tenant_id=tenant_id,
                    status=DocStatus.PARSING,
                    rag_task_id=result.get("task_id"),
                )
                await session.commit()
                logger.info(
                    f"Document submitted to RAG parsing: doc_id={doc.id}, task_id={result.get('task_id')}"
                )
            except Exception as e:
                await dao.update_status(
                    doc_id=doc.id,
                    tenant_id=tenant_id,
                    status=DocStatus.FAILED,
                    error_message=str(e),
                )
                await session.commit()
                raise UpstreamServiceError(message=f"RAG ingestion submission failed: {e}") from e

            updated = await dao.get(doc.id, tenant_id)
            return updated.to_dict()

    async def get_document(self, doc_id: str, tenant_id: str) -> dict:
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            doc = await dao.get(doc_id, tenant_id)
            if not doc:
                raise ResourceNotFoundError(
                    message=f"Document not found or no access: {doc_id}",
                    details={"doc_id": doc_id, "tenant_id": tenant_id},
                )
            return doc.to_dict()

    async def list_documents(
        self,
        tenant_id: str,
        status: Optional[DocStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[dict]:
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            docs = await dao.list_by_tenant(tenant_id, status, offset, limit)
            doc_items = [d.to_dict() for d in docs]
            parsing_doc_ids = [
                d.id
                for d in docs
                if getattr(d.status, "value", d.status) == DocStatus.PARSING.value
                and d.rag_task_id
            ]

        if not parsing_doc_ids:
            return doc_items

        for doc_id in parsing_doc_ids:
            await self.reconcile_task(doc_id=doc_id, tenant_id=tenant_id)

        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            docs = await dao.list_by_tenant(tenant_id, status, offset, limit)
            return [d.to_dict() for d in docs]

    async def query(
        self,
        tenant_id: str,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        """Search: directly forward to RAG client"""
        if not tenant_id or tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        return await self.rag.query(
            query=query,
            tenant_id=tenant_id,
            mode=mode,
            top_k=top_k,
        )

    async def query_with_ontology(
        self,
        tenant_id: str,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        kb_id: Optional[str] = None,
    ) -> dict:
        """Ontology priority -> RAG fallback routed query."""
        from jonex_core.common.ontology_llm import answer_from_facts

        ontology_instances = []
        gdao = None
        if kb_id:
            try:
                gdao = OntologyGraphDAO(get_neo4j_driver())
                processed = _preprocess_query(query)
                ontology_instances = await gdao.search_entities(
                    tenant_id=tenant_id, kb_id=kb_id, query=processed, limit=5,
                )
            except Exception as e:
                logger.warning(f"Ontology search failed, fallback to RAG: {e}")
                ontology_instances = []

        # Ontology priority path
        answer = None
        source = "rag"
        rag_used = True

        if ontology_instances and gdao is not None:
            top_score = ontology_instances[0].get("score", 0)
            if top_score >= ONTOLOGY_ROUTE_SCORE_MIN:
                try:
                    top_name = ontology_instances[0].get("name", "")
                    neighbor_data = await gdao.neighbors(
                        tenant_id, kb_id, top_name, hops=1, limit=20,
                    )
                    facts = neighbor_data.get("facts", [])
                    llm_answer = await answer_from_facts(
                        query, ontology_instances, facts,
                    )
                    if llm_answer != "INSUFFICIENT":
                        answer = llm_answer
                        source = "ontology"
                        rag_used = False
                except Exception as e:
                    logger.warning(f"Ontology Q&A failed, fallback to RAG: {e}")

        # Fallback: RAG
        if answer is None:
            answer = await self.rag.query(query, tenant_id, mode, top_k)

        return {
            "answer": answer,
            "source": source,
            "ontology_instances": ontology_instances,
            "rag_used": rag_used,
        }

    async def delete_document(self, doc_id: str, tenant_id: str) -> bool:
        """Soft delete: business layer mark DELETING -> atomic-rag delete -> DELETED"""
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            doc = await dao.get(doc_id, tenant_id)
            if not doc:
                raise ResourceNotFoundError(
                    message=f"Document not found or no access: {doc_id}",
                    details={"doc_id": doc_id, "tenant_id": tenant_id},
                )

            # Mark soft delete
            await dao.update_status(
                doc_id=doc.id,
                tenant_id=tenant_id,
                status=DocStatus.DELETING,
            )
            await session.flush()

        # Invoke atomic-rag delete (no DB session needed)
        all_success = True
        for rag_doc_id in (doc.rag_doc_ids or []):
            try:
                ok = await self.rag.delete(doc_id=rag_doc_id, tenant_id=tenant_id)
                if not ok:
                    all_success = False
            except Exception as e:
                logger.exception(f"Delete lightrag doc failed: {rag_doc_id}: {e}")
                all_success = False

        # Mark terminal state (new session)
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            status = DocStatus.DELETED if all_success else DocStatus.FAILED
            error = None if all_success else "Partial chunk deletion failed"
            await dao.update_status(
                doc_id=doc_id,
                tenant_id=tenant_id,
                status=status,
                error_message=error,
            )
            await session.commit()

        # Clean Neo4j ontology data (independent of RAG deletion result, clean even if partial failure)
        try:
            gdao = OntologyGraphDAO(get_neo4j_driver())
            await gdao.delete_by_document(tenant_id, doc_id)
            logger.info(f"Document ontology data cleaned from Neo4j: doc_id={doc_id}")
        except Exception as e:
            logger.warning(f"Neo4j ontology cleanup failed (does not affect document deletion): {e}")

        return all_success

    async def _set_ont_status(
        self, doc_id: str, tenant_id: str, status: str, error: Optional[str] = None
    ) -> None:
        """Wrap KnowledgeDocumentDAO.update_ontology_status invocation."""
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            await dao.update_ontology_status(doc_id, tenant_id, status, error)
            await session.commit()

    async def _verify_via_storage(self, doc) -> Optional[List[str]]:
        """Secondary confirmation via LightRAG storage whether document is indexed.

        When atomic-rag's task state is lost (Redis data expired or other extreme cases)
        But document actually already successfully indexed in LightRAG, as fallback verification.

        Returns:
            List[str] - rag_doc_ids list, document confirmed to exist
            None - Cannot confirm (query exception / not in storage)
        """
        kb_id = doc.extra_metadata.get("knowledge_base_id") if doc.extra_metadata else ""

        try:
            result = await self.rag.get_storage_documents(
                knowledge_base_id=kb_id,
                tenant_id=doc.tenant_id,
                keyword=doc.file_name,
                status="processed",
                page=1,
                page_size=500,
            )
        except Exception as e:
            logger.warning(f"Secondary confirmation query exception: doc_id={doc.id}, error={e}")
            return None

        items = result.get("items", [])
        total = result.get("total", len(items))
        if total > len(items):
            logger.warning(
                f"Secondary confirmation: storage total records {total} exceeds single page {len(items)}, "
                f"doc_id={doc.id}, may miss writing rag_doc_ids"
            )

        # Exact match: compatible with no prefix and <8-hex>_<original_name> two storage forms
        matched = [
            item for item in items
            if (
                item.get("file_name") == doc.file_name
                or (item.get("file_name") or "").endswith("_" + doc.file_name)
            )
            and item.get("status") == "processed"
        ]

        if not matched:
            raw_items = [
                {"file_name": i.get("file_name"), "file_path": (i.get("file_path") or "")[:120], "status": i.get("status")}
                for i in items[:5]
            ]
            logger.info(
                f"Secondary confirmation not hit: doc_id={doc.id}, file_name={doc.file_name}, "
                f"total_items={len(items)}, sample(5)={raw_items}"
            )
            return None

        rag_doc_ids = [item["id"] for item in matched if item.get("id")]
        logger.info(
            f"Secondary confirmation hit: doc_id={doc.id}, rag_doc_ids={rag_doc_ids}"
        )
        return rag_doc_ids

    async def reconcile_task(self, doc_id: str, tenant_id: str, task_id: Optional[str] = None) -> dict:
        """Async reconciliation: update local DocStatus using atomic-rag get_task_status

        atomic-rag task_id exists in memory (_tasks dict), lost after restart,
        At this point get_task_status will return status="not_found".
        This method treats "not_found" also as terminal state, prevents documents from being stuck in PARSING forever.

        Args:
            task_id: Explicitly specify task_id to query. For ontology retry scenario,
                     Document may already be in READY state, retry task_id differs from original rag_task_id.
        """
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            doc = await dao.get(doc_id, tenant_id)
            if not doc:
                raise ResourceNotFoundError(
                    message=f"Document not found or no access: {doc_id}",
                    details={"doc_id": doc_id, "tenant_id": tenant_id},
                )
            # No task_id and not PARSING status, no need to reconcile
            target_task_id = task_id or doc.rag_task_id
            if not target_task_id:
                logger.warning(
                    f"Document rag_task_id is empty, cannot reconcile: doc_id={doc_id}, "
                    f"status={getattr(doc.status, 'value', doc.status)}"
                )
                return doc.to_dict()
            if not task_id and doc.status != DocStatus.PARSING:
                return doc.to_dict()

        # Query atomic-rag (no DB session needed)
        try:
            status_info = await self.rag.get_task_status(
                task_id=target_task_id,
                tenant_id=tenant_id,
            )
        except Exception as e:
            logger.warning(f"Reconciliation query failed: doc_id={doc.id}, error={e}")
            return doc.to_dict()

        rag_status = status_info.get("status")
        update_kwargs = {}
        log_msg = ""

        if rag_status == "completed":
            update_kwargs["status"] = DocStatus.READY
            update_kwargs["rag_doc_ids"] = status_info.get("lightrag_doc_ids", [])
            log_msg = f"Reconciliation -> READY: doc_id={doc_id}, chunks={len(update_kwargs['rag_doc_ids'])}"

            # Capture ontology data, persist in session below
            ont_status = status_info.get("ontology_status", "pending")
            ont_data = status_info.get("ontology_data")
            ont_error = status_info.get("ontology_error")
            kb_id = doc.extra_metadata.get("knowledge_base_id", "") if doc.extra_metadata else ""
        elif rag_status == "failed":
            update_kwargs["status"] = DocStatus.FAILED
            update_kwargs["error_message"] = status_info.get("error", "RAG Parsing failed")
            log_msg = f"Reconciliation -> FAILED: doc_id={doc_id}, error={update_kwargs['error_message']}"
        elif rag_status == "not_found":
            # atomic-rag task state lost (Redis data expired or other extreme cases),
            # first verify via LightRAG storage whether document already successfully indexed
            rag_doc_ids = await self._verify_via_storage(doc)
            if rag_doc_ids is not None:
                update_kwargs["status"] = DocStatus.READY
                update_kwargs["rag_doc_ids"] = rag_doc_ids
                log_msg = (
                    f"Reconciliation -> READY (via storage secondary confirmation): doc_id={doc_id}, "
                    f"chunks={len(rag_doc_ids)}"
                )
            else:
                update_kwargs["status"] = DocStatus.FAILED
                update_kwargs["error_message"] = (
                    f"RAG task status lost (possibly atomic-rag container restarted), "
                    f"original task_id={doc.rag_task_id}, please delete document and re-upload"
                )
                log_msg = (
                    f"Reconciliation -> FAILED (task lost): doc_id={doc_id}, "
                    f"task_id={doc.rag_task_id}"
                )
        else:
            # processing / pending: upstream still executing, keep PARSING
            logger.debug(
                f"Reconciliation -> keep PARSING: doc_id={doc_id}, rag_status={rag_status}, "
                f"progress={status_info.get('progress')}"
            )
            return doc.to_dict()

        # -- Step 1: Neo4j ontology write (before PG, B.4 consistency design) ---
        neo4j_ok = True
        if rag_status == "completed" and ont_status == "completed" and ont_data:
            try:
                gdao = OntologyGraphDAO(get_neo4j_driver())
                for ent in ont_data.get("entities", []):
                    await gdao.merge_entity(tenant_id, kb_id, doc_id, ent)
                for rel in ont_data.get("relations", []):
                    await gdao.merge_relation(tenant_id, kb_id, doc_id, rel)
                logger.info(
                    f"Ontology persisted: doc_id={doc_id}, "
                    f"entities={len(ont_data.get('entities', []))}, "
                    f"relations={len(ont_data.get('relations', []))}"
                )
            except Exception as e:
                logger.error(f"Ontology write to Neo4j failed: doc_id={doc_id}, error={e}")
                neo4j_ok = False

        # -- Step 2: PG status update (single session, no nested lock competition) ---
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            await dao.update_status(
                doc_id=doc_id,
                tenant_id=tenant_id,
                **update_kwargs,
            )

            if rag_status == "completed":
                if ont_status == "completed" and neo4j_ok:
                    await dao.update_ontology_status(doc_id, tenant_id, "completed")
                elif ont_status == "failed":
                    await dao.update_ontology_status(
                        doc_id, tenant_id, "failed", ont_error or "Ontology extraction failed",
                    )
                elif not neo4j_ok:
                    await dao.update_ontology_status(
                        doc_id, tenant_id, "failed", "Neo4j ontology write failed",
                    )

            await session.commit()
            updated = await dao.get(doc_id, tenant_id)
            logger.info(log_msg)
            return updated.to_dict() if updated else doc.to_dict()

    async def _reconcile_ontology_pending(self) -> None:
        """Scan documents with ontology_status pending/failed and retry ontology extraction.

        Flow:
        1. Query documents with pending/failed status
        2. For each document, first check task status of existing rag_task_id
        3. If task completed and contains ontology data -> persist (means last retry succeeded)
        4. If task still executing -> skip, wait for next cycle
        5. Other cases -> trigger new retry, update rag_task_id
        """
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            pending_docs = await dao.list_by_ontology_status(
                statuses=[OntologyStatus.ON_PENDING, OntologyStatus.ON_FAILED],
                limit=50,
            )

        if not pending_docs:
            return

        logger.info(f"Ontology reconciliation: found {len(pending_docs)} documents pending retry")
        for doc in pending_docs:
            try:
                kb_id = doc.extra_metadata.get("knowledge_base_id", "") if doc.extra_metadata else ""

                # Check whether retry count has reached limit
                retry_count = doc.ontology_retry_count or 0
                if retry_count >= self.MAX_ONTOLOGY_RETRIES:
                    logger.warning(
                        f"Ontology retry count reached limit ({retry_count}/{self.MAX_ONTOLOGY_RETRIES}), "
                        f"no longer retry: doc_id={doc.id}"
                    )
                    async with get_db_session() as session:
                        ont_dao = KnowledgeDocumentDAO(session)
                        await ont_dao.update_ontology_status(
                            doc.id, doc.tenant_id, "failed",
                            f"Ontology retry count reached limit ({retry_count}/{self.MAX_ONTOLOGY_RETRIES})",
                        )
                        await session.commit()
                    continue

                # Check task status via rag_task_id (may be created by last retry)
                if doc.rag_task_id:
                    try:
                        status_info = await self.rag.get_task_status(
                            task_id=doc.rag_task_id,
                            tenant_id=doc.tenant_id,
                        )
                        rag_status = status_info.get("status", "")

                        if rag_status in ("processing", "pending"):
                            logger.debug(f"Ontology retry task still executing: doc_id={doc.id}, task_id={doc.rag_task_id}")
                            continue

                        if rag_status == "completed":
                            ont_status = status_info.get("ontology_status")
                            if ont_status == "completed" and status_info.get("ontology_data"):
                                # retry task completed and has ontology data -> persist
                                await self.reconcile_task(
                                    doc_id=doc.id, tenant_id=doc.tenant_id, task_id=doc.rag_task_id,
                                )
                                continue
                            # completed but no ontology data -> need to trigger new retry
                    except Exception as e:
                        logger.warning(f"Query task status failed, skip and wait for next cycle: doc_id={doc.id}, task_id={doc.rag_task_id}, error={e}")
                        continue

                # Trigger new ontology retry
                result = await self.rag.retry_ontology_extract(
                    document_id=doc.id,
                    knowledge_base_id=kb_id,
                    tenant_id=doc.tenant_id,
                    file_path=doc.file_path,
                )
                retry_task_id = result.get("task_id", "")
                if retry_task_id:
                    async with get_db_session() as session:
                        dao = KnowledgeDocumentDAO(session)
                        await dao.increment_ontology_retry(
                            doc_id=doc.id,
                            tenant_id=doc.tenant_id,
                        )
                        await dao.update_rag_task_id(
                            doc_id=doc.id,
                            tenant_id=doc.tenant_id,
                            rag_task_id=retry_task_id,
                        )
                        await session.commit()
                    logger.info(f"Ontology retry triggered: doc_id={doc.id}, task_id={retry_task_id}")
                else:
                    logger.warning(f"Ontology retry did not return task_id: doc_id={doc.id}")
            except Exception as e:
                logger.warning(f"Ontology retry failed: doc_id={doc.id}, error={e}")

    async def _reconcile_all_parsing(self) -> None:
        """Scan all parsing status documents and reconcile one by one (background loop invocation)"""
        async with get_db_session() as session:
            dao = KnowledgeDocumentDAO(session)
            parsing_docs = await dao.list_by_status(
                status=DocStatus.PARSING,
                offset=0,
                limit=100,
            )

        if parsing_docs:
            logger.info(f"Background reconciliation: found {len(parsing_docs)} parsing documents")
            for doc in parsing_docs:
                try:
                    await self.reconcile_task(doc_id=doc.id, tenant_id=doc.tenant_id)
                    logger.debug(f"Background reconciliation succeeded: doc_id={doc.id}")
                except Exception as e:
                    logger.warning(f"Background reconciliation failed: doc_id={doc.id}, tenant={doc.tenant_id}, error={e}")

        # Ontology reconciliation (scan documents with ontology_status=pending/failed)
        await self._reconcile_ontology_pending()

    async def _reconcile_loop(self, interval: int = 30) -> None:
        """Background reconciliation loop"""
        logger.info(f"Background reconciliation loop started, Interval={interval}s")
        while self._running:
            try:
                await self._reconcile_all_parsing()
            except Exception as e:
                logger.error(f"Background reconciliation loop exception: {e}")
            await asyncio.sleep(interval)
        logger.info("Background reconciliation loop exited")

    async def start_reconciliation(self, interval: int = 30) -> None:
        """Start background reconciliation loop"""
        if self._running:
            logger.warning("Background reconciliation loop already running")
            return
        self._running = True
        self._reconcile_task = asyncio.create_task(self._reconcile_loop(interval))

    async def stop_reconciliation(self) -> None:
        """Stop background reconciliation loop"""
        self._running = False
        if self._reconcile_task:
            self._reconcile_task.cancel()
            try:
                await self._reconcile_task
            except asyncio.CancelledError:
                pass
            self._reconcile_task = None
        logger.info("Background reconciliation loop stopped")

    # -- search overview ------------------------------------------------------

    async def get_search_overview(self, tenant_id: str, user_id: str = "anonymous") -> dict:
        """Get knowledge search homepage overview statistics (totalDocuments/totalEntities/totalRelations/todaySearches)"""
        try:
            summary = await self.rag.get_storage_summary("", tenant_id)
        except Exception as e:
            logger.warning(f"Get storage summary failed, return empty overview: {e}")
            summary = {}

        today_searches = 0
        try:
            async with get_db_session() as session:
                dao = KnowledgeSearchHistoryDAO(session)
                today_searches = await dao.count_today_by_user(tenant_id, user_id)
        except Exception as e:
            logger.warning(f"Query today search count failed: {e}")

        return {
            "totalDocuments": summary.get("documents_count", 0),
            "totalEntities": summary.get("entities_count", 0),
            "totalRelations": summary.get("relationships_count", 0),
            "todaySearches": today_searches,
            "avgResponseTimeMs": 0,
        }

    # -- search history -------------------------------------------------------

    async def list_search_history(
        self,
        tenant_id: str,
        user_id: str = "anonymous",
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        if not tenant_id or tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        if not user_id:
            user_id = "anonymous"
        limit = min(max(limit, 1), 50)

        async with get_db_session() as session:
            dao = KnowledgeSearchHistoryDAO(session)
            items = await dao.list_by_user(tenant_id, user_id, limit, offset)
            total = await dao.count_by_user(tenant_id, user_id)
            return {
                "items": [item.to_dict() for item in items],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def save_search_history(
        self,
        tenant_id: str,
        user_id: str = "anonymous",
        data: dict = None,
    ) -> dict:
        if not tenant_id or tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        if not user_id:
            user_id = "anonymous"
        if not data or not data.get("query"):
            raise InvalidParameterError(message="query cannot be empty")

        status = data.get("status") or "done"
        if status != "done":
            raise InvalidParameterError(message="Only accept save requests with status=done")

        domain_id = data.get("domain_id") or data.get("domainId") or "all"
        if not domain_id or domain_id == "all":
            data["domain_id"] = "all"

        ref_count = max(data.get("reference_count") or data.get("referenceCount") or 0, 0)
        res_count = max(data.get("result_count") or data.get("resultCount") or 0, 0)
        data["reference_count"] = ref_count
        data["result_count"] = res_count

        preview = data.get("answer_preview") or data.get("answerPreview") or ""
        if isinstance(preview, str) and len(preview) > 500:
            data["answer_preview"] = preview[:500]

        mode = data.get("mode") or "hybrid"
        top_k = data.get("top_k") or data.get("topK") or 5
        data["mode"] = mode
        data["top_k"] = top_k

        extra = data.get("extra_metadata") or data.get("extraMetadata") or {}
        if not isinstance(extra, dict):
            extra = {}
        data["extra_metadata"] = extra

        async with get_db_session() as session:
            dao = KnowledgeSearchHistoryDAO(session)
            item = await dao.upsert_history(tenant_id, user_id, data)
            await dao.prune_by_user(tenant_id, user_id, keep=20)
            result = item.to_dict()
            await session.commit()
            return {"item": result}

    async def delete_search_history(
        self,
        tenant_id: str,
        user_id: str = "anonymous",
        history_id: str = "",
    ) -> dict:
        if not tenant_id or tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        if not user_id:
            user_id = "anonymous"
        if not history_id:
            raise InvalidParameterError(message="history_id cannot be empty")

        async with get_db_session() as session:
            dao = KnowledgeSearchHistoryDAO(session)
            await dao.delete_one(tenant_id, user_id, history_id)
            await session.commit()
            return {"deleted": True}

    async def clear_search_history(
        self,
        tenant_id: str,
        user_id: str = "anonymous",
    ) -> dict:
        if not tenant_id or tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        if not user_id:
            user_id = "anonymous"

        async with get_db_session() as session:
            dao = KnowledgeSearchHistoryDAO(session)
            count = await dao.clear_by_user(tenant_id, user_id)
            await session.commit()
            return {"deletedCount": count}

    # -- parse result (LightRAG storage reader) -------------------------------

    async def _build_parse_scope(self, knowledge_base_id: str, tenant_id: str) -> dict:
        """Query documents in DB belonging to this knowledge base, build file_path/file_name scope"""
        scope: dict = {
            "knowledge_base_id": knowledge_base_id,
            "tenant_id": tenant_id,
            "scope_mode": "knowledge_base",
            "file_paths": [],
            "file_names": [],
        }
        try:
            async with get_db_session() as session:
                dao = KnowledgeDocumentDAO(session)
                docs = await dao.list_by_knowledge_base(knowledge_base_id, tenant_id)
                for d in docs:
                    if d.file_path:
                        scope["file_paths"].append(d.file_path)
                    if d.file_name:
                        scope["file_names"].append(d.file_name)
        except Exception as e:
            logger.warning(f"Build parse scope failed (DB query exception): {e}")
            scope["scope_warning"] = f"DB query exception: {e}"

        if not scope["file_paths"] and not scope["file_names"]:
            scope["scope_warning"] = (
                "No indexed documents found for this knowledge base, will return global storage data"
            )

        return scope

    async def get_parse_result_summary(self, knowledge_base_id: str, tenant_id: str) -> dict:
        scope = await self._build_parse_scope(knowledge_base_id, tenant_id)
        return await self.rag.get_storage_summary(knowledge_base_id, tenant_id)

    async def get_parse_result_documents(
        self, knowledge_base_id: str, tenant_id: str,
        page: int = 1, page_size: int = 20,
        keyword: Optional[str] = None, status: Optional[str] = None,
    ) -> dict:
        return await self.rag.get_storage_documents(
            knowledge_base_id, tenant_id,
            page=page, page_size=page_size, keyword=keyword, status=status,
        )

    async def get_parse_result_entities(
        self, knowledge_base_id: str, tenant_id: str,
        page: int = 1, page_size: int = 20,
        keyword: Optional[str] = None, entity_type: Optional[str] = None,
        file_path: Optional[str] = None, document_id: Optional[str] = None,
    ) -> dict:
        storage_result = await self.rag.get_storage_entities(
            knowledge_base_id, tenant_id,
            page=page, page_size=page_size, keyword=keyword,
            entity_type=entity_type, file_path=file_path, document_id=document_id,
        )

        # Read typed data from ontology store, override entity_type (match by canonical_name)
        try:
            items = storage_result.get("items", [])
            if items:
                names = list(set(
                    item.get("name") or item.get("entity_name") or ""
                    for item in items
                ))
                names = [n for n in names if n]
                if names:
                    gdao = OntologyGraphDAO(get_neo4j_driver())
                    type_map = await gdao.list_entity_types(tenant_id, knowledge_base_id, names)
                    if type_map:
                        for item in items:
                            cn = item.get("name") or item.get("entity_name") or ""
                            if cn in type_map:
                                item["entity_type"] = type_map[cn]
                                item["ontology_typed"] = True
        except Exception as e:
            logger.warning(f"Ontology store query exception, skip type override: {e}")

        return storage_result

    async def get_parse_result_relationships(
        self, knowledge_base_id: str, tenant_id: str,
        page: int = 1, page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None, document_id: Optional[str] = None,
        source_entity: Optional[str] = None, target_entity: Optional[str] = None,
    ) -> dict:
        storage_result = await self.rag.get_storage_relationships(
            knowledge_base_id, tenant_id,
            page=page, page_size=page_size, keyword=keyword,
            file_path=file_path, document_id=document_id,
            source_entity=source_entity, target_entity=target_entity,
        )

        # Read typed entities from ontology store, override source/target entity type in relations
        try:
            items = storage_result.get("items", [])
            if items:
                names = list(set(
                    item.get("source_name") or ""
                    for item in items
                ) | set(
                    item.get("target_name") or ""
                    for item in items
                ))
                names = [n for n in names if n]
                if names:
                    gdao = OntologyGraphDAO(get_neo4j_driver())
                    type_map = await gdao.list_entity_types(tenant_id, knowledge_base_id, names)
                    if type_map:
                        for item in items:
                            src = item.get("source_name") or ""
                            tgt = item.get("target_name") or ""
                            if src in type_map:
                                item["source_entity_type"] = type_map[src]
                            if tgt in type_map:
                                item["target_entity_type"] = type_map[tgt]
                            if src in type_map or tgt in type_map:
                                item["ontology_typed"] = True
        except Exception as e:
            logger.warning(f"Ontology store relation override exception: {e}")

        return storage_result

    async def get_parse_result_graph_summary(self, knowledge_base_id: str, tenant_id: str) -> dict:
        return await self.rag.get_storage_graph_summary(knowledge_base_id, tenant_id)

    async def get_parse_result_graph(
        self, knowledge_base_id: str, tenant_id: str,
        limit: int = 200, keyword: Optional[str] = None,
        file_path: Optional[str] = None, document_id: Optional[str] = None,
    ) -> dict:
        return await self.rag.get_storage_graph(
            knowledge_base_id, tenant_id,
            limit=limit, keyword=keyword, file_path=file_path, document_id=document_id,
        )

    async def get_document_parse_result(self, knowledge_base_id: str, tenant_id: str) -> dict:
        return await self.rag.get_document_parse_result(knowledge_base_id, tenant_id)
