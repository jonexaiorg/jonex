#!/usr/bin/python3



from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx

from jonex_core.common.file_source_util import lightrag_workspace

logger = logging.getLogger(__name__)


_DOC_PAGE_MAX = 200


def _pick_first(sep_values: str) -> str:

    if not sep_values:
        return ""
    parts = [p.strip() for p in str(sep_values).split("<SEP>") if p.strip()]
    return parts[0] if parts else str(sep_values)


def _extract_basename(file_path: str) -> str:

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

    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


class LightRAGGraphReader:


    def __init__(self) -> None:
        self.base_url = os.getenv("LIGHTRAG_API_URL", "http://lightrag:9621").rstrip("/")
        self.api_key = os.getenv("LIGHTRAG_API_KEY", "")
        self.timeout = float(os.getenv("LIGHTRAG_API_TIMEOUT", "300"))
        self._client: Optional[httpx.AsyncClient] = None



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



    async def _fetch_all_doc_status(self, scope: dict, status: Optional[str] = None) -> list[dict]:

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



    async def get_summary(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        doc_id = self._scope_doc_id(scope)
        fpath = self._scope_file_path(scope)
        documents_count = processed = failed = chunks_count = 0
        last_updated: Optional[str] = None
        try:


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
            logger.warning("get_summary document count failed: %s", exc)

        entities_count = relationships_count = 0
        try:
            gc = await self._get(
                "/graph/counts", {"doc_id": doc_id, "file_path": fpath}, scope
            )
            entities_count = int(gc.get("entities_count", 0) or 0)
            relationships_count = int(gc.get("relationships_count", 0) or 0)
        except Exception as exc:
            logger.warning("get_summary graph count failed: %s", exc)

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
            "chunks_count": chunks_count,
            "entities_count": entities_count,
            "relationships_count": relationships_count,
            "compile_versions_count": 0,
            "last_updated_at": last_updated,
            "storage_files": {},
        }



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



    async def get_document_parse_result(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        if not (scope.get("document_ids")):
            logger.warning("get_document_parse_result called without document_id scope; returning an empty result to avoid a knowledge-base-wide N+1 query")
            return {"summary": await self.get_summary(scope), "documents": [], "entities": [], "relationships": []}


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
