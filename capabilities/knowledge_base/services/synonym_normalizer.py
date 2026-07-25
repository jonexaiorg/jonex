#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""KB 级同义词 → 本体抽取结果归一器（效果 Y：实体归并）。

纯函数模块，无 IO：输入 atomic-rag 抽取产出的 ``ont_data``（entities/relations）
与同义词组，输出"归一 canonical_name + 统一 entity_type + 内存合并"后的 ont_data。

设计见 docs/kb-synonym-ontology-extraction-integration-plan.md §5.1 / §5.3。
关键约束：Neo4j 节点 MERGE 主键 = (tenant_id, kb_id, entity_type, canonical_name)，
故归并必须同时统一 canonical_name 与 entity_type，否则同名不同类仍是两个节点。
"""
from typing import Any, Optional

from .ontology_synonym_service import _normalize_group, _normalize_key

_UNKNOWN = "unknown"


def build_synonym_index(groups: list) -> dict[str, str]:
    """构建 {归一化 term key -> canonical(display)} 索引。

    Args:
        groups: 同义词组列表，元素含 ``terms``(list) 与 ``canonical``(str)。
                接受 ORM 对象（有 .terms/.canonical 属性）或 dict。

    一期已保证跨组唯一（一词不多组），故一个 key 只映射一个 canonical。
    """
    index: dict[str, str] = {}
    for g in groups or []:
        terms = getattr(g, "terms", None) if not isinstance(g, dict) else g.get("terms")
        canonical = getattr(g, "canonical", None) if not isinstance(g, dict) else g.get("canonical")
        display_terms, keys = _normalize_group(terms or [])
        if not display_terms:
            continue
        # canonical 缺省取 terms[0]（与 service._resolve_canonical 口径一致）
        canon = (canonical or "").strip() or display_terms[0]
        for k in keys:
            index[k] = canon
    return index


def _entity_hit(ent: dict, index: dict[str, str]) -> Optional[str]:
    """实体命中的 canonical；用 canonical_name + aliases 关键词精确匹配。"""
    candidates = [ent.get("canonical_name", "")] + list(ent.get("aliases", []) or [])
    for raw in candidates:
        k = _normalize_key(str(raw))
        if k and k in index:
            return index[k]
    return None


def _pick_unified_type(members: list[dict], canonical: str) -> str:
    """§5.3 entity_type 统一策略：canonical 词类型优先 → 最高 confidence → 首现；unknown 不占优。"""
    canon_key = _normalize_key(canonical)
    # unknown 不占优（除非组内全 unknown）
    non_unknown = [m for m in members if (m.get("entity_type") or _UNKNOWN) != _UNKNOWN]
    pool = non_unknown or members

    # canonical 词自身被抽出的实体优先（其原 canonical_name 归一后 == canonical）
    canon_members = [m for m in pool if _normalize_key(str(m.get("_orig_name", ""))) == canon_key]
    ranked = canon_members or pool
    # 最高 confidence 优先，稳定保序（首现兜底）
    best = max(
        range(len(ranked)),
        key=lambda i: (float(ranked[i].get("confidence", 0.0) or 0.0), -i),
    )
    return ranked[best].get("entity_type") or _UNKNOWN


def normalize_ont_data(ont_data: dict, index: dict[str, str]) -> dict:
    """对 ont_data 做同义词归一 + 实体合并 + 关系端点归一。

    返回**新** dict（不原地改入参）。index 为空时原样返回（浅拷贝）。
    """
    entities = list(ont_data.get("entities", []) or [])
    relations = list(ont_data.get("relations", []) or [])
    if not index or not entities:
        return {**ont_data, "entities": entities, "relations": relations}

    # ── Step A：命中判定，记录原名 ──
    working: list[dict] = []
    for ent in entities:
        e = dict(ent)
        e["_orig_name"] = e.get("canonical_name", "")
        e["_hit"] = _entity_hit(e, index)
        working.append(e)

    # ── Step B：每个 canonical 决定统一 entity_type ──
    by_canon: dict[str, list[dict]] = {}
    for e in working:
        if e["_hit"]:
            by_canon.setdefault(e["_hit"], []).append(e)
    unified_type: dict[str, str] = {
        canon: _pick_unified_type(members, canon) for canon, members in by_canon.items()
    }

    # ── Step C：应用归一 + 按 (entity_type, canonical_name) 内存合并 ──
    merged: dict[tuple, dict] = {}
    order: list[tuple] = []
    for e in working:
        hit = e.pop("_hit")
        orig = e.pop("_orig_name")
        if hit:
            e["canonical_name"] = hit
            e["entity_type"] = unified_type[hit]
            aliases = list(e.get("aliases", []) or [])
            if orig and orig != hit and orig not in aliases:
                aliases.append(orig)
            e["aliases"] = aliases
        key = (e.get("entity_type") or _UNKNOWN, e.get("canonical_name", ""))
        if key not in merged:
            merged[key] = e
            order.append(key)
        else:
            _merge_entity_dict(merged[key], e)

    new_entities = [merged[k] for k in order]

    # ── Step D：关系端点归一（端点名 + 端点类型对齐统一类型）──
    new_relations: list[dict] = []
    seen_rel: set[tuple] = set()
    for rel in relations:
        r = dict(rel)
        _normalize_relation_endpoint(r, "source_name", "source_type", index, unified_type)
        _normalize_relation_endpoint(r, "target_name", "target_type", index, unified_type)
        sig = (
            r.get("source_type", ""), r.get("source_name", ""),
            r.get("relation_type", ""),
            r.get("target_type", ""), r.get("target_name", ""),
        )
        if sig in seen_rel:
            continue
        seen_rel.add(sig)
        new_relations.append(r)

    return {**ont_data, "entities": new_entities, "relations": new_relations}


def _normalize_relation_endpoint(
    rel: dict, name_key: str, type_key: str, index: dict[str, str], unified_type: dict[str, str]
) -> None:
    k = _normalize_key(str(rel.get(name_key, "")))
    if k and k in index:
        canon = index[k]
        rel[name_key] = canon
        if canon in unified_type:
            rel[type_key] = unified_type[canon]


def _merge_entity_dict(base: dict, other: dict) -> None:
    """把 other 合并进 base（同一 (type, canonical) 节点）。"""
    # aliases 并集
    a = list(base.get("aliases", []) or [])
    for x in other.get("aliases", []) or []:
        if x not in a:
            a.append(x)
    base["aliases"] = a
    # description 取更长的非空
    if len(str(other.get("description", "") or "")) > len(str(base.get("description", "") or "")):
        base["description"] = other.get("description", "")
    # attributes 浅合并（base 优先保留已有非空）
    attrs = dict(other.get("attributes", {}) or {})
    attrs.update({k: v for k, v in (base.get("attributes", {}) or {}).items() if v not in (None, "")})
    base["attributes"] = attrs
    # confidence 取最大
    base["confidence"] = max(
        float(base.get("confidence", 0.0) or 0.0), float(other.get("confidence", 0.0) or 0.0)
    )
    # source_chunks 合并
    sc = list(base.get("source_chunks", []) or [])
    for x in other.get("source_chunks", []) or []:
        if x not in sc:
            sc.append(x)
    if sc:
        base["source_chunks"] = sc


__all__ = ["build_synonym_index", "normalize_ont_data"]
