"""Search service for Knowledge Base."""

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
from jonex_core.common.i18n import translate
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

# RRF 融合参数
_RRF_K = int(os.getenv("ONTOLOGY_RRF_K", "60"))
_RRF_W_FT = float(os.getenv("ONTOLOGY_RRF_W_FT", "1.0"))
_RRF_W_VEC = float(os.getenv("ONTOLOGY_RRF_W_VEC", "1.0"))

# 与 LightRAG QueryRequest.query 的 min_length=3 对齐：短于该长度 LightRAG 必返回 422。
# 可经 RAG_MIN_QUERY_LEN 调整客户端拦截阈值，但下限恒为 3（LightRAG 硬约束，配更小无意义）。
RAG_MIN_QUERY_LEN = max(3, int(os.getenv("RAG_MIN_QUERY_LEN", "3")))

# 多 KB 本体查询上限（单次最多查 20 个知识库）
MAX_KB_PER_QUERY = 20

# RAG fallback 路径最大引用文档数（按 chunk 命中数降序取 top-N，过滤噪声文档）
RAG_FALLBACK_MAX_REFS = max(1, int(os.getenv("ONTOLOGY_RAG_FALLBACK_MAX_REFS", "5")))

# RAG fallback 引用重排开关（方案 B2）：开启后用 reranker 按相关性排序，
# 失败/关闭时兜底回退 len(locations) 频次排序。默认关闭（灰度）。
RAG_FALLBACK_RERANK_ENABLED = os.getenv(
    "ONTOLOGY_RAG_FALLBACK_RERANK_ENABLED", "false"
).lower() in ("1", "true", "yes", "on")

# LightRAG 检索期 rerank 配置态（召回后、送 LLM 前，在 LightRAG 内部执行，平台不感知
# 每次调用）。此标志仅供 reasoning 展示，须与 deploy/.env.rag 的 RERANK_BINDING 保持一致：
# 当 .env.rag 设 RERANK_BINDING=cohere（指向 gateway /v1/rerank）时，这里应设 true。
RAG_RETRIEVAL_RERANK_ENABLED = os.getenv(
    "RAG_RETRIEVAL_RERANK_ENABLED", "false"
).lower() in ("1", "true", "yes", "on")

# RAG fallback 召回明细配置
ONTOLOGY_RAG_RECALL_DETAIL_ENABLED = os.getenv(
    "ONTOLOGY_RAG_RECALL_DETAIL_ENABLED", "true"
).lower() in ("1", "true", "yes", "on")
ONTOLOGY_RAG_RECALL_MAX_ITEMS = max(1, int(os.getenv("ONTOLOGY_RAG_RECALL_MAX_ITEMS", "20")))
ONTOLOGY_RAG_RECALL_TEXT_MAX = max(1, int(os.getenv("ONTOLOGY_RAG_RECALL_TEXT_MAX", "200")))

# 编排推理链进程级总闸（前端再用 with_reasoning 按请求控制）
_REASONING_ENABLED = os.getenv("REASONING_TRACE_ENABLED", "true").lower() in ("1", "true", "yes")

# 查询 embedding TTL 缓存（相同 query 在 TTL 内不重复调 embedding API）
_query_embedding_cache: dict[str, tuple[float, list[float]]] = {}
_QUERY_EMBED_CACHE_TTL = int(os.getenv("ONTOLOGY_QUERY_EMBED_TTL", "300"))
_QUERY_EMBED_CACHE_MAX = int(os.getenv("ONTOLOGY_QUERY_EMBED_CACHE_MAX", "500"))

# 向量召回 embedding 的阶段级超时（秒）：即便 embedding 客户端自身超时/重试失效，
# 也用 asyncio.wait_for 给本体匹配（ontology_match）向量分支一个硬上界，
# 超时即降级为「仅全文召回」，不阻塞整条搜索链路。
_ONTOLOGY_EMBED_TIMEOUT = float(os.getenv("ONTOLOGY_EMBED_TIMEOUT", "5"))

# ── 本体多跳邻域召回配置 ──
ONTOLOGY_NEIGHBOR_DEPTH_MAX = max(1, int(os.getenv("ONTOLOGY_NEIGHBOR_DEPTH_MAX", "3")))
ONTOLOGY_NEIGHBOR_DEPTH = max(1, min(
    int(os.getenv("ONTOLOGY_NEIGHBOR_DEPTH", "1")), ONTOLOGY_NEIGHBOR_DEPTH_MAX))
ONTOLOGY_NEIGHBOR_LIMIT = max(1, int(os.getenv("ONTOLOGY_NEIGHBOR_LIMIT", "20")))
ONTOLOGY_NEIGHBOR_PER_HOP_LIMIT = max(1, int(os.getenv("ONTOLOGY_NEIGHBOR_PER_HOP_LIMIT", "50")))
ONTOLOGY_NEIGHBOR_TIMEOUT = max(1, int(os.getenv("ONTOLOGY_NEIGHBOR_TIMEOUT", "15")))


def _evict_stale_entries() -> None:
    """淘汰过期条目；超容量时按时间戳淘汰最旧条目。"""
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
    """RRF 融合全文（BM25）与向量（余弦）结果，保留原始分供路由决策。"""
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
    """转义 Lucene 特殊字符，保留原始查询文本。

    不再使用 jieba 分词 + OR 拼接：cjk analyzer 自动做中文 bigram 切分，
    查询端 analyzer 与索引端 analyzer 一致，无需前端分词桥接。
    """
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
            trace_id=trace_id,          # [jonex] 计量链路追踪
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
                    domain_space_id=req.domain_space_id,
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
        trace_id: str = "",          # [jonex] 计量链路追踪
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
        """去重保序 + 数量校验 + 逐 KB 归属校验。"""
        kb_ids = list(dict.fromkeys(k.strip() for k in req.knowledge_base_ids if k and k.strip()))
        if not kb_ids:
            raise InvalidParameterError(message=translate("err.search.kb_required", fallback="请至少指定一个知识库（knowledge_base_ids 不能为空）")  )  # 原消息)
        if len(kb_ids) > MAX_KB_PER_QUERY:
            raise InvalidParameterError(
                message=translate("err.search.max_kb_exceeded", params={"max": str(MAX_KB_PER_QUERY), "n": str(len(kb_ids))}, fallback=f"单次查询最多支持 {MAX_KB_PER_QUERY} 个知识库，当前传入 {len(kb_ids)} 个，请减少后重试")  # 原消息
            )
        await self._assert_kb_ownership(tenant_id, kb_ids)
        return kb_ids

    async def _assert_kb_ownership(self, tenant_id: str, kb_ids: list[str]) -> None:
        """每个 KB 必须属于当前租户（D6 权限模型）。"""
        async with get_db_session() as session:
            repo = KnowledgeInfoRepository(session)
            for kb_id in kb_ids:
                kb = await repo.get_by_id(kb_id, tenant_id)
                if kb is None:
                    raise ResourceNotFoundError(
                        message=translate("err.kb.not_found_or_tenant", params={"kb_id": kb_id}, fallback=f"知识库 {kb_id} 不存在或不属于当前租户")  # 原消息
                    )

    async def _build_references(
        self, tenant_id: str, raw_refs: list[dict],
        allowed_kb_ids: list[str] | None = None,
        doc_map: dict[str, Any] | None = None,
    ) -> list[dict]:
        """从 RAG 返回的原始引用片段富化出完整的 references。

        D5（richification in service）+ D6（doc_id 聚合）+ D8（租户过滤）。
        若对象存储可用则生成预签名 URL，否则 raw_url 为 None。

        allowed_kb_ids：纵深防御——仅保留属于本次请求知识库的文档。即便底层
        LightRAG 检索因 workspace 漏配等原因串库，也不会把库外文档泄露给前端
        （None 表示不做 KB 过滤，兼容历史单库调用）。

        doc_map：可选，调用方预查好的 doc 实体映射 {doc_id: KnowledgeDocument}。
        None 时内部自查。
        """
        doc_ids = [r["doc_id"] for r in raw_refs if r.get("doc_id")]
        if not doc_ids:
            return []

        if doc_map is None:
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
                    "references 富化: %d 个 doc_id 命中库外知识库被剔除（跨库防御）: %s",
                    len(cross_kb), list(cross_kb)[:10],
                )
            doc_map = {
                did: d for did, d in doc_map.items()
                if d.knowledge_base_id in allowed
            }
        filtered = len(set(doc_ids)) - len(doc_map)
        if filtered:
            logger.info(
                "references 富化: %d refs 输入, %d 个 doc_id 被剔除（越权/不存在/库外）",
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
        """文档级 references 富化（本体路径，无 chunk/位置）。

        D8：校验租户归属，越权/不存在自动剔除。
        allowed_kb_ids：纵深防御，仅保留属于本次请求知识库的文档（None 不过滤）。
        """
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
        """引用富化端点（流式 gateway 解析出 doc_ids 后调用此方法）。

        D7：参见 resolve endpoint。支持两种输入：
        - doc_ids：文档级（位置退化为 document）
        - refs：保留位置信息（流式解析出的 ParsedRef 格式）
        """
        if refs:
            return await self._build_references(tenant_id, refs)
        if doc_ids:
            return await self._build_references_by_doc_ids(tenant_id, doc_ids)
        return []

    async def _match_ontology(
        self, gdao: OntologyGraphRepository, tenant_id: str, kb_ids: list[str], query: str,
    ) -> list[dict]:
        """四级递进实体匹配（精确 → 前缀 → 全文+向量并行 → RRF 融合），跨 KB 合并后按 fused_score 降序。"""
        instances: list[dict] = []

        # 1a) 精确匹配旁路（canonical_name 或 alias 完全相等）
        exact = await gdao.exact_match_entities(tenant_id, kb_ids, query)
        if exact:
            for r in exact:
                r["source"] = "exact"
            instances = exact
            logger.info(
                "[ontology] 匹配命中 stage=exact query=%r kb_ids=%s hits=%d",
                query, kb_ids, len(exact),
            )
            return instances

        # 1b) 前缀匹配（"研发"→"研发流程"）
        prefix = await gdao.prefix_match_entities(tenant_id, kb_ids, query, limit=3)
        if prefix:
            for r in prefix:
                r["source"] = "prefix"
            instances = prefix
            logger.info(
                "[ontology] 匹配命中 stage=prefix query=%r kb_ids=%s hits=%d names=%s",
                query, kb_ids, len(prefix), [r.get("name") for r in prefix],
            )
            return instances

        # 1c) 全文 + 1d) 向量：二者无依赖，asyncio.gather 并行
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
                    "[ontology] 向量召回 embedding 超时（%.1fs），降级仅全文 query=%r",
                    _ONTOLOGY_EMBED_TIMEOUT, query,
                )
                return []
            except Exception as e:
                logger.warning("[ontology] 向量召回失败，仅用全文: %s", e)
                return []

        fulltext_hits, vector_hits = await asyncio.gather(_ft(), _vec())

        # 1e) RRF 融合（保留 vscore / ft_score 供路由用）
        instances = _fuse_hits(fulltext_hits, vector_hits)

        if instances:
            logger.info(
                "[ontology] 匹配 stage=hybrid query=%r kb_ids=%s hits=%d "
                "ft_hits=%d vec_hits=%d top_fused=%.4f top_vscore=%.4f top_ftscore=%s",
                query, kb_ids, len(instances), len(fulltext_hits), len(vector_hits),
                instances[0].get("fused_score", 0),
                instances[0].get("vscore", 0),
                instances[0].get("ft_score", 0),
            )
        else:
            logger.info(
                "[ontology] 四级匹配（exact/prefix/fulltext/vector）均未命中 query=%r kb_ids=%s",
                query, kb_ids,
            )
        return instances

    def _log_rag_timing(
        self, tenant_id: str, rag_multi_ms: int | None, fusion_ms: int | None,
        kb_ok: int, kb_total: int, kb_failed: list[str],
    ) -> None:
        """打印 RAG 线路分阶段耗时结构化日志（多库检索 + 多答案融合）。

        无论 with_reasoning 是否开启都会打印，便于按容器 grep；message 内嵌
        数字供人读/grep，extra 保留结构化字段供将来 ELK/JSON 聚合（口径同
        ingest_timing / reconcile_timing，见 docs/ingestion-timing-metrics-design.md §3.4 A）。

        fusion_ms=None 表示未触发融合（无有效答案或仅 1 个答案）。
        查看：make perf-search / docker logs jonex-knowledge-base | findstr ontology_search_timing
        """
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

    async def _rag_retrieve_refs(
        self,
        tenant_id: str,
        req: OntologySearchRequest,
        kb_ids: list[str],
        trace_id: str | None,
    ) -> list[dict]:
        """RAG 多库检索 → chunk 级引用富化（仅 references，不生成回答）。

        本体路径成功时调用此方法获取 chunk 级位置信息：
        - 视频/音频文件的 time_start/time_end（定位播放）
        - 文档的 page_no（跳转页码）
        - chunk 文本片段（关键词高亮上下文）
        """
        if len((req.query or "").strip()) < RAG_MIN_QUERY_LEN:
            return []

        rag = get_rag_client()
        tasks = [
            rag.query_detailed(
                query=req.query, tenant_id=tenant_id, mode=req.mode,
                top_k=req.top_k, knowledge_base_id=kid, trace_id=trace_id or "",
            )
            for kid in kb_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_raw_refs: list[dict] = []
        for kid, res in zip(kb_ids, results):
            if isinstance(res, Exception):
                logger.warning("[ontology] RAG 检索引用失败 kb=%s: %s", kid, res)
                continue
            if isinstance(res, dict):
                all_raw_refs.extend(res.get("references", []))

        if not all_raw_refs:
            return []

        return await self._build_references(
            tenant_id, all_raw_refs, allowed_kb_ids=kb_ids,
        )

    async def _rag_fallback_multi(
        self, tenant_id: str, user_id: str, req: OntologySearchRequest,
        kb_ids: list[str], trace_id: str | None,
        collector: ReasoningCollector | None = None,
    ) -> dict:
        """策略 A：并行查询全部 KB 的 RAG → LLM 融合。

        Args:
            collector: 可选，推理链采集器（P0 非流式埋点）。
        Returns:
            {"answer": str, "references": list[dict]}
        """
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
        t_fallback_epoch = time.time()   # 用于回读「检索期 rerank 命中」标记的时间基线
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
                logger.warning("[ontology] RAG 查询失败 kb=%s: %s", kid, res)
                kb_failed.append(kid)
                continue
            answer = res.get("answer") if isinstance(res, dict) else res
            if not (answer or "").strip():
                logger.info("[ontology] RAG 返回空答案 kb=%s", kid)
                kb_failed.append(kid)
                continue
            per_kb.append({"kb_id": kid, "answer": answer})
            if isinstance(res, dict):
                all_raw_refs.extend(res.get("references", []))

        rag_multi_ms = int((time.perf_counter() - t_rag) * 1000)

        # ── 召回明细：埋点前预查 doc_map（与后续 _build_references 共用，避免重复 DB 查询）──
        recall_doc_ids: list[str] = []
        if ONTOLOGY_RAG_RECALL_DETAIL_ENABLED and collector and all_raw_refs:
            recall_doc_ids = [r.get("doc_id") for r in all_raw_refs if r.get("doc_id")]
        doc_map: dict[str, Any] = {}
        if recall_doc_ids:
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                # get_by_ids 全列加载，访问 knowledge_base_id/file_name 均为标量列
                # （非 relationship / 非 deferred），session 关闭后读取安全
                docs = await repo.get_by_ids(list(set(recall_doc_ids)), tenant_id)
            doc_map = {d.id: d for d in docs}

        allowed = set(kb_ids)
        recalls: list[dict] = []
        if ONTOLOGY_RAG_RECALL_DETAIL_ENABLED and collector and all_raw_refs:
            for r in all_raw_refs[:ONTOLOGY_RAG_RECALL_MAX_ITEMS]:
                did = r.get("doc_id")
                d = doc_map.get(did)
                # 租户+跨库防御：doc_map 已按 tenant_id 查询；查不到或库外一律剔除
                if d is None or d.knowledge_base_id not in allowed:
                    continue
                text = r.get("text") or ""
                if len(text) > ONTOLOGY_RAG_RECALL_TEXT_MAX:
                    text = text[:ONTOLOGY_RAG_RECALL_TEXT_MAX] + "…"
                recalls.append({
                    "doc_id": did,
                    "file_name": d.file_name,
                    "kb_id": d.knowledge_base_id,
                    "chunk_index": r.get("chunk_index"),
                    "chunk_id": r.get("chunk_id"),
                    "text": text,
                })

        if collector:
            collector.step(
                STAGE_RAG_FALLBACK, "RAG 多库检索",
                summary=f"{len(per_kb)}/{len(kb_ids)} 个知识库返回有效答案，召回 {len(recalls)} 个片段",
                detail={
                    "kb_ok": [p["kb_id"] for p in per_kb],
                    "kb_failed": kb_failed,
                    "recall_count": len(recalls),
                    "recalls": recalls,
                },
                t_start=t_rag,
            )
            # 检索期 rerank（LightRAG 内部：召回后、送 LLM 前）实测检测：
            # gateway 被 LightRAG 调用 rerank 时写 Redis 标记，这里按 query 哈希回读，
            # 得到本次查询「是否真的触发了 rerank 调用」（best-effort，检测不可用则回退配置态）。
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

        # 汇集所有 KB 的 references 统一去重富化（按请求 kb_ids 做跨库防御过滤）
        # 传入预查的 doc_map 复用，避免重复 DB 查询
        references = await self._build_references(
            tenant_id, all_raw_refs, allowed_kb_ids=kb_ids, doc_map=doc_map if doc_map else None,
        )

        # 引用排序 + 截断 top-N：优先 reranker 相关性排序，失败/关闭兜底回退 chunk 频次。
        # 各分支都往 reasoning 采集 rerank 阶段，便于前端/排查确认是否触发与打分分布。
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
                # rerank 关闭或调用失败 → 回退 chunk 命中频次排序
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
        """回读 gateway 写入的「检索期 rerank 命中」标记，判断本次查询是否真的触发了
        LightRAG 检索期 rerank 调用。

        Returns:
            True  = 检测到本次查询窗口内的 rerank 调用；
            False = 检测可用但未命中（未调用 / 无召回 / rerank 回退）；
            None  = 检测不可用（Redis 不可达等），无法确认。
        """
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
            # 标记时间戳需落在本次 fallback 检索开始之后（含 2s 时钟容差），
            # 否则视为上一次相同查询遗留的陈旧标记。
            return float(val) >= since_epoch - 2.0
        except Exception as e:
            logger.warning("[rerank] 检索期命中检测不可用（忽略）: %s", e)
            return None

    async def _rerank_references(
        self, query: str, references: list[dict], *,
        tenant_id: str, trace_id: str | None,
    ) -> list[dict] | None:
        """用 reranker 对 references 按相关性排序；返回排序后的新列表，失败返回 None。"""
        from jonex_core.common.rerank import rerank

        # 先按 len(locations) 频次粗排，让 gateway 的 MAX_DOCS 截断切掉「频次最低」的
        # 尾部候选（而非 agg 字典近似随机序），避免误杀相关文档，且与兜底排序口径一致。
        references = sorted(references, key=lambda r: len(r.get("locations", [])), reverse=True)

        # 取每个文档代表文本：首个 location 的 chunk 原文 + 文件名兜底。
        # 取舍：仅取 locations[0].text[:1024]；若关键信息在 chunk 后半段会丢信号，
        # 属已知取舍，后续区分度不足时可改为拼接该文档所有 locations 的 text（限总长）。
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
            r["relevance"] = score_by_idx.get(i, 0.0)  # 透传给前端用于展示/调试
        sorted_refs = sorted(references, key=lambda r: r.get("relevance", 0.0), reverse=True)

        # 可观测性：灰度期对比「频次排序 vs rerank 排序」，确认 reranker 是否真起作用
        logger.info(
            "[rerank] query=%s top3_scores=%s (共 %d 文档)",
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

        # ── 编排推理链采集器（R1 双闸：请求开关 + 进程总闸）──
        collector = ReasoningCollector(enabled=req.with_reasoning and _REASONING_ENABLED)

        # ── 阶段 1：多 KB 本体实体匹配（采集点①）──
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
            logger.warning("[ontology] 本体检索失败，降级 RAG: %s", e)

        # ── 阶段 2：路由决策（采集点②）──
        answer: str | None = None
        source = "rag"
        rag_used = True
        matched: dict | None = None

        if ontology_instances:
            # 路由判定：top-5 内任一命中即走本体（避免高 vscore 候选因全文 rank 落后被埋没）
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
                    "[ontology] 路由=本体 query=%r top_name=%s top_kb=%s source=%s vscore=%.4f ft_score=%s",
                    req.query, top_name, top_kb_id, top_source, top_vscore, top_ftscore,
                )

                # ── 阶段 3：邻域取证（采集点③，独立 try）──
                t = time.perf_counter()
                facts = None
                try:
                    neighbor_data = await asyncio.wait_for(
                        gdao.neighbors(
                            tenant_id, top_kb_id, top_name,
                            limit=ONTOLOGY_NEIGHBOR_LIMIT,
                            depth=ONTOLOGY_NEIGHBOR_DEPTH,
                            per_hop_limit=ONTOLOGY_NEIGHBOR_PER_HOP_LIMIT,
                        ),
                        timeout=ONTOLOGY_NEIGHBOR_TIMEOUT,
                    )
                    facts = neighbor_data.get("facts", [])
                    neighbor_depth = neighbor_data.get("depth", 1)
                    collector.step(
                        STAGE_FACT_LOOKUP, "邻域事实检索",
                        summary=(
                            f"取到 {len(facts)} 条事实"
                            + (f"（{neighbor_depth} 跳）"
                               if neighbor_depth > 1 else "（1 跳）")
                        ),
                        detail={
                            "entity": top_name,
                            "kb_id": top_kb_id,
                            "fact_count": len(facts),
                            "depth": neighbor_depth,
                            "hop_distribution": neighbor_data.get("hop_distribution", {}),
                            "truncated": neighbor_data.get("truncated", False),
                            "facts": facts,
                        },
                        t_start=t,
                    )
                except asyncio.TimeoutError:
                    collector.step(STAGE_FACT_LOOKUP, "邻域事实检索", status="failed",
                                   summary="邻域查询超时，降级 RAG", t_start=t)
                    logger.warning("[ontology] 邻域查询超时（%ds），降级 RAG", ONTOLOGY_NEIGHBOR_TIMEOUT)
                except Exception as e:
                    collector.step(STAGE_FACT_LOOKUP, "邻域事实检索", status="failed",
                                   summary="邻域检索失败，降级 RAG", t_start=t)
                    logger.warning("[ontology] 邻域检索失败，降级 RAG: %s", e)

                # ── 阶段 4：本体作答（采集点④，独立 try）──
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
                        logger.warning("[ontology] 本体 LLM 回答超时（30s），降级 RAG")
                    except Exception as e:
                        collector.step(STAGE_LLM_ANSWER, "本体事实作答", status="failed",
                                       summary="本体作答失败，降级 RAG", t_start=t)
                        logger.warning("[ontology] 本体问答失败，降级 RAG: %s", e)
            else:
                logger.info(
                    "[ontology] 路由=RAG降级（命中但分数不足）source=%s vscore=%.4f ft_score=%s query=%r",
                    top_source, top_vscore, top_ftscore, req.query,
                )

        # ── 阶段 5/6：RAG Fallback + 融合（采集点⑤⑥在 _rag_fallback_multi 内部）──
        references: list[dict] = []
        if answer is None:
            fallback = await self._rag_fallback_multi(
                tenant_id, user_id, req, kb_ids, trace_id, collector=collector)
            answer = fallback["answer"]
            references = fallback["references"]
            source = "rag"
        else:
            # 本体路径成功：执行 RAG 检索获取 chunk 级引用（含视频/音频时间段等位置信息）
            references = await self._rag_retrieve_refs(
                tenant_id, req, kb_ids, trace_id,
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
