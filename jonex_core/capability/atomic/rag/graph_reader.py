#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
LightRAG 图数据 HTTP 读取器（LightRAGGraphReader）—— [jonex] 悦溪新增文件。

替代 storage_reader.LightRAGStorageReader 的本地 JSON 读取：存储升级（向量→Milvus、
KV/DocStatus→PG）后 LightRAG 不再写本地 vdb_*.json，改为经 lightrag-server HTTP 端点
穷举实体/关系/图/文档数据（图仍在 Neo4j）。

设计要点（见 docs/ontology-storage-source-http-refactor-plan.md）：
- **无状态单例 + workspace 走方法参数**：不在构造时固定 tenant/kb；每次调用从 scope 的
  tenant_id/knowledge_base_id 现算 LIGHTRAG-WORKSPACE 头，天然支持多租户并发、杜绝串库。
- **输出结构与 LightRAGStorageReader 完全一致**：消费方（本体 worker / adapter action /
  rag client / 前端）零改契约；仅方法由同步改为 **async**（调用方在 async 上下文加 await）。
- `get_graph` 不走 `/graphs`（BFS 语义不同），改用穷举端点自拼（全图→过滤→截断）。
- `get_document_parse_result` 强制 document_id scope，避免整库 N+1。
- 依赖 LightRAG 源码新增端点：GET /graph/entities|relationships|counts|summary
  （见 Reference/LightRAG/JONEX_CHANGES.md 九）。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx

from jonex_core.common.file_source_util import lightrag_workspace

logger = logging.getLogger(__name__)

# 文档分页服务端约束：page_size ∈ [10,200]
_DOC_PAGE_MAX = 200


def _pick_first(sep_values: str) -> str:
    """取 <SEP> 分隔多值的首个非空段（合并实体的 file_path/source_id 为多值）。"""
    if not sep_values:
        return ""
    parts = [p.strip() for p in str(sep_values).split("<SEP>") if p.strip()]
    return parts[0] if parts else str(sep_values)


def _extract_basename(file_path: str) -> str:
    """从 file_source / 路径提取干净文件名（兼容新老格式）。"""
    if "|" in file_path:
        raw = file_path.split("|file=")[-1] if "|file=" in file_path else file_path
        raw = raw.split("|chunk=")[0] if "|chunk=" in raw else raw
    else:
        raw = file_path.split("#chunk")[0]
    raw = raw.rsplit("@", 1)[0] if "#chunk" not in file_path and "@" in raw else raw
    return Path(raw).name


def _infer_entity_type(name: str, content: str = "") -> str:
    lower = f"{name} {content}".lower()
    if "(table)" in lower:
        return "table"
    if "(image)" in lower:
        return "image"
    return "unknown"


def _to_epoch(value: Any) -> Optional[int]:
    """created_at 统一为 int epoch 秒（Neo4j 存 int(time.time())）。"""
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


class LightRAGGraphReader:
    """LightRAG 图数据 HTTP 读取器（无状态单例；workspace 从 scope 现算）。"""

    def __init__(self) -> None:
        self.base_url = os.getenv("LIGHTRAG_API_URL", "http://lightrag:9621").rstrip("/")
        self.api_key = os.getenv("LIGHTRAG_API_KEY", "")
        self.timeout = float(os.getenv("LIGHTRAG_API_TIMEOUT", "300"))
        self._client: Optional[httpx.AsyncClient] = None

    # ── low-level ─────────────────────────────

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-API-Key": self.api_key},
                timeout=self.timeout,
            )
        return self._client

    @staticmethod
    def _ws_headers(scope: dict) -> dict:
        ws = lightrag_workspace(
            scope.get("tenant_id", ""), scope.get("knowledge_base_id", "")
        )
        return {"LIGHTRAG-WORKSPACE": ws} if ws else {}

    async def _get(self, path: str, params: dict, scope: dict) -> dict:
        client = self._ensure_client()
        clean = {k: v for k, v in params.items() if v is not None}
        resp = await client.get(path, params=clean, headers=self._ws_headers(scope))
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, body: dict, scope: dict) -> dict:
        client = self._ensure_client()
        resp = await client.post(path, json=body, headers=self._ws_headers(scope))
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ── scope → endpoint filter ───────────────

    @staticmethod
    def _scope_doc_id(scope: dict) -> Optional[str]:
        ids = scope.get("document_ids") or []
        return ids[0] if ids else None

    @staticmethod
    def _scope_file_path(scope: dict) -> Optional[str]:
        paths = scope.get("file_paths") or []
        return paths[0] if paths else None

    @staticmethod
    def _paginate(items: list, page: int, page_size: int) -> dict:
        total = len(items)
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size
        return {
            "items": items[offset: offset + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ── documents (via /documents/paginated) ──

    async def _fetch_all_doc_status(self, scope: dict, status: Optional[str] = None) -> list[dict]:
        """穷举 LightRAG 全部文档状态（循环 /documents/paginated）。"""
        docs: list[dict] = []
        page = 1
        while True:
            body = {
                "page": page,
                "page_size": _DOC_PAGE_MAX,
                "sort_field": "updated_at",
                "sort_direction": "desc",
            }
            if status:
                body["status_filter"] = status
            data = await self._post("/documents/paginated", body, scope)
            batch = data.get("documents", []) or []
            docs.extend(batch)
            pg = data.get("pagination", {}) or {}
            if not batch or not pg.get("has_next"):
                break
            page += 1
        return docs

    def _map_document(self, d: dict) -> dict:
        fp = d.get("file_path", "") or ""
        meta = d.get("metadata") if isinstance(d.get("metadata"), dict) else {}
        return {
            "id": d.get("id"),
            "business_document_id": None,
            "file_name": _extract_basename(fp),
            "file_path": fp,
            "status": d.get("status", "unknown"),
            "chunks_count": d.get("chunks_count") or 0,
            "content_length": d.get("content_length") or 0,
            "content_summary": (d.get("content_summary") or "")[:200],
            "error_msg": d.get("error") or "",
            "created_at": str(d.get("created_at", "") or ""),
            "updated_at": str(d.get("updated_at", "") or ""),
            "multimodal_processed": bool((meta or {}).get("multimodal_processed", False)),
        }

    async def get_documents(
        self,
        scope: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        scope = scope or {}
        raw = await self._fetch_all_doc_status(scope, status=status)
        items = [self._map_document(d) for d in raw]
        if keyword:
            kw = keyword.lower()
            items = [it for it in items if kw in (it["file_name"] or "").lower()]
        items.sort(key=lambda x: x.get("updated_at", "") or x.get("created_at", ""), reverse=True)
        result = self._paginate(items, page, page_size)
        result["scope_mode"] = scope.get("scope_mode", "knowledge_base")
        result["scope_warning"] = scope.get("scope_warning")
        return result

    # ── entities (via /graph/entities) ────────

    def _map_entity(self, e: dict) -> dict:
        name = e.get("entity_name", "") or ""
        return {
            "id": name,
            "name": name,
            "type": e.get("entity_type") or _infer_entity_type(name, e.get("description", "") or ""),
            "description": _pick_first(e.get("description", "") or "")[:300],
            "source_id": _pick_first(e.get("source_id", "") or ""),
            "file_path": _pick_first(e.get("file_path", "") or ""),
            "created_at": _to_epoch(e.get("created_at")),
            "relations_count": int(e.get("degree") or 0),
        }

    async def get_entities(
        self,
        scope: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        with_degree: bool = True,
    ) -> dict:
        """with_degree=False 时跳过服务端度数聚合（本体抽取不需要 relations_count，省开销）。"""
        scope = scope or {}
        doc_id = document_id or self._scope_doc_id(scope)
        fpath = file_path or self._scope_file_path(scope)
        data = await self._get(
            "/graph/entities",
            {
                "page": page, "page_size": page_size,
                "doc_id": doc_id, "file_path": fpath,
                "keyword": keyword, "entity_type": entity_type,
                "with_degree": str(with_degree).lower(),
            },
            scope,
        )
        items = [self._map_entity(e) for e in (data.get("items") or [])]
        return {
            "items": items,
            "total": data.get("total", len(items)),
            "page": page,
            "page_size": page_size,
            "scope_mode": scope.get("scope_mode", "knowledge_base"),
            "scope_warning": scope.get("scope_warning"),
        }

    # ── relationships (via /graph/relationships) ──

    def _map_relation(self, r: dict) -> dict:
        src = r.get("src_id", "") or ""
        tgt = r.get("tgt_id", "") or ""
        return {
            "id": f"{src}->{tgt}",
            "source_entity": src,
            "target_entity": tgt,
            "description": _pick_first(r.get("description", "") or "")[:300],
            "source_id": _pick_first(r.get("source_id", "") or ""),
            "file_path": _pick_first(r.get("file_path", "") or ""),
            "created_at": _to_epoch(r.get("created_at")),
        }

    async def get_relationships(
        self,
        scope: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> dict:
        scope = scope or {}
        doc_id = document_id or self._scope_doc_id(scope)
        fpath = file_path or self._scope_file_path(scope)
        # src/tgt 过滤下推到服务端（配合服务端 total），避免"取一页再客户端过滤"漏返
        data = await self._get(
            "/graph/relationships",
            {"page": page, "page_size": page_size, "doc_id": doc_id,
             "file_path": fpath, "keyword": keyword,
             "source_entity": source_entity, "target_entity": target_entity},
            scope,
        )
        items = [self._map_relation(r) for r in (data.get("items") or [])]
        return {
            "items": items,
            "total": data.get("total", len(items)),
            "page": page,
            "page_size": page_size,
            "scope_mode": scope.get("scope_mode", "knowledge_base"),
            "scope_warning": scope.get("scope_warning"),
        }

    # ── summary (via status_counts + /graph/counts) ──

    async def get_summary(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        doc_id = self._scope_doc_id(scope)
        fpath = self._scope_file_path(scope)
        documents_count = processed = failed = chunks_count = 0
        last_updated: Optional[str] = None
        try:
            # 穷举全部文档：精确统计文档数 / 已处理 / 失败 / chunk 总数 / 最近更新时间
            # （与旧 storage_reader 从 doc_status.json 全量统计口径一致）
            raw = await self._fetch_all_doc_status(scope)
            documents_count = len(raw)
            for d in raw:
                st = str(d.get("status", "")).lower()
                if st == "processed":
                    processed += 1
                elif st == "failed":
                    failed += 1
                chunks_count += int(d.get("chunks_count") or 0)
                upd = str(d.get("updated_at", "") or d.get("created_at", "") or "")
                if upd and (last_updated is None or upd > last_updated):
                    last_updated = upd
        except Exception as exc:
            logger.warning("get_summary 文档计数失败: %s", exc)

        entities_count = relationships_count = 0
        try:
            gc = await self._get(
                "/graph/counts", {"doc_id": doc_id, "file_path": fpath}, scope
            )
            entities_count = int(gc.get("entities_count", 0) or 0)
            relationships_count = int(gc.get("relationships_count", 0) or 0)
        except Exception as exc:
            logger.warning("get_summary 图计数失败: %s", exc)

        return {
            "knowledge_base_id": scope.get("knowledge_base_id"),
            "tenant_id": scope.get("tenant_id"),
            "source": "lightrag_http",
            "scope_mode": scope.get("scope_mode", "knowledge_base"),
            "scope_warning": scope.get("scope_warning"),
            "status": "processed",
            "documents_count": documents_count,
            "processed_documents_count": processed or documents_count,
            "failed_documents_count": failed,
            "chunks_count": chunks_count,   # 由全量文档 chunks_count 汇总
            "entities_count": entities_count,
            "relationships_count": relationships_count,
            "compile_versions_count": 0,
            "last_updated_at": last_updated,
            "storage_files": {},   # 文件系统概念，HTTP 版移除（保留空 dict 兼容字段存在性）
        }

    # ── graph summary (via /graph/summary) ────

    async def get_graph_summary(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        doc_id = self._scope_doc_id(scope)
        fpath = self._scope_file_path(scope)
        data = await self._get(
            "/graph/summary", {"doc_id": doc_id, "file_path": fpath}, scope
        )
        nodes_count = int(data.get("total_nodes", 0) or 0)
        edges_count = int(data.get("total_edges", 0) or 0)
        type_map = data.get("entity_type_distribution", {}) or {}
        dist = [
            {"label": label, "count": int(cnt),
             "pct": round(int(cnt) / max(nodes_count, 1) * 100, 2)}
            for label, cnt in sorted(type_map.items(), key=lambda x: -int(x[1]))
        ]
        rel_dist = [{"label": "default", "count": edges_count, "pct": 100.0}] if edges_count else []
        # 无向度均值近似：2*边数 / 节点数
        avg_degree = round(2 * edges_count / max(nodes_count, 1), 2)
        return {
            "nodes_count": nodes_count,
            "edges_count": edges_count,
            "entity_type_count": len(type_map),
            "relation_type_count": 1 if edges_count else 0,
            "avg_degree": avg_degree,
            "entity_type_distribution": dist,
            "relation_distribution": rel_dist,
        }

    # ── graph (自拼：穷举 entities + relationships → 过滤 → 截断) ──

    async def _fetch_all_entities(self, scope: dict, keyword: Optional[str], with_degree: bool) -> list[dict]:
        doc_id = self._scope_doc_id(scope)
        fpath = self._scope_file_path(scope)
        out: list[dict] = []
        page = 1
        while True:
            data = await self._get(
                "/graph/entities",
                {"page": page, "page_size": 500, "doc_id": doc_id, "file_path": fpath,
                 "keyword": keyword, "with_degree": str(with_degree).lower()},
                scope,
            )
            batch = data.get("items") or []
            if not batch:
                break
            out.extend(batch)
            if len(out) >= int(data.get("total", 0) or 0) or len(batch) < 500:
                break
            page += 1
        return out

    async def _fetch_all_relations(self, scope: dict, keyword: Optional[str]) -> list[dict]:
        doc_id = self._scope_doc_id(scope)
        fpath = self._scope_file_path(scope)
        out: list[dict] = []
        page = 1
        while True:
            data = await self._get(
                "/graph/relationships",
                {"page": page, "page_size": 500, "doc_id": doc_id,
                 "file_path": fpath, "keyword": keyword},
                scope,
            )
            batch = data.get("items") or []
            if not batch:
                break
            out.extend(batch)
            if len(out) >= int(data.get("total", 0) or 0) or len(batch) < 500:
                break
            page += 1
        return out

    async def get_graph(
        self,
        scope: Optional[dict] = None,
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        scope = scope or {}
        if file_path:
            scope = {**scope, "file_paths": [file_path]}
        if document_id:
            scope = {**scope, "document_ids": [document_id]}

        # keyword 下推服务端（按实体名+描述过滤），避免大库下拉全量再客户端过滤；
        # 图不需要度数（下面按边自算），故 with_degree=False。
        entities = await self._fetch_all_entities(scope, keyword=keyword, with_degree=False)
        relations = await self._fetch_all_relations(scope, keyword=None)

        nodes: list[dict] = []
        seen: set[str] = set()
        for e in entities:
            name = e.get("entity_name", "") or ""
            if not name or name in seen:
                continue
            seen.add(name)
            nodes.append({
                "id": name,
                "label": name,
                "type": e.get("entity_type") or _infer_entity_type(name, e.get("description", "") or ""),
                "degree": 0,
                "file_path": _pick_first(e.get("file_path", "") or ""),
            })

        edges: list[dict] = []
        degrees: dict[str, int] = {}
        for r in relations:
            src = r.get("src_id", "") or ""
            tgt = r.get("tgt_id", "") or ""
            # 有 keyword 时只保留两端都命中的边，构成一致子图（无 keyword 保留全图）；
            # 无 keyword 时 seen 为全部节点，条件恒真。
            if keyword and (src not in seen or tgt not in seen):
                continue
            edges.append({
                "id": f"{src}->{tgt}",
                "source": src,
                "target": tgt,
                "label": _pick_first(r.get("description", "") or "")[:100],
                "weight": float(r.get("weight") or 1),
                "file_path": _pick_first(r.get("file_path", "") or ""),
            })
            degrees[src] = degrees.get(src, 0) + 1
            degrees[tgt] = degrees.get(tgt, 0) + 1
        for n in nodes:
            n["degree"] = degrees.get(n["id"], 0)

        return {"nodes": nodes[:limit], "edges": edges[:limit]}

    # ── composite parse-result (强制 document_id scope) ──

    async def get_document_parse_result(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        if not (scope.get("document_ids")):
            logger.warning("get_document_parse_result 未带 document_id scope，返回空结果（避免整库 N+1）")
            return {"summary": await self.get_summary(scope), "documents": [], "entities": [], "relationships": []}
        # 单文档 scope 下实体/关系量有限；page_size=500 与本体 worker 口径一致，
        # 覆盖绝大多数密集文档（>500 实体的极端文档会截断，前端解析结果页可接受）。
        summary = await self.get_summary(scope)
        documents = await self.get_documents(scope, page=1, page_size=500)
        entities = await self.get_entities(scope, page=1, page_size=500, with_degree=False)
        relationships = await self.get_relationships(scope, page=1, page_size=500)
        return {
            "summary": summary,
            "documents": documents.get("items", []),
            "entities": entities.get("items", []),
            "relationships": relationships.get("items", []),
        }
