"""
LightRAG rag_storage reader.

Reads the raw JSON / GraphML files from LightRAG's internal storage directory
and returns structured, frontend-friendly dicts. Vector fields are always stripped.

Scope filtering supports:
- Old file_source:   ``/app/inputs/.../file.pdf#chunk0@tenant``
- New file_source:   ``kb=...|doc=...|tenant=...|file=...|chunk=...``
"""

from __future__ import annotations

import json
import logging
import os
import xml.etree.ElementTree as ET  # noqa: N814
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _resolve_storage_dir() -> Path:
    value = os.getenv("LIGHTRAG_STORAGE_DIR") or os.getenv("WORKING_DIR") or "/app/rag_storage"
    return Path(value)


def _strip_vector(data: Any) -> Any:
    """Recursively remove ``vector`` keys from dicts and lists."""
    if isinstance(data, dict):
        return {k: _strip_vector(v) for k, v in data.items() if k != "vector"}
    if isinstance(data, list):
        return [_strip_vector(item) for item in data]
    return data


def _parse_file_source(value: str) -> dict[str, str]:
    """Parse file_source into {kb, doc, tenant, file, chunk} dict."""
    if "|" not in value:
        return {"file": value}
    result: dict[str, str] = {}
    for part in value.split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            result[k] = v
    return result


def _infer_entity_type(name: str, content: str = "", graph_type: Optional[str] = None) -> str:
    if graph_type:
        return graph_type
    lower = f"{name} {content}".lower()
    if "(table)" in lower:
        return "table"
    if "(image)" in lower:
        return "image"
    return "unknown"


def _extract_basename(file_path: str) -> str:
    """Get clean file basename from file_source / full path.

    Handles both formats:
    - Old: ``/path/to/file.pdf#chunk0@tenant``
    - New: ``kb=...|file=/path/to/file.pdf|chunk=0``
    """
    if "|" in file_path:
        raw = file_path.split("|file=")[-1] if "|file=" in file_path else file_path
        raw = raw.split("|chunk=")[0] if "|chunk=" in raw else raw
    else:
        raw = file_path.split("#chunk")[0]
    raw = raw.rsplit("@", 1)[0] if "#chunk" not in file_path and "@" in raw else raw
    return Path(raw).name


def _pick_first(sep_values: str) -> str:
    """Return first non-empty segment from `<SEP>`-delimited value."""
    if not sep_values:
        return ""
    parts = [p.strip() for p in sep_values.split("<SEP>") if p.strip()]
    return parts[0] if parts else sep_values


# ──────────────────────────────────────────────
# LightRAGStorageReader
# ──────────────────────────────────────────────


class LightRAGStorageReader:
    """Read LightRAG ``rag_storage`` JSON/GraphML files."""

    def __init__(self, storage_dir: Optional[str | Path] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else _resolve_storage_dir()
        self._json_cache: dict[str, tuple[float, dict]] = {}

    # ── low-level loaders ─────────────────────

    def _load_json(self, file_name: str) -> dict:
        path = self.storage_dir / file_name
        if not path.is_file():
            return {}

        mtime = path.stat().st_mtime
        cached = self._json_cache.get(file_name)
        if cached and cached[0] == mtime:
            return cached[1]

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            logger.warning("Failed to read LightRAG storage: %s, %s", path, exc)
            return {}

        clean = _strip_vector(data)
        self._json_cache[file_name] = (mtime, clean)
        return clean

    def _load_doc_status(self) -> dict:
        return self._load_json("kv_store_doc_status.json")

    def _load_chunks_raw(self) -> list:
        return self._load_json("vdb_chunks.json").get("data", [])

    def _load_entities_raw(self) -> list:
        return self._load_json("vdb_entities.json").get("data", [])

    def _load_relationships_raw(self) -> list:
        return self._load_json("vdb_relationships.json").get("data", [])

    def _load_graphml(self) -> Optional[ET.Element]:
        path = self.storage_dir / "graph_chunk_entity_relation.graphml"
        if not path.is_file():
            return None
        try:
            return ET.parse(str(path)).getroot()
        except Exception as exc:
            logger.warning("GraphML Parsing failed: %s", exc)
            return None

    # ── scope matching ────────────────────────

    @staticmethod
    def _match_file_scope(item_file_path: Optional[str], scope: dict) -> bool:
        paths = set(scope.get("file_paths") or [])
        names = set(scope.get("file_names") or [])
        if not paths and not names:
            return True

        raw = item_file_path or ""
        raw_base = _extract_basename(raw)

        allowed_bases = {Path(p).name for p in paths}
        return (
            raw in paths
            or raw_base in names
            or raw_base in allowed_bases
            or any(name and name in raw for name in names)
        )

    # ── pagination ────────────────────────────

    @staticmethod
    def _paginate(items: list, page: int = 1, page_size: int = 20) -> dict:
        total = len(items)
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size
        return {
            "items": items[offset : offset + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ── entity type map (from GraphML) ────────

    def _build_entity_type_map(self) -> dict[str, str]:
        """Read entity types from GraphML nodes and map entity names to types.

        When ENTITY_TYPES is configured during entity extraction in LightRAG 1.4.16,
        GraphML nodes include an entity_type attribute. This method prioritizes that attribute
        and falls back to an empty dict; the caller should use the _infer_entity_type heuristic.
        """
        gml = self._load_graphml()
        if gml is None:
            return {}

        ns = "http://graphml.graphdrawing.org/xmlns"
        key_map: dict[str, str] = {}
        for key_el in gml.findall(f"{{{ns}}}key"):
            kid = key_el.get("id", "")
            key_map[kid] = key_el.get("attr.name", "")

        type_map: dict[str, str] = {}
        graph = gml.find(f"{{{ns}}}graph")
        if graph is None:
            return {}

        for node_el in graph.findall(f"{{{ns}}}node"):
            node_id = node_el.get("id", "")
            entity_id = ""
            entity_type = ""
            for data_el in node_el.findall(f"{{{ns}}}data"):
                kid = data_el.get("key", "")
                attr_name = key_map.get(kid, kid)
                if attr_name == "entity_type":
                    entity_type = data_el.text or ""
                elif attr_name == "entity_id":
                    entity_id = data_el.text or ""
            if entity_type:
                # Index by both entity_id and node_id to support either lookup method.
                if entity_id:
                    type_map[entity_id] = entity_type
                type_map[node_id] = entity_type

        return type_map

    # ── relation count map ────────────────────

    def _build_relation_count_map(self, scope: dict) -> dict[str, int]:
        rels = self._load_relationships_raw()
        count: dict[str, int] = {}
        for r in rels:
            if not self._match_file_scope(r.get("file_path", ""), scope):
                continue
            count[r.get("src_id", "")] = count.get(r.get("src_id", ""), 0) + 1
            count[r.get("tgt_id", "")] = count.get(r.get("tgt_id", ""), 0) + 1
        return count

    # ── storage files manifest ────────────────

    def _storage_files(self) -> dict[str, bool]:
        files = [
            "kv_store_doc_status.json",
            "vdb_chunks.json",
            "vdb_entities.json",
            "vdb_relationships.json",
            "graph_chunk_entity_relation.graphml",
        ]
        return {f: (self.storage_dir / f).is_file() for f in files}

    # ══════════════════════════════════════════
    # Public API
    # ══════════════════════════════════════════

    def get_summary(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        if not self.storage_dir.is_dir():
            return {
                "knowledge_base_id": scope.get("knowledge_base_id"),
                "tenant_id": scope.get("tenant_id"),
                "source": "lightrag_storage",
                "scope_mode": scope.get("scope_mode", "knowledge_base"),
                "scope_warning": scope.get("scope_warning"),
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

        doc_status = self._load_doc_status()
        chunks_raw = self._load_chunks_raw()
        entities_raw = self._load_entities_raw()
        rels_raw = self._load_relationships_raw()

        matching_docs = 0
        processed = 0
        failed = 0
        last_updated: Optional[str] = None

        for doc_id, ds in doc_status.items():
            fp = ds.get("file_path", "")
            if not self._match_file_scope(fp, scope):
                continue
            matching_docs += 1
            if ds.get("status") == "processed":
                processed += 1
            elif ds.get("status") == "failed":
                failed += 1
            updated = ds.get("updated_at", "") or ds.get("created_at", "")
            if isinstance(updated, str) and (last_updated is None or updated > last_updated):
                last_updated = updated

        filtered_chunks = [c for c in chunks_raw if self._match_file_scope(c.get("file_path", ""), scope)]
        filtered_entities = [e for e in entities_raw if self._match_file_scope(e.get("file_path", ""), scope)]
        filtered_rels = [r for r in rels_raw if self._match_file_scope(r.get("file_path", ""), scope)]

        return {
            "knowledge_base_id": scope.get("knowledge_base_id"),
            "tenant_id": scope.get("tenant_id"),
            "source": "lightrag_storage",
            "scope_mode": scope.get("scope_mode", "knowledge_base"),
            "scope_warning": scope.get("scope_warning"),
            "status": "processed",
            "documents_count": matching_docs or len(doc_status),
            "processed_documents_count": processed or matching_docs or len(doc_status),
            "failed_documents_count": failed,
            "chunks_count": len(filtered_chunks) or len(chunks_raw),
            "entities_count": len(filtered_entities) or len(entities_raw),
            "relationships_count": len(filtered_rels) or len(rels_raw),
            "compile_versions_count": 0,
            "last_updated_at": last_updated,
            "storage_files": self._storage_files(),
        }

    def get_documents(
        self,
        scope: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        scope = scope or {}
        doc_status = self._load_doc_status()
        items: list[dict] = []

        for doc_id, ds in doc_status.items():
            fp = ds.get("file_path", "")
            if not self._match_file_scope(fp, scope):
                continue
            if status and ds.get("status") != status:
                continue
            name = _extract_basename(fp)
            if keyword and keyword.lower() not in name.lower():
                continue

            items.append({
                "id": doc_id,
                "business_document_id": None,
                "file_name": name,
                "file_path": fp,
                "status": ds.get("status", "unknown"),
                "chunks_count": ds.get("chunks_count", 0),
                "content_length": ds.get("content_length", 0),
                "content_summary": (ds.get("content_summary") or "")[:200],
                "error_msg": ds.get("error", ""),
                "created_at": str(ds.get("created_at", "")),
                "updated_at": str(ds.get("updated_at", "")),
                "multimodal_processed": ds.get("metadata", {}).get("multimodal_processed", False) if isinstance(ds.get("metadata"), dict) else False,
            })

        items.sort(key=lambda x: x.get("updated_at", "") or x.get("created_at", ""), reverse=True)
        result = self._paginate(items, page, page_size)
        result["scope_mode"] = scope.get("scope_mode", "knowledge_base")
        result["scope_warning"] = scope.get("scope_warning")
        return result

    def get_entities(
        self,
        scope: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        scope = scope or {}
        if file_path and file_path not in (scope.get("file_paths") or []):
            scope = {**scope, "file_paths": [file_path]}

        entities_raw = self._load_entities_raw()
        rel_count = self._build_relation_count_map(scope)
        type_map = self._build_entity_type_map()

        items: list[dict] = []
        for e in entities_raw:
            fp = e.get("file_path", "")
            if not self._match_file_scope(fp, scope):
                continue
            name = e.get("entity_name", "")
            content = e.get("content", "")
            eid = e.get("__id__", "")
            # Prefer entity_type from GraphML; fall back to heuristic inference.
            e_type = type_map.get(eid) or type_map.get(name) or _infer_entity_type(name, content)
            if entity_type and entity_type != e_type:
                continue
            if keyword and keyword.lower() not in (name + content).lower():
                continue

            items.append({
                "id": e.get("__id__", ""),
                "name": name,
                "type": e_type,
                "description": _pick_first(content)[:300],
                "source_id": _pick_first(e.get("source_id", "")),
                "file_path": _pick_first(fp),
                "created_at": e.get("__created_at__"),
                "relations_count": rel_count.get(name, 0),
            })

        items.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
        result = self._paginate(items, page, page_size)
        result["scope_mode"] = scope.get("scope_mode", "knowledge_base")
        result["scope_warning"] = scope.get("scope_warning")
        return result

    def get_relationships(
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
        if file_path and file_path not in (scope.get("file_paths") or []):
            scope = {**scope, "file_paths": [file_path]}

        rels_raw = self._load_relationships_raw()

        items: list[dict] = []
        for r in rels_raw:
            fp = r.get("file_path", "")
            if not self._match_file_scope(fp, scope):
                continue
            content = r.get("content", "")
            src = r.get("src_id", "")
            tgt = r.get("tgt_id", "")
            if source_entity and src != source_entity:
                continue
            if target_entity and tgt != target_entity:
                continue
            if keyword and keyword.lower() not in f"{src} {tgt} {content}".lower():
                continue

            items.append({
                "id": r.get("__id__", ""),
                "source_entity": src,
                "target_entity": tgt,
                "description": _pick_first(content)[:300],
                "source_id": _pick_first(r.get("source_id", "")),
                "file_path": _pick_first(fp),
                "created_at": r.get("__created_at__"),
            })

        items.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
        result = self._paginate(items, page, page_size)
        result["scope_mode"] = scope.get("scope_mode", "knowledge_base")
        result["scope_warning"] = scope.get("scope_warning")
        return result

    def get_graph_summary(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        entities = self._load_entities_raw()
        rels = self._load_relationships_raw()

        filtered_e = [e for e in entities if self._match_file_scope(e.get("file_path", ""), scope)]
        filtered_r = [r for r in rels if self._match_file_scope(r.get("file_path", ""), scope)]

        nodes_count = len(filtered_e) or len(entities)
        edges_count = len(filtered_r) or len(rels)

        # Entity type distribution: prefer GraphML values.
        gml_type_map = self._build_entity_type_map()
        type_map: dict[str, int] = {}
        for e in (filtered_e or entities):
            eid = e.get("__id__", "")
            name = e.get("entity_name", "")
            e_type = (
                gml_type_map.get(eid)
                or gml_type_map.get(name)
                or _infer_entity_type(name, e.get("content", ""))
            )
            type_map[e_type] = type_map.get(e_type, 0) + 1

        dist: list[dict] = []
        for label, cnt in sorted(type_map.items(), key=lambda x: -x[1]):
            dist.append({"label": label, "count": cnt, "pct": round(cnt / max(nodes_count, 1) * 100, 2)})

        # relation type distribution (all default from LightRAG)
        rel_dist: list[dict] = [{"label": "default", "count": edges_count, "pct": 100.0}] if edges_count else []

        # avg degree
        degree_sum = sum(
            e.get("relations_count", 0)
            for e in (
                self.get_entities(scope, page=1, page_size=max(nodes_count, 1)).get("items", [])
            )
        )
        avg_degree = round(degree_sum / max(nodes_count, 1), 2)

        return {
            "nodes_count": nodes_count,
            "edges_count": edges_count,
            "entity_type_count": len(type_map),
            "relation_type_count": 1 if edges_count else 0,
            "avg_degree": avg_degree,
            "entity_type_distribution": dist,
            "relation_distribution": rel_dist,
        }

    def get_graph(
        self,
        scope: Optional[dict] = None,
        limit: int = 200,
        keyword: Optional[str] = None,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        scope = scope or {}
        if file_path and file_path not in (scope.get("file_paths") or []):
            scope = {**scope, "file_paths": [file_path]}

        # try GraphML first
        gml = self._load_graphml()
        nodes: list[dict] = []
        edges: list[dict] = []

        if gml is not None:
            ns = "http://graphml.graphdrawing.org/xmlns"
            key_map: dict[str, dict] = {}
            for key_el in gml.findall(f"{{{ns}}}key"):
                kid = key_el.get("id", "")
                key_map[kid] = {
                    "name": key_el.get("attr.name", ""),
                    "for": key_el.get("for", ""),
                }

            graph = gml.find(f"{{{ns}}}graph")
            if graph is not None:
                for node_el in graph.findall(f"{{{ns}}}node"):
                    n_data: dict[str, Any] = {"id": node_el.get("id", "")}
                    for data_el in node_el.findall(f"{{{ns}}}data"):
                        kid = data_el.get("key", "")
                        kdef = key_map.get(kid, {})
                        attr_name = kdef.get("name", kid)
                        n_data[attr_name] = data_el.text or ""
                        if attr_name == "created_at" and n_data.get("created_at"):
                            n_data["created_at"] = int(float(n_data["created_at"]))

                    fp = _pick_first(str(n_data.get("file_path", "")))
                    if not self._match_file_scope(fp, scope):
                        continue
                    if keyword and keyword.lower() not in (n_data.get("id", "") + str(n_data.get("description", ""))).lower():
                        continue

                    e_type = n_data.get("entity_type") or _infer_entity_type(n_data.get("entity_id", ""), n_data.get("description", ""))
                    nodes.append({
                        "id": n_data.get("id", ""),
                        "label": n_data.get("entity_id", n_data.get("id", "")),
                        "type": e_type,
                        "degree": 0,
                        "file_path": fp,
                    })

                for edge_el in graph.findall(f"{{{ns}}}edge"):
                    e_data: dict[str, Any] = {"source": edge_el.get("source", ""), "target": edge_el.get("target", "")}
                    for data_el in edge_el.findall(f"{{{ns}}}data"):
                        kid = data_el.get("key", "")
                        kdef = key_map.get(kid, {})
                        attr_name = kdef.get("name", kid)
                        e_data[attr_name] = data_el.text or ""
                        if attr_name == "created_at" and e_data.get("created_at"):
                            e_data["created_at"] = int(float(e_data["created_at"]))

                    fp = _pick_first(str(e_data.get("file_path", "")))
                    if not self._match_file_scope(fp, scope):
                        continue

                    edges.append({
                        "id": f"{e_data['source']}->{e_data['target']}",
                        "source": e_data["source"],
                        "target": e_data["target"],
                        "label": _pick_first(str(e_data.get("description", "")))[:100],
                        "weight": float(e_data.get("weight", 1)) if e_data.get("weight") else 1,
                        "file_path": fp,
                    })

                # compute degrees
                node_degrees: dict[str, int] = {}
                for edge in edges:
                    node_degrees[edge["source"]] = node_degrees.get(edge["source"], 0) + 1
                    node_degrees[edge["target"]] = node_degrees.get(edge["target"], 0) + 1
                for node in nodes:
                    node["degree"] = node_degrees.get(node["id"], 0)

        # fallback: build from vdb files
        if not nodes:
            entities_raw = self._load_entities_raw()
            rels_raw = self._load_relationships_raw()
            seen_entities: set[str] = set()

            for e in entities_raw:
                fp = e.get("file_path", "")
                if not self._match_file_scope(fp, scope):
                    continue
                name = e.get("entity_name", "")
                if keyword and keyword.lower() not in name.lower():
                    continue
                if name in seen_entities:
                    continue
                seen_entities.add(name)
                nodes.append({
                    "id": name,
                    "label": name,
                    "type": _infer_entity_type(name, e.get("content", "")),
                    "degree": 0,
                    "file_path": _pick_first(fp),
                })

            node_degrees = {}
            for r in rels_raw:
                fp = r.get("file_path", "")
                if not self._match_file_scope(fp, scope):
                    continue
                src = r.get("src_id", "")
                tgt = r.get("tgt_id", "")
                edges.append({
                    "id": f"{src}->{tgt}",
                    "source": src,
                    "target": tgt,
                    "label": _pick_first(r.get("content", ""))[:100],
                    "weight": 1,
                    "file_path": _pick_first(fp),
                })
                node_degrees[src] = node_degrees.get(src, 0) + 1
                node_degrees[tgt] = node_degrees.get(tgt, 0) + 1
            for node in nodes:
                node["degree"] = node_degrees.get(node["id"], 0)

        # enforce limit
        nodes = nodes[:limit]
        return {"nodes": nodes, "edges": edges[:limit]}

    def get_document_parse_result(self, scope: Optional[dict] = None) -> dict:
        scope = scope or {}
        summary = self.get_summary(scope)
        documents = self.get_documents(scope, page=1, page_size=1000)
        entities = self.get_entities(scope, page=1, page_size=100)
        relationships = self.get_relationships(scope, page=1, page_size=100)
        return {
            "summary": summary,
            "documents": documents.get("items", []),
            "entities": entities.get("items", []),
            "relationships": relationships.get("items", []),
        }
