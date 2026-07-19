

import asyncio
import hashlib
import logging
import os
import re
import time
from typing import Any

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import InvalidParameterError, ResourceNotFoundError
from jonex_core.common.file_source_util import classify_media, to_location
from jonex_core.common.neo4j_client import get_neo4j_driver
from jonex_core.common.object_storage import get_object_storage
from jonex_core.common.ontology_embedding import embed
from jonex_core.common.ontology_llm import answer_from_facts, fuse_rag_answers
from jonex_core.common.tenant import require_tenant

from ..dtos import OntologySearchRequest, SearchHistoryCreateRequest, SearchRequest
from ..dtos.reasoning import (
    STAGE_FACT_LOOKUP,
    STAGE_FUSION,
    STAGE_LLM_ANSWER,
    STAGE_ONTOLOGY_MATCH,
    STAGE_RAG_FALLBACK,
    STAGE_RERANK,
    STAGE_RETRIEVAL_RERANK,
    STAGE_ROUTE_DECISION,
)
from ..repository import OntologyGraphRepository
from ..repository.document_repository import KnowledgeDocumentRepository
from ..repository.knowledge_info_repository import KnowledgeInfoRepository
from .document_service import _payload
from .reasoning_trace import ReasoningCollector
from .search_history_service import SearchHistoryService

logger = logging.getLogger(__name__)

ONTOLOGY_ROUTE_SCORE_MIN = float(os.getenv("ONTOLOGY_ROUTE_SCORE_MIN", "1.0"))
ONTOLOGY_VECTOR_SCORE_MIN = float(os.getenv("ONTOLOGY_VECTOR_SCORE_MIN", "0.75"))
_ONTOLOGY_VECTOR_ENABLED = os.getenv("ONTOLOGY_VECTOR_ENABLED", "true").lower() in ("1", "true", "yes", "on")


_RRF_K = int(os.getenv("ONTOLOGY_RRF_K", "60"))
_RRF_W_FT = float(os.getenv("ONTOLOGY_RRF_W_FT", "1.0"))
_RRF_W_VEC = float(os.getenv("ONTOLOGY_RRF_W_VEC", "1.0"))



RAG_MIN_QUERY_LEN = max(3, int(os.getenv("RAG_MIN_QUERY_LEN", "3")))


MAX_KB_PER_QUERY = 20


RAG_FALLBACK_MAX_REFS = max(1, int(os.getenv("ONTOLOGY_RAG_FALLBACK_MAX_REFS", "5")))



RAG_FALLBACK_RERANK_ENABLED = os.getenv(
    "ONTOLOGY_RAG_FALLBACK_RERANK_ENABLED", "false"
).lower() in ("1", "true", "yes", "on")




RAG_RETRIEVAL_RERANK_ENABLED = os.getenv(
    "RAG_RETRIEVAL_RERANK_ENABLED", "false"
).lower() in ("1", "true", "yes", "on")


_REASONING_ENABLED = os.getenv("REASONING_TRACE_ENABLED", "true").lower() in ("1", "true", "yes")


_query_embedding_cache: dict[str, tuple[float, list[float]]] = {}
_QUERY_EMBED_CACHE_TTL = int(os.getenv("ONTOLOGY_QUERY_EMBED_TTL", "300"))
_QUERY_EMBED_CACHE_MAX = int(os.getenv("ONTOLOGY_QUERY_EMBED_CACHE_MAX", "500"))




_ONTOLOGY_EMBED_TIMEOUT = float(os.getenv("ONTOLOGY_EMBED_TIMEOUT", "5"))


def _evict_stale_entries() -> None:

    now = time.time()
    stale = [k for k, v in _query_embedding_cache.items() if now - v[0] >= _QUERY_EMBED_CACHE_TTL]
    for k in stale:
        del _query_embedding_cache[k]
    over = len(_query_embedding_cache) - _QUERY_EMBED_CACHE_MAX
    if over > 0:
        oldest = sorted(_query_embedding_cache.items(), key=lambda x: x[1][0])[:over]
        for k, _ in oldest:
            del _query_embedding_cache[k]


async def _embed_query_cached(query: str, tenant_id: str) -> list[float] | None:
    key = hashlib.sha256(query.encode("utf-8")).hexdigest()
    now = time.time()
    hit = _query_embedding_cache.get(key)
    if hit and now - hit[0] < _QUERY_EMBED_CACHE_TTL:
        return hit[1]
    vec = await embed(query, tenant_id=tenant_id)
    if vec is not None:
        _query_embedding_cache[key] = (now, vec)
        if len(_query_embedding_cache) > _QUERY_EMBED_CACHE_MAX * 1.2:
            _evict_stale_entries()
    return vec


def _fuse_hits(fulltext_hits: list[dict], vector_hits: list[dict]) -> list[dict]:

    merged: dict[tuple, dict] = {}

    for rank_idx, hit in enumerate(fulltext_hits):
        key = (hit.get("type", ""), hit.get("name", ""), hit.get("kb_id", ""))
        rrf = _RRF_W_FT / (_RRF_K + rank_idx + 1)
        merged[key] = {**hit, "fused_score": rrf, "ft_score": hit.get("score", 0), "vscore": 0.0}

    for rank_idx, hit in enumerate(vector_hits):
        key = (hit.get("type", ""), hit.get("name", ""), hit.get("kb_id", ""))
        rrf = _RRF_W_VEC / (_RRF_K + rank_idx + 1)
        vscore = hit.get("vscore", hit.get("score", 0))
        if key in merged:
            merged[key]["fused_score"] = merged[key]["fused_score"] + rrf
            merged[key]["vscore"] = vscore
        else:
            merged[key] = {**hit, "fused_score": rrf, "ft_score": 0.0, "vscore": vscore}

    fused = sorted(merged.values(), key=lambda x: x.get("fused_score", 0), reverse=True)
    return fused


def _preprocess_query(query: str) -> str:

    if not query.strip():
        return query
    return re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r'\\\1', query)


class SearchService:
    def __init__(self):
        self._history = SearchHistoryService()

    async def search(self, tenant_id: str, user_id: str, request: SearchRequest | dict, trace_id: str = "") -> dict:
        tenant_id = require_tenant(tenant_id)
        req = SearchRequest(**_payload(request))
        start = time.perf_counter()
        detailed = await get_rag_client().query_detailed(
            query=req.query,
            tenant_id=tenant_id,
            mode=req.mode,
            top_k=req.top_k,
            knowledge_base_id=req.knowledge_base_id,
            trace_id=trace_id,
        )
        answer = detailed.get("answer", "")
        raw_refs = detailed.get("references", [])
        duration_ms = int((time.perf_counter() - start) * 1000)
        references = await self._build_references(
            tenant_id, raw_refs, allowed_kb_ids=[req.knowledge_base_id],
        )
        result = {
            "query": req.query,
            "answer": answer,
            "mode": req.mode,
            "top_k": req.top_k,
            "references": references,
            "metadata": {
                "knowledge_base_id": req.knowledge_base_id,
                "duration_ms": duration_ms,
            },
        }
        if req.save_history:
            await self._history.save_history(
                tenant_id,
                user_id,
                SearchHistoryCreateRequest(
                    query=req.query,
                    knowledge_base_id=req.knowledge_base_id,
                    mode=req.mode,
                    top_k=req.top_k,
                    answer_preview=answer[:300],
                    duration_ms=duration_ms,
                ),
            )
        return result

    async def enhanced_search(
        self,
        tenant_id: str,
        user_id: str,
        request: SearchRequest | dict,
        trace_id: str = "",
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = SearchRequest(**_payload(request))
        base = await self.search(tenant_id, user_id, req, trace_id=trace_id)
        rag = get_rag_client()
        graph = await rag.get_storage_graph(
            knowledge_base_id=req.knowledge_base_id,
            tenant_id=tenant_id,
            limit=100,
            keyword=req.query,
        )
        entities = graph.get("entities") or graph.get("nodes") or []
        relationships = graph.get("relationships") or graph.get("edges") or []
        return {
            **base,
            "entities": entities,
            "relationships": relationships,
            "graph": graph,
        }

    async def _resolve_kb_ids(self, tenant_id: str, req: OntologySearchRequest) -> list[str]:

        kb_ids = list(dict.fromkeys(k.strip() for k in req.knowledge_base_ids if k and k.strip()))
        if not kb_ids:
            raise InvalidParameterError(message="Specify at least one knowledge base (knowledge_base_ids must not be empty)")
        if len(kb_ids) > MAX_KB_PER_QUERY:
            raise InvalidParameterError(
                message=f"A single query supports at most {MAX_KB_PER_QUERY} knowledge bases; received {len(kb_ids)}. Reduce the number and try again"
            )
        await self._assert_kb_ownership(tenant_id, kb_ids)
        return kb_ids

    async def _assert_kb_ownership(self, tenant_id: str, kb_ids: list[str]) -> None:

        async with get_db_session() as session:
            repo = KnowledgeInfoRepository(session)
            for kb_id in kb_ids:
                kb = await repo.get_by_id(kb_id, tenant_id)
                if kb is None:
                    raise ResourceNotFoundError(
                        message=f"Knowledge base {kb_id} does not exist or does not belong to the current tenant"
                    )

    async def _build_references(
        self, tenant_id: str, raw_refs: list[dict],
        allowed_kb_ids: list[str] | None = None,
    ) -> list[dict]:

        doc_ids = [r["doc_id"] for r in raw_refs if r.get("doc_id")]
        if not doc_ids:
            return []

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            docs = await repo.get_by_ids(doc_ids, tenant_id)
        doc_map = {d.id: d for d in docs}
        if allowed_kb_ids is not None:
            allowed = set(allowed_kb_ids)
            cross_kb = {
                did for did, d in doc_map.items()
                if d.knowledge_base_id not in allowed
            }
            if cross_kb:
                logger.warning(
                    "references enrichment: %d doc_id values associated with out-of-scope KBs were filtered out (cross-KB safeguard): %s",
                    len(cross_kb), list(cross_kb)[:10],
                )
            doc_map = {
                did: d for did, d in doc_map.items()
                if d.knowledge_base_id in allowed
            }
        filtered = len(set(doc_ids)) - len(doc_map)
        if filtered:
            logger.info(
                "references enrichment: %d input refs, %d doc_id values filtered out (unauthorized/nonexistent/outside selected KBs)",
                len(doc_ids), filtered,
            )

        agg: dict[str, dict] = {}
        for r in raw_refs:
            did = r.get("doc_id")
            if not did or did not in doc_map:
                continue
            ref = agg.setdefault(did, {"doc_id": did, "locations": []})
            ref["locations"].append(to_location(r))

        storage = get_object_storage()
        out = []
        for did, ref in agg.items():
            d = doc_map[did]
            raw_url = None
            if d.storage_key:
                try:
                    raw_url = await storage.presigned_url(d.storage_key, tenant_id)
                except Exception:
                    pass
            out.append({
                "doc_id": did,
                "kb_id": d.knowledge_base_id,
                "file_name": d.file_name,
                "mime_type": d.mime_type,
                "file_size": d.file_size,
                "media_type": classify_media(d.mime_type, d.file_name),
                "raw_url": raw_url,
                "locations": ref["locations"],
            })
        return out

    async def _build_references_by_doc_ids(
        self, tenant_id: str, doc_ids: list[str],
        allowed_kb_ids: list[str] | None = None,
    ) -> list[dict]:

        deduped = list(dict.fromkeys(d for d in doc_ids if d))
        if not deduped:
            return []
        async with get_db_session() as session:
            docs = await KnowledgeDocumentRepository(session).get_by_ids(deduped, tenant_id)

        if allowed_kb_ids is not None:
            allowed = set(allowed_kb_ids)
            docs = [d for d in docs if d.knowledge_base_id in allowed]

        storage = get_object_storage()
        out = []
        for d in docs:
            raw_url = None
            if d.storage_key:
                try:
                    raw_url = await storage.presigned_url(d.storage_key, tenant_id)
                except Exception:
                    pass
            out.append({
                "doc_id": d.id,
                "kb_id": d.knowledge_base_id,
                "file_name": d.file_name,
                "mime_type": d.mime_type,
                "file_size": d.file_size,
                "media_type": classify_media(d.mime_type, d.file_name),
                "raw_url": raw_url,
                "locations": [{"type": "document"}],
            })
        return out

    async def resolve_references(
        self, tenant_id: str, doc_ids: list[str] | None = None, refs: list[dict] | None = None,
    ) -> list[dict]:

        if refs:
            return await self._build_references(tenant_id, refs)
        if doc_ids:
            return await self._build_references_by_doc_ids(tenant_id, doc_ids)
        return []

    async def _match_ontology(
        self, gdao: OntologyGraphRepository, tenant_id: str, kb_ids: list[str], query: str,
    ) -> list[dict]:

        instances: list[dict] = []


        exact = await gdao.exact_match_entities(tenant_id, kb_ids, query)
        if exact:
            for r in exact:
                r["source"] = "exact"
            instances = exact
            logger.info(
                "[ontology] Match found stage=exact query=%r kb_ids=%s hits=%d",
                query, kb_ids, len(exact),
            )
            return instances


        prefix = await gdao.prefix_match_entities(tenant_id, kb_ids, query, limit=3)
        if prefix:
            for r in prefix:
                r["source"] = "prefix"
            instances = prefix
            logger.info(
                "[ontology] Match found stage=prefix query=%r kb_ids=%s hits=%d names=%s",
                query, kb_ids, len(prefix), [r.get("name") for r in prefix],
            )
            return instances


        processed = _preprocess_query(query)

        async def _ft():
            return await gdao.search_entities(tenant_id, kb_ids, processed, limit=10)

        async def _vec():
            if not _ONTOLOGY_VECTOR_ENABLED:
                return []
            try:
                qvec = await asyncio.wait_for(
                    _embed_query_cached(query, tenant_id),
                    timeout=_ONTOLOGY_EMBED_TIMEOUT,
                )
                if qvec is None:
                    return []
                return await gdao.vector_search_entities(tenant_id, kb_ids, qvec, limit=10)
            except asyncio.TimeoutError:
                logger.warning(
                    "[ontology] Vector retrieval embedding timed out (%.1fs); using full-text only query=%r",
                    _ONTOLOGY_EMBED_TIMEOUT, query,
                )
                return []
            except Exception as e:
                logger.warning("[ontology] Vector retrieval failed; using full-text only: %s", e)
                return []

        fulltext_hits, vector_hits = await asyncio.gather(_ft(), _vec())


        instances = _fuse_hits(fulltext_hits, vector_hits)

        if instances:
            logger.info(
                "[ontology] Match stage=hybrid query=%r kb_ids=%s hits=%d "
                "ft_hits=%d vec_hits=%d top_fused=%.4f top_vscore=%.4f top_ftscore=%s",
                query, kb_ids, len(instances), len(fulltext_hits), len(vector_hits),
                instances[0].get("fused_score", 0),
                instances[0].get("vscore", 0),
                instances[0].get("ft_score", 0),
            )
        else:
            logger.info(
                "[ontology] No matches across all four stages (exact/prefix/fulltext/vector) query=%r kb_ids=%s",
                query, kb_ids,
            )
        return instances

    def _log_rag_timing(
        self, tenant_id: str, rag_multi_ms: int | None, fusion_ms: int | None,
        kb_ok: int, kb_total: int, kb_failed: list[str],
    ) -> None:

        logger.info(
            "ontology_search_timing rag_multi_ms=%s fusion_ms=%s kb_ok=%s kb_total=%s",
            rag_multi_ms, fusion_ms, kb_ok, kb_total,
            extra={
                "event": "ontology_search_timing",
                "tenant_id": tenant_id,
                "rag_multi_ms": rag_multi_ms,
                "fusion_ms": fusion_ms,
                "kb_ok": kb_ok,
                "kb_total": kb_total,
                "kb_failed": kb_failed,
            },
        )

    async def _rag_fallback_multi(
        self, tenant_id: str, user_id: str, req: OntologySearchRequest,
        kb_ids: list[str], trace_id: str | None,
        collector: ReasoningCollector | None = None,
    ) -> dict:

        empty = {
            "answer": (
                "未在本体图谱中找到与该查询直接相关的信息，"
                "且查询过短无法进行语义检索，请输入更完整的描述。"
            ),
            "references": [],
        }
        if len((req.query or "").strip()) < RAG_MIN_QUERY_LEN:
            return empty

        rag = get_rag_client()
        t_rag = time.perf_counter()
        t_fallback_epoch = time.time()
        tasks = [
            rag.query_detailed(
                query=req.query, tenant_id=tenant_id, mode=req.mode,
                top_k=req.top_k, knowledge_base_id=kid, trace_id=trace_id or "",
            )
            for kid in kb_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        per_kb: list[dict] = []
        kb_failed: list[str] = []
        all_raw_refs: list[dict] = []
        for kid, res in zip(kb_ids, results):
            if isinstance(res, Exception):
                logger.warning("[ontology] RAG query failed kb=%s: %s", kid, res)
                kb_failed.append(kid)
                continue
            answer = res.get("answer") if isinstance(res, dict) else res
            if not (answer or "").strip():
                logger.info("[ontology] RAG returned an empty answer kb=%s", kid)
                kb_failed.append(kid)
                continue
            per_kb.append({"kb_id": kid, "answer": answer})
            if isinstance(res, dict):
                all_raw_refs.extend(res.get("references", []))

        rag_multi_ms = int((time.perf_counter() - t_rag) * 1000)
        if collector:
            collector.step(
                STAGE_RAG_FALLBACK, "RAG 多库检索",
                summary=f"{len(per_kb)}/{len(kb_ids)} 个知识库返回有效答案",
                detail={"kb_ok": [p["kb_id"] for p in per_kb], "kb_failed": kb_failed},
                t_start=t_rag,
            )



            hit = await self._detect_retrieval_rerank_hit(req.query, since_epoch=t_fallback_epoch)
            if hit is True:
                collector.step(
                    STAGE_RETRIEVAL_RERANK, "检索期重排（LightRAG）",
                    summary=(f"已触发（实测）：本次 fallback 检测到 LightRAG 在送 LLM 前调用了 "
                             f"rerank（经 llm-gateway，覆盖 {len(per_kb)} 个 KB 检索）"),
                    detail={"triggered": True, "detected": True, "where": "lightrag_internal",
                            "phase": "retrieval", "kb_count": len(per_kb)},
                )
            elif RAG_RETRIEVAL_RERANK_ENABLED:
                collector.step(
                    STAGE_RETRIEVAL_RERANK, "检索期重排（LightRAG）",
                    status="skipped" if hit is False else "done",
                    summary=("已配置但本次未检测到 rerank 调用"
                             "（可能无召回结果 / enable_rerank=false / rerank 异常回退原序）"
                             if hit is False else
                             "已配置（命中检测暂不可用，无法确认本次是否实际调用）"),
                    detail={"triggered": False if hit is False else None,
                            "configured": True, "detected": hit is not None,
                            "where": "lightrag_internal", "phase": "retrieval"},
                )
            else:
                collector.step(
                    STAGE_RETRIEVAL_RERANK, "检索期重排（LightRAG）", status="skipped",
                    summary=("未启用：LightRAG 未配置检索期 rerank（RERANK_BINDING=null），"
                             "召回结果未在送 LLM 前重排"),
                    detail={"triggered": False, "configured": False,
                            "where": "lightrag_internal", "phase": "retrieval"},
                )

        if not per_kb:
            if collector:
                collector.step(STAGE_FUSION, "多答案融合", status="skipped",
                               summary="无有效答案，无需融合")
            self._log_rag_timing(tenant_id, rag_multi_ms, None, len(per_kb), len(kb_ids), kb_failed)
            return {
                "answer": (
                    "抱歉，所有知识库的语义检索均未返回有效结果，"
                    "请尝试调整查询或检查知识库内容。"
                ),
                "references": [],
            }

        fusion_ms = None
        if len(per_kb) == 1:
            answer = per_kb[0]["answer"]
            if collector:
                collector.step(STAGE_FUSION, "多答案融合", status="skipped",
                               summary="仅 1 个有效答案，无需融合")
        else:
            t_fuse = time.perf_counter()
            answer = await fuse_rag_answers(
                req.query, per_kb,
                tenant_id=tenant_id, user_id=user_id, trace_id=trace_id,
            )
            fusion_ms = int((time.perf_counter() - t_fuse) * 1000)
            if collector:
                collector.step(STAGE_FUSION, "多答案融合",
                               summary=f"融合 {len(per_kb)} 个知识库的答案",
                               t_start=t_fuse)
        self._log_rag_timing(tenant_id, rag_multi_ms, fusion_ms, len(per_kb), len(kb_ids), kb_failed)


        references = await self._build_references(tenant_id, all_raw_refs, allowed_kb_ids=kb_ids)



        candidate_count = len(references)
        if candidate_count > RAG_FALLBACK_MAX_REFS:
            ranked = None
            t_rr = time.perf_counter()
            if RAG_FALLBACK_RERANK_ENABLED:
                ranked = await self._rerank_references(
                    req.query, references, tenant_id=tenant_id, trace_id=trace_id,
                )
            if ranked is not None:
                references = ranked[:RAG_FALLBACK_MAX_REFS]
                if collector:
                    collector.step(
                        STAGE_RERANK, "引用重排",
                        summary=(f"Reranker 重排 {candidate_count} 个候选文档，按相关性取 "
                                 f"top-{RAG_FALLBACK_MAX_REFS}"),
                        detail={
                            "triggered": True,
                            "candidate_count": candidate_count,
                            "max_refs": RAG_FALLBACK_MAX_REFS,
                            "top_scores": [
                                {"file_name": r.get("file_name"),
                                 "relevance": round(r.get("relevance", 0), 4)}
                                for r in references
                            ],
                        },
                        t_start=t_rr,
                    )
            else:

                references.sort(key=lambda r: len(r.get("locations", [])), reverse=True)
                references = references[:RAG_FALLBACK_MAX_REFS]
                if collector:
                    if RAG_FALLBACK_RERANK_ENABLED:
                        collector.step(
                            STAGE_RERANK, "引用重排", status="failed",
                            summary="Reranker 调用失败，回退按 chunk 命中频次排序",
                            detail={"triggered": True, "candidate_count": candidate_count,
                                    "max_refs": RAG_FALLBACK_MAX_REFS,
                                    "fallback": "len(locations)"},
                            t_start=t_rr,
                        )
                    else:
                        collector.step(
                            STAGE_RERANK, "引用重排", status="skipped",
                            summary=("未启用 rerank（ONTOLOGY_RAG_FALLBACK_RERANK_ENABLED=false），"
                                     "按 chunk 命中频次排序取 top-N"),
                            detail={"triggered": False, "candidate_count": candidate_count,
                                    "max_refs": RAG_FALLBACK_MAX_REFS,
                                    "fallback": "len(locations)"},
                        )
        elif collector:
            collector.step(
                STAGE_RERANK, "引用重排", status="skipped",
                summary=f"引用文档 {candidate_count} 个 ≤ top-{RAG_FALLBACK_MAX_REFS}，无需重排",
                detail={"triggered": False, "candidate_count": candidate_count,
                        "max_refs": RAG_FALLBACK_MAX_REFS},
            )

        return {"answer": answer, "references": references}

    async def _detect_retrieval_rerank_hit(
        self, query: str, *, since_epoch: float,
    ) -> bool | None:

        try:
            import hashlib
            from jonex_core.common.cache import CacheUtil
            q = (query or "").strip()
            if not q:
                return False
            qh = hashlib.sha1(q.encode("utf-8")).hexdigest()[:20]
            val = await CacheUtil.get(f"yx:rr:hit:{qh}")
            if val is None:
                return False


            return float(val) >= since_epoch - 2.0
        except Exception as e:
            logger.warning("[rerank] Retrieval-stage hit detection unavailable (ignored): %s", e)
            return None

    async def _rerank_references(
        self, query: str, references: list[dict], *,
        tenant_id: str, trace_id: str | None,
    ) -> list[dict] | None:

        from jonex_core.common.rerank import rerank



        references = sorted(references, key=lambda r: len(r.get("locations", [])), reverse=True)




        docs_text: list[str] = []
        for r in references:
            loc = (r.get("locations") or [{}])[0]
            docs_text.append((loc.get("text") or r.get("file_name") or "")[:1024])

        results = await rerank(
            query, docs_text, tenant_id=tenant_id, kb_id=None, trace_id=trace_id,
        )
        if not results:
            return None

        score_by_idx = {x["index"]: x.get("relevance_score", 0.0) for x in results}
        for i, r in enumerate(references):
            r["relevance"] = score_by_idx.get(i, 0.0)
        sorted_refs = sorted(references, key=lambda r: r.get("relevance", 0.0), reverse=True)


        logger.info(
            "[rerank] query=%s top3_scores=%s (%d documents total)",
            query[:80],
            [round(r.get("relevance", 0), 3) for r in sorted_refs[:3]],
            len(sorted_refs),
        )
        return sorted_refs

    async def query_with_ontology(
        self,
        tenant_id: str,
        user_id: str,
        request: OntologySearchRequest | dict,
        trace_id: str | None = None,
    ) -> dict:
        """本体优先 → RAG fallback 分流查询（多 KB 并行）。

        匹配策略（四级递进）：
          1a) 精确匹配   canonical_name / alias — 短查询高置信旁路
          1b) 前缀匹配   canonical_name — "研发"→"研发流程" 场景
          1c) cjk 全文检索 ont_entity_ft — BM25 模糊匹配
          1d) 向量语义召回 ont_entity_embedding — 同义/近义查询
          1e) RRF 融合全文+向量结果
        2. 路由判定：exact/prefix 恒走本体；向量余弦 ≥ ONTOLOGY_VECTOR_SCORE_MIN({:.2f})
           或全文 BM25 ≥ ONTOLOGY_ROUTE_SCORE_MIN({:.1f}) 走本体路径
        3. 本体路径：1-hop 邻域 → answer_from_facts → LLM 返回答案或 INSUFFICIENT
        4. 分低或 INSUFFICIENT 时降级 RAG（多 KB 并行 + LLM 融合）
        """.format(ONTOLOGY_VECTOR_SCORE_MIN, ONTOLOGY_ROUTE_SCORE_MIN)
        req = OntologySearchRequest(**_payload(request))
        kb_ids = await self._resolve_kb_ids(tenant_id, req)
        gdao = OntologyGraphRepository(get_neo4j_driver())


        collector = ReasoningCollector(enabled=req.with_reasoning and _REASONING_ENABLED)


        ontology_instances: list[dict] = []
        t = time.perf_counter()
        try:
            ontology_instances = await self._match_ontology(gdao, tenant_id, kb_ids, req.query)
            collector.step(
                STAGE_ONTOLOGY_MATCH, "本体实体匹配",
                status="done" if ontology_instances else "skipped",
                summary=(f"命中 {len(ontology_instances)} 个实体"
                         if ontology_instances else "三级匹配均未命中"),
                detail={
                    "hits": [
                        {"name": i.get("name"), "score": i.get("score"), "kb_id": i.get("kb_id")}
                        for i in ontology_instances[:5]
                    ],
                    "total_hits": len(ontology_instances),
                    "kb_count": len(kb_ids),
                },
                t_start=t,
            )
        except Exception as e:
            collector.step(STAGE_ONTOLOGY_MATCH, "本体实体匹配",
                           status="failed", summary="本体检索失败，降级 RAG", t_start=t)
            logger.warning("[ontology] Ontology retrieval failed; falling back to RAG: %s", e)


        answer: str | None = None
        source = "rag"
        rag_used = True
        matched: dict | None = None

        if ontology_instances:

            top_n = ontology_instances[:5]
            go_ontology = False
            for hit in top_n:
                src = hit.get("source", "")
                vs = hit.get("vscore", 0)
                fs = hit.get("ft_score", hit.get("score", 0))
                if src in ("exact", "prefix") or vs >= ONTOLOGY_VECTOR_SCORE_MIN or fs >= ONTOLOGY_ROUTE_SCORE_MIN:
                    go_ontology = True
                    matched = hit
                    break

            top_source = matched.get("source", "") if matched else ""
            top_vscore = matched.get("vscore", 0) if matched else 0.0
            top_ftscore = matched.get("ft_score", matched.get("score", 0)) if matched else 0.0

            route_reason = (
                f"source={top_source}" if top_source in ("exact", "prefix")
                else f"vscore={top_vscore} ≥ {ONTOLOGY_VECTOR_SCORE_MIN}" if top_vscore >= ONTOLOGY_VECTOR_SCORE_MIN
                else f"ft_score={top_ftscore} ≥ {ONTOLOGY_ROUTE_SCORE_MIN}" if top_ftscore >= ONTOLOGY_ROUTE_SCORE_MIN
                else f"分数均不足（top-{len(top_n)} max_vscore={max((h.get('vscore',0) for h in top_n), default=0):.2f} max_ftscore={max((h.get('ft_score',h.get('score',0)) for h in top_n), default=0):.2f}）"
            )
            collector.step(
                STAGE_ROUTE_DECISION, "路由决策",
                summary=(f"走本体路径（{route_reason}）"
                         if go_ontology else
                         f"降级 RAG（{route_reason}）"),
                detail={"source": top_source, "vscore": top_vscore, "ft_score": top_ftscore,
                        "vscore_threshold": ONTOLOGY_VECTOR_SCORE_MIN,
                        "ftscore_threshold": ONTOLOGY_ROUTE_SCORE_MIN,
                        "route": "ontology" if go_ontology else "rag"},
            )
            if go_ontology:
                top_name = matched.get("name", "")
                top_kb_id = matched.get("kb_id") or kb_ids[0]
                logger.info(
                    "[ontology] route=ontology query=%r top_name=%s top_kb=%s source=%s vscore=%.4f ft_score=%s",
                    req.query, top_name, top_kb_id, top_source, top_vscore, top_ftscore,
                )


                t = time.perf_counter()
                facts = None
                try:
                    neighbor_data = await gdao.neighbors(
                        tenant_id, top_kb_id, top_name, limit=20,
                    )
                    facts = neighbor_data.get("facts", [])
                    collector.step(STAGE_FACT_LOOKUP, "邻域事实检索",
                                   summary=f"取到 {len(facts)} 条事实",
                                   detail={"entity": top_name, "kb_id": top_kb_id,
                                           "fact_count": len(facts)},
                                   t_start=t)
                except Exception as e:
                    collector.step(STAGE_FACT_LOOKUP, "邻域事实检索", status="failed",
                                   summary="邻域检索失败，降级 RAG", t_start=t)
                    logger.warning("[ontology] Neighborhood retrieval failed; falling back to RAG: %s", e)


                if facts is not None:
                    t = time.perf_counter()
                    try:
                        llm_answer = await asyncio.wait_for(
                            answer_from_facts(
                                req.query, ontology_instances, facts,
                                tenant_id=tenant_id,
                                kb_id=top_kb_id,
                                user_id=user_id,
                                trace_id=trace_id,
                            ),
                            timeout=30,
                        )
                        if llm_answer and llm_answer != "INSUFFICIENT":
                            answer = llm_answer
                            source = "ontology"
                            rag_used = False
                            collector.step(STAGE_LLM_ANSWER, "本体事实作答",
                                           summary="基于本体事实生成答案", t_start=t)
                        else:
                            collector.step(STAGE_LLM_ANSWER, "本体事实作答", status="skipped",
                                           summary="事实不足（INSUFFICIENT），降级 RAG", t_start=t)
                    except asyncio.TimeoutError:
                        collector.step(STAGE_LLM_ANSWER, "本体事实作答", status="failed",
                                       summary="本体 LLM 超时（30s），降级 RAG", t_start=t)
                        logger.warning("[ontology] Ontology LLM response timed out (30s); falling back to RAG")
                    except Exception as e:
                        collector.step(STAGE_LLM_ANSWER, "本体事实作答", status="failed",
                                       summary="本体作答失败，降级 RAG", t_start=t)
                        logger.warning("[ontology] Ontology QA failed; falling back to RAG: %s", e)
            else:
                logger.info(
                    "[ontology] route=RAG fallback (match score below threshold)source=%s vscore=%.4f ft_score=%s query=%r",
                    top_source, top_vscore, top_ftscore, req.query,
                )


        references: list[dict] = []
        if answer is None:
            fallback = await self._rag_fallback_multi(
                tenant_id, user_id, req, kb_ids, trace_id, collector=collector)
            answer = fallback["answer"]
            references = fallback["references"]
            source = "rag"
        else:

            matched_doc_ids = matched.get("doc_ids") or [] if matched else []
            if matched_doc_ids:
                references = await self._build_references_by_doc_ids(
                    tenant_id, matched_doc_ids, allowed_kb_ids=kb_ids,
                )

        return {
            "answer": answer,
            "source": source,
            "references": references,
            "ontology_instances": ontology_instances,
            "rag_used": rag_used,
            "knowledge_base_ids": kb_ids,
            "reasoning": collector.build(source),
        }


__all__ = ["SearchService"]
