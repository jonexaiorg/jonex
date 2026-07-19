#!/usr/bin/python3



from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.ontology import OntologyRegistry

logger = __import__("logging").getLogger(__name__)







@dataclass
class ExtractedEntity:
    canonical_name: str
    entity_type: str
    aliases: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    confidence: float = 1.0
    source_chunks: List[Dict[str, Any]] = field(default_factory=list)
    extraction_method: str = "llm_guided"


@dataclass
class ExtractedRelation:
    source_name: str
    source_type: str
    target_name: str
    target_type: str
    relation_type: str
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    entities: List[ExtractedEntity] = field(default_factory=list)
    relations: List[ExtractedRelation] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    raw_llm_response: Optional[str] = None
    ok: bool = True







def _extract_concurrency() -> int:

    try:
        n = int(os.getenv("ONTOLOGY_EXTRACT_CONCURRENCY", "8"))
    except ValueError:
        n = 8
    return max(1, n)


async def _openai_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    scope: Optional[Dict[str, Any]] = None,
    json_mode: bool = False,
) -> str:

    import httpx

    host = os.getenv(
        "ONTOLOGY_LLM_BINDING_HOST",
        "http://llm-gateway:8787/v1",
    ).rstrip("/")
    api_key = os.getenv(
        "ONTOLOGY_LLM_BINDING_API_KEY",
        "",
    )
    model = os.getenv(
        "ONTOLOGY_LLM_MODEL",
        os.getenv("LLM_MODEL", "deepseek-v4-flash-202605"),
    )
    timeout = float(os.getenv("ONTOLOGY_LLM_TIMEOUT", "60"))

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"


    if scope:
        tenant_id = scope.get("tenant_id", "unknown")
        kb_id = scope.get("knowledge_base_id", "")
        doc_id = scope.get("document_id", "")
        headers["X-Jonex-Tenant-Id"] = tenant_id
        headers["X-Jonex-Kb-Id"] = kb_id
        headers["X-Jonex-Doc-Id"] = doc_id
        headers["X-Jonex-Scene"] = "ontology_extract"



        trace_id = scope.get("trace_id") or f"ontology_extract:{tenant_id}:{kb_id}:{doc_id}"
        headers["X-Jonex-Trace-Id"] = trace_id

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{host}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]







SYSTEM_PROMPT_TEMPLATE = """你是一个本体抽取助手。根据以下领域本体定义，将输入的候选实体归类到定义的类型、补全属性、为关系指定类型。

## 本体定义（JSON）
{ontology_json}

## 要求
1. 只输出 schema 中定义的实体类型和关系类型
2. 每个实体必须包含 confidence (0.0-1.0) 字段，反映归类正确性的置信度
3. 如果候选实体无法匹配任何类型，使用 "unknown" 类型并降低 confidence
4. attributes 根据 schema 中的属性定义从原文中提取
5. 关系从实体对的上下文推断，relation_type 必须在 schema 中定义
6. 输出必须是合法的 JSON，不能包含 markdown 代码块标记
7. 每个关系必须包含 source_type 和 target_type，值是实体在本体定义中的类型名"""


USER_PROMPT_TEMPLATE = """## 候选实体列表
{entities_json}

## 原文上下文
{chunks_json}

## 输出格式（JSON）
{{
  "entities": [
    {{"name": "实体名", "type": "实体类型", "aliases": ["别名1"], "attributes": {{"key": "value"}}, "confidence": 0.95}}
  ],
  "relations": [
    {{"source": "源实体", "source_type": "实体类型", "target": "目标实体", "target_type": "实体类型", "relation_type": "关系类型", "confidence": 0.9}}
  ]
}}"""



ENTITY_SYSTEM_PROMPT = """你是本体实体归类助手。根据以下领域本体定义，把候选实体归类到已定义类型并补全属性。
## 本体定义（JSON）
{ontology_json}
## 要求
1. 只输出 schema 中定义的实体类型；无法匹配用 "unknown" 并降低 confidence
2. 每个实体必须含 confidence(0.0-1.0)
3. attributes 仅对 schema 中定义了属性的类型提取；找不到留空，禁止编造
4. 只输出合法 JSON，不要 markdown 代码块"""

ENTITY_USER_PROMPT = """## 候选实体（本批 {n} 个）
{entities_json}
## 输出格式（JSON）
{{"entities":[{{"name":"实体名","original":"输入候选名","type":"实体类型","aliases":["别名"],"attributes":{{}},"confidence":0.95}}]}}"""



RELATION_SYSTEM_PROMPT = """你是本体关系定型助手。给定已抽取的实体关系边，把每条边映射到 schema 中定义的关系类型。
## 本体关系定义（JSON）
{relations_json}
## 要求
1. relation_type 必须是 schema 中定义的关系名；无法匹配则【不输出】该条
2. 不要臆造 schema 之外的关系，不要新增边
3. 不得改写、不得新增端点名（source/target），端点名仅用于参考语义
4. 只输出合法 JSON，不要 markdown"""

RELATION_USER_PROMPT = """## 候选关系边（本批 {n} 条，来自 LightRAG）
{edges_json}
## 输出格式（JSON）
{{"relations":[{{"source":"源实体","target":"目标实体","relation_type":"关系类型","confidence":0.9}}]}}"""







class OntologyExtractor:


    def __init__(self, registry: Optional[OntologyRegistry] = None):
        self._registry = registry
        self._compiled_client: Optional[Any] = None

    def _get_compiled_client(self):
        if self._compiled_client is None:
            from jonex_core.capability.atomic.ontology.compiled_schema_client import (
                CompiledSchemaClient,
            )
            self._compiled_client = CompiledSchemaClient()
        return self._compiled_client

    async def _resolve_schema(
        self,
        compiled_schema: Optional[dict],
        scope: Dict[str, Any],
    ) -> tuple[Optional[Any], Optional[str]]:


        if compiled_schema is not None:
            prompt = compiled_schema.get("prompt_schema")
            if prompt:
                ontology_json = json.dumps(prompt, ensure_ascii=False)
                logger.info(
                    "Using push compiled schema for %s/%s (version=%s)",
                    scope.get("tenant_id", "?"), scope.get("knowledge_base_id", "?"),
                    compiled_schema.get("schema_version", "?"),
                )
                return compiled_schema, ontology_json


        tenant_id = scope.get("tenant_id")
        knowledge_base_id = scope.get("knowledge_base_id")
        if tenant_id and knowledge_base_id:
            try:
                client = self._get_compiled_client()
                raw = await client.get_schema(tenant_id, knowledge_base_id)
                if raw and raw.get("prompt_schema"):
                    ontology_json = json.dumps(raw["prompt_schema"], ensure_ascii=False, indent=2)
                    logger.info(
                        "Using client-fetched compiled schema for %s/%s (source=%s)",
                        tenant_id, knowledge_base_id, raw.get("source_type", "?"),
                    )
                    return raw, ontology_json
            except Exception as e:
                logger.warning("Compiled schema load failed: %s", e)


        if self._registry is not None:
            domain = scope.get("domain", "default")
            ontology_json = self._registry.to_prompt_json(domain)
            logger.info("Fallback to OntologyRegistry domain=%s", domain)
            return None, ontology_json

        return None, None

    async def extract(
        self,
        content_list: List[Dict[str, Any]],
        lightrag_entities: List[Dict[str, Any]],
        scope: Dict[str, Any],
        compiled_schema: Optional[dict] = None,
        lightrag_relations: Optional[List[dict]] = None,
    ) -> ExtractionResult:

        schema, ontology_json = await self._resolve_schema(compiled_schema, scope)
        if not ontology_json:
            return ExtractionResult(ok=False, errors=["无可用 ontology schema，跳过本体抽取"])


        max_entities = int(os.getenv("ONTOLOGY_EXTRACT_MAX_ENTITIES", "200"))
        filtered = self._filter_and_sort(lightrag_entities)[:max_entities]
        if not filtered:
            return ExtractionResult(ok=False, errors=["无候选实体，跳过本体抽取"])


        type_index, case_insensitive = self._build_type_index(schema)
        pre_classified: List[ExtractedEntity] = []
        ambiguous: List[dict] = []
        for e in filtered:
            code = self._match_type(e, type_index, case_insensitive)
            if code:
                name = e.get("name", e.get("entity_name", ""))
                pre_classified.append(ExtractedEntity(
                    canonical_name=name,
                    entity_type=code,
                    aliases=[name],
                    confidence=0.9,
                ))
            else:
                ambiguous.append({
                    "name": e.get("name", e.get("entity_name", "")),
                    "original_type": e.get("type", ""),
                    "description": (e.get("description", "") or "")[:300],
                })


        llm_entities, ent_errors, any_batch_ok = await self._classify_entities(
            ambiguous, ontology_json, scope,
        )
        entities = pre_classified + llm_entities


        entity_type_map = {e.canonical_name: e.entity_type for e in entities}

        drop_chunks = os.getenv("ONTOLOGY_EXTRACT_DROP_CHUNKS", "true").lower() in ("1", "true", "yes", "on")
        if drop_chunks and lightrag_relations is not None:

            relations_json = json.dumps(
                schema.get("prompt_schema", {}).get("relation_types", [])
                if schema else [],
                ensure_ascii=False,
            ) if ontology_json else "[]"

            if not relations_json or relations_json == "[]":
                try:
                    parsed = json.loads(ontology_json)
                    relations_json = json.dumps(parsed.get("relation_types", []), ensure_ascii=False)
                except Exception:
                    relations_json = "[]"
            relations, rel_errors = await self._type_relations(
                lightrag_relations or [], entity_type_map, relations_json, scope,
            )
        else:

            relations, rel_errors = await self._extract_relations_legacy(
                filtered, content_list, ontology_json, scope,
            )


        prov = {
            e.get("name", e.get("entity_name", "")): {
                "source_id": e.get("source_id", ""), "file_path": e.get("file_path", "")
            }
            for e in filtered
        }
        for ent in entities:
            p = prov.get(ent.canonical_name)
            if p and (p["source_id"] or p["file_path"]):
                ent.source_chunks = [p]



        desc_maxlen = int(os.getenv("ONTOLOGY_ENTITY_DESC_MAXLEN", "1000"))
        desc_map = {
            e.get("name", e.get("entity_name", "")): (e.get("description", "") or "")
            for e in filtered
        }
        for ent in entities:
            if not ent.description:
                ent.description = desc_map.get(ent.canonical_name, "")[:desc_maxlen]



        if os.getenv("ONTOLOGY_ENTITY_BACKFILL_ENDPOINTS", "true").lower() in ("1", "true", "yes", "on"):
            known_names = {e.canonical_name for e in entities}
            endpoint_names = {r.source_name for r in relations} | {r.target_name for r in relations}
            for nm in endpoint_names - known_names:
                entities.append(ExtractedEntity(
                    canonical_name=nm,
                    entity_type="unknown",
                    aliases=[nm],
                    confidence=0.3,
                    extraction_method="endpoint_backfill",
                ))


        entities, relations = self._post_validate(entities, relations, schema)



        if os.getenv("ONTOLOGY_KEEP_UNTYPED_EDGES", "false").lower() in ("1", "true", "yes", "on"):
            relations.extend(
                self._fallback_untyped_edges(lightrag_relations or [], relations, entity_type_map)
            )

        ok = bool(entities) or any_batch_ok
        return ExtractionResult(
            entities=entities,
            relations=relations,
            errors=ent_errors + rel_errors,
            ok=ok,
        )



    @staticmethod
    def _post_validate(
        entities: List[ExtractedEntity],
        relations: List[ExtractedRelation],
        schema: Optional[dict],
    ) -> tuple[List[ExtractedEntity], List[ExtractedRelation]]:

        if not schema:
            return entities, relations

        valid_etypes = {et.get("name", "") for et in schema.get("entity_types", [])}
        rel_constraint = {
            rt.get("name", ""): (rt.get("source", ""), rt.get("target", ""))
            for rt in schema.get("relation_types", [])
        }

        kept_e = [e for e in entities if e.entity_type in valid_etypes or e.entity_type == "unknown"]
        kept_r = []
        for r in relations:
            st = rel_constraint.get(r.relation_type)
            if st is None:
                continue

            src_ok = OntologyExtractor._endpoint_ok(r.source_type, st[0])
            tgt_ok = OntologyExtractor._endpoint_ok(r.target_type, st[1])
            if src_ok and tgt_ok:
                kept_r.append(r)
        return kept_e, kept_r

    @staticmethod
    def _endpoint_ok(actual: str, expected: str) -> bool:

        return (not actual) or (actual == "unknown") or (actual == expected)

    @staticmethod
    def _fallback_untyped_edges(
        lightrag_relations: List[dict],
        typed_relations: List[ExtractedRelation],
        entity_type_map: Dict[str, str],
    ) -> List[ExtractedRelation]:

        typed_pairs = {(r.source_name, r.target_name) for r in typed_relations}
        typed_pairs |= {(r.target_name, r.source_name) for r in typed_relations}
        extra: List[ExtractedRelation] = []
        for lr in lightrag_relations:
            s = lr.get("source_entity", "")
            t = lr.get("target_entity", "")
            if not s or not t or (s, t) in typed_pairs:
                continue
            typed_pairs.add((s, t))
            typed_pairs.add((t, s))
            try:
                conf = float(lr.get("weight", 0.5))
            except (ValueError, TypeError):
                conf = 0.5
            extra.append(ExtractedRelation(
                source_name=s, target_name=t,
                source_type=entity_type_map.get(s, ""),
                target_type=entity_type_map.get(t, ""),
                relation_type="RELATED_TO", confidence=conf,
            ))
        return extra



    @staticmethod
    def _load_json(raw: str) -> Optional[dict]:

        import re

        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            s, e = cleaned.find("{"), cleaned.rfind("}")
            if s != -1 and e > s:
                try:
                    return json.loads(cleaned[s:e + 1])
                except json.JSONDecodeError:
                    return None
        return None

    @staticmethod
    def _parse_llm_response(raw: str) -> ExtractionResult:

        data = OntologyExtractor._load_json(raw)
        if data is None:
            return ExtractionResult(errors=["LLM 输出不是合法 JSON"])

        entities = []
        relations = []
        errors = []

        for ent in data.get("entities", []):
            try:
                entities.append(
                    ExtractedEntity(
                        canonical_name=ent.get("name", ""),
                        entity_type=ent.get("type", "unknown"),
                        aliases=ent.get("aliases", []),
                        attributes=ent.get("attributes", {}),
                        confidence=float(ent.get("confidence", 1.0)),
                    )
                )
            except (ValueError, TypeError) as e:
                errors.append(f"实体解析失败: {ent.get('name', '?')} → {e}")

        for rel in data.get("relations", []):
            try:
                relations.append(
                    ExtractedRelation(
                        source_name=rel.get("source", ""),
                        source_type=rel.get("source_type", ""),
                        target_name=rel.get("target", ""),
                        target_type=rel.get("target_type", ""),
                        relation_type=rel.get("relation_type", ""),
                        confidence=float(rel.get("confidence", 1.0)),
                    )
                )
            except (ValueError, TypeError) as e:
                errors.append(f"关系解析失败: {rel.get('source', '?')}→{rel.get('target', '?')} → {e}")

        return ExtractionResult(
            entities=entities,
            relations=relations,
            errors=errors,
        )



    @staticmethod
    def _build_type_index(schema: Optional[dict]) -> tuple[dict, bool]:

        if not schema:
            return {}, True
        case_insensitive = (schema.get("disambiguation") or {}).get("case_insensitive", True)
        index: dict[str, str] = {}
        for et in schema.get("entity_types", []):
            code = et.get("name", "")
            if not code:
                continue
            keys = [code, et.get("display_name", "")] + (et.get("aliases") or [])
            for k in keys:
                k = (k or "").strip()
                if not k:
                    continue
                index[k.lower() if case_insensitive else k] = code
        return index, case_insensitive

    @staticmethod
    def _match_type(raw_entity: dict, index: dict, case_insensitive: bool) -> Optional[str]:

        t = (raw_entity.get("type", "") or "").strip()
        if not t:
            return None
        return index.get(t.lower() if case_insensitive else t)

    @staticmethod
    def _filter_and_sort(lightrag_entities: List[dict]) -> List[dict]:

        drop_orphan = os.getenv("ONTOLOGY_EXTRACT_DROP_ORPHAN", "true").lower() in ("1", "true", "yes", "on")
        items = lightrag_entities
        if drop_orphan:
            items = [
                e for e in items
                if not (e.get("relations_count", 0) == 0 and not (e.get("description", "") or "").strip())
            ]
        return sorted(items, key=lambda e: e.get("relations_count", 0), reverse=True)



    async def _classify_entities(
        self,
        entities_snapshot: List[dict],
        ontology_json: str,
        scope: Optional[Dict[str, Any]],
    ) -> tuple[List[ExtractedEntity], List[str], bool]:

        batch_size = int(os.getenv("ONTOLOGY_EXTRACT_BATCH_SIZE", "35"))
        max_tokens = int(os.getenv("ONTOLOGY_EXTRACT_MAX_TOKENS", "4096"))
        json_mode = os.getenv("ONTOLOGY_EXTRACT_JSON_MODE", "true").lower() in ("1", "true", "yes", "on")
        system_prompt = ENTITY_SYSTEM_PROMPT.format(ontology_json=ontology_json)

        batches = [
            entities_snapshot[i:i + batch_size]
            for i in range(0, len(entities_snapshot), batch_size)
        ]
        sem = asyncio.Semaphore(_extract_concurrency())

        async def _run_batch(batch_idx: int, batch: List[dict]) -> tuple[List[ExtractedEntity], List[str], bool]:

            b_entities: List[ExtractedEntity] = []
            b_errors: List[str] = []
            user_prompt = ENTITY_USER_PROMPT.format(n=len(batch), entities_json=json.dumps(batch, ensure_ascii=False))
            async with sem:
                try:
                    raw = await _openai_chat(
                        messages=[{"role": "system", "content": system_prompt},
                                  {"role": "user", "content": user_prompt}],
                        temperature=0, max_tokens=max_tokens, scope=scope, json_mode=json_mode,
                    )
                except Exception as e:
                    b_errors.append(f"实体批#{batch_idx} 调用失败: {e}")
                    return b_entities, b_errors, False

            data = self._load_json(raw)
            if data is None:
                b_errors.append(f"实体批#{batch_idx} 输出非合法 JSON")
                return b_entities, b_errors, False

            for ent in data.get("entities", []):
                try:
                    name = ent.get("name", "")
                    original = ent.get("original", "")
                    aliases = list({*ent.get("aliases", []), name, original} - {""})
                    b_entities.append(ExtractedEntity(
                        canonical_name=name, entity_type=ent.get("type", "unknown"),
                        aliases=aliases, attributes=ent.get("attributes", {}),
                        confidence=float(ent.get("confidence", 1.0)),
                    ))
                except (ValueError, TypeError) as e:
                    b_errors.append(f"实体解析失败 {ent.get('name','?')}: {e}")
            return b_entities, b_errors, True


        results = await asyncio.gather(*[_run_batch(i, b) for i, b in enumerate(batches)])
        entities: List[ExtractedEntity] = []
        errors: List[str] = []
        any_ok = False
        for b_entities, b_errors, b_ok in results:
            entities.extend(b_entities)
            errors.extend(b_errors)
            any_ok = any_ok or b_ok

        return entities, errors, any_ok




    async def _extract_relations_legacy(
        self,
        entities_snapshot: List[dict],
        content_list: List[Dict[str, Any]],
        ontology_json: str,
        scope: Optional[Dict[str, Any]],
    ) -> tuple[List[ExtractedRelation], List[str]]:

        max_chunks = int(os.getenv("ONTOLOGY_EXTRACT_MAX_CHUNKS", "50"))
        max_tokens = int(os.getenv("ONTOLOGY_EXTRACT_MAX_TOKENS", "4096"))
        json_mode = os.getenv("ONTOLOGY_EXTRACT_JSON_MODE", "true").lower() in ("1", "true", "yes", "on")

        chunks_snapshot = [
            {"content": (c.get("content", "") or "")[:500]}
            for c in (content_list or [])[:max_chunks]
        ]

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(ontology_json=ontology_json)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            entities_json=json.dumps(entities_snapshot, ensure_ascii=False),
            chunks_json=json.dumps(chunks_snapshot, ensure_ascii=False),
        )

        try:
            raw = await _openai_chat(
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_prompt}],
                temperature=0, max_tokens=max_tokens, scope=scope, json_mode=json_mode,
            )
        except Exception as e:
            return [], [f"关系抽取调用失败: {e}"]

        data = self._load_json(raw)
        if data is None:
            return [], ["关系抽取输出非合法 JSON"]

        relations, errors = [], []
        for rel in data.get("relations", []):
            try:
                relations.append(ExtractedRelation(
                    source_name=rel.get("source", ""),
                    source_type=rel.get("source_type", ""),
                    target_name=rel.get("target", ""),
                    target_type=rel.get("target_type", ""),
                    relation_type=rel.get("relation_type", ""),
                    confidence=float(rel.get("confidence", 1.0)),
                ))
            except (ValueError, TypeError) as e:
                errors.append(f"关系解析失败: {rel.get('source', '?')}→{rel.get('target', '?')} → {e}")

        return relations, errors



    async def _type_relations(
        self,
        lightrag_relations: List[dict],
        entity_type_map: Dict[str, str],
        relations_json: str,
        scope: Optional[Dict[str, Any]],
    ) -> tuple[List[ExtractedRelation], List[str]]:

        rel_batch = int(os.getenv("ONTOLOGY_EXTRACT_REL_BATCH_SIZE", "50"))
        max_tokens = int(os.getenv("ONTOLOGY_EXTRACT_MAX_TOKENS", "4096"))
        json_mode = os.getenv("ONTOLOGY_EXTRACT_JSON_MODE", "true").lower() in ("1", "true", "yes", "on")
        use_original_endpoint = os.getenv("ONTOLOGY_REL_USE_ORIGINAL_ENDPOINT", "true").lower() in ("1", "true", "yes", "on")

        edges = [
            {"source": r.get("source_entity", ""), "target": r.get("target_entity", ""),
             "description": (r.get("description", "") or "")[:200]}
            for r in lightrag_relations
            if r.get("source_entity") and r.get("target_entity")
        ]
        if not edges:
            return [], []

        system_prompt = RELATION_SYSTEM_PROMPT.format(relations_json=relations_json)
        batches = [edges[i:i + rel_batch] for i in range(0, len(edges), rel_batch)]
        sem = asyncio.Semaphore(_extract_concurrency())

        async def _run_batch(batch_idx: int, batch: List[dict]) -> tuple[List[ExtractedRelation], List[str]]:

            b_relations: List[ExtractedRelation] = []
            b_errors: List[str] = []
            if use_original_endpoint:

                indexed_batch = [
                    {"idx": j, "source": e["source"], "target": e["target"],
                     "description": e["description"]}
                    for j, e in enumerate(batch)
                ]
                edge_by_idx = {j: e for j, e in enumerate(batch)}
                user_prompt = (
                    "## 候选关系边（本批 {n} 条，来自 LightRAG）\n"
                    "{edges_json}\n"
                    "## 输出格式（JSON）\n"
                    '{{"relations":[{{"idx":0,"relation_type":"关系类型","confidence":0.9}}]}}'
                ).format(n=len(indexed_batch), edges_json=json.dumps(indexed_batch, ensure_ascii=False))
                async with sem:
                    try:
                        raw = await _openai_chat(
                            messages=[{"role": "system", "content": system_prompt},
                                      {"role": "user", "content": user_prompt}],
                            temperature=0, max_tokens=max_tokens, scope=scope, json_mode=json_mode,
                        )
                    except Exception as e:
                        b_errors.append(f"关系批#{batch_idx} 调用失败: {e}")
                        return b_relations, b_errors
                data = self._load_json(raw)
                if data is None:
                    b_errors.append(f"关系批#{batch_idx} 输出非合法 JSON")
                    return b_relations, b_errors
                for rel in data.get("relations", []):
                    idx = rel.get("idx")
                    if idx is None or idx not in edge_by_idx:
                        continue
                    e = edge_by_idx[idx]
                    src, tgt = e["source"], e["target"]
                    b_relations.append(ExtractedRelation(
                        source_name=src, target_name=tgt,
                        source_type=entity_type_map.get(src, ""),
                        target_type=entity_type_map.get(tgt, ""),
                        relation_type=rel.get("relation_type", ""),
                        confidence=float(rel.get("confidence", 1.0)),
                    ))
            else:
                user_prompt = RELATION_USER_PROMPT.format(n=len(batch), edges_json=json.dumps(batch, ensure_ascii=False))
                async with sem:
                    try:
                        raw = await _openai_chat(
                            messages=[{"role": "system", "content": system_prompt},
                                      {"role": "user", "content": user_prompt}],
                            temperature=0, max_tokens=max_tokens, scope=scope, json_mode=json_mode,
                        )
                    except Exception as e:
                        b_errors.append(f"关系批#{batch_idx} 调用失败: {e}")
                        return b_relations, b_errors
                data = self._load_json(raw)
                if data is None:
                    b_errors.append(f"关系批#{batch_idx} 输出非合法 JSON")
                    return b_relations, b_errors
                for rel in data.get("relations", []):
                    src, tgt = rel.get("source", ""), rel.get("target", "")
                    b_relations.append(ExtractedRelation(
                        source_name=src, target_name=tgt,
                        source_type=entity_type_map.get(src, ""),
                        target_type=entity_type_map.get(tgt, ""),
                        relation_type=rel.get("relation_type", ""),
                        confidence=float(rel.get("confidence", 1.0)),
                    ))
            return b_relations, b_errors


        results = await asyncio.gather(*[_run_batch(i, b) for i, b in enumerate(batches)])
        relations: List[ExtractedRelation] = []
        errors: List[str] = []
        for b_relations, b_errors in results:
            relations.extend(b_relations)
            errors.extend(b_errors)
        return relations, errors
