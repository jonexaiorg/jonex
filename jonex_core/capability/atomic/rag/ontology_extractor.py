#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Ontology extractor - Stage4 core component.

Runs inside the atomic-rag process, receives LightRAG extracted candidate entities + original chunks,
uses LLM to perform ontology type classification, attribute completion, and relation classification on them.

Outputs structured ExtractionResult, which is written to PostgreSQL by the knowledge-base
reconcile loop after being relayed through Redis task.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.ontology import OntologyRegistry

logger = __import__("logging").getLogger(__name__)


# ============================================================
# Data model
# ============================================================


@dataclass
class ExtractedEntity:
    canonical_name: str
    entity_type: str
    aliases: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_chunks: List[Dict[str, Any]] = field(default_factory=list)


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


# ============================================================
# LLM invocation (OpenAI compatible interface)
# ============================================================


async def _openai_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
) -> str:
    """Invoke OpenAI compatible interface (deepseek-v4-flash, etc.)."""
    import httpx

    host = os.getenv(
        "ONTOLOGY_LLM_BINDING_HOST",
        os.getenv("LLM_BINDING_HOST", "https://tokenhub.tencentmaas.com/v1"),
    ).rstrip("/")
    api_key = os.getenv(
        "ONTOLOGY_LLM_BINDING_API_KEY",
        os.getenv("LLM_BINDING_API_KEY", ""),
    )
    model = os.getenv(
        "ONTOLOGY_LLM_MODEL",
        os.getenv("LLM_MODEL", "deepseek-v4-flash"),
    )
    timeout = float(os.getenv("ONTOLOGY_LLM_TIMEOUT", "60"))

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{host}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ============================================================
# Prompt template
# ============================================================


SYSTEM_PROMPT_TEMPLATE = """You are an ontology extraction assistant. Based on the following domain ontology definition, classify the input candidate entities into defined types, complete attributes, and assign types to relations.

## Ontology definition (JSON)
{ontology_json}

## Requirements
1. Only output entity types and relation types defined in schema
2. Each entity must include a confidence (0.0-1.0) field, reflecting the confidence of classification correctness
3. If a candidate entity cannot match any type, use "unknown" type and lower confidence
4. attributes Extract from original text based on attribute definitions in schema
5. Relations inferred from entity pair context, relation_type must be defined in schema
6. Output must be valid JSON, cannot contain markdown code block markers
7. Each relation must include source_type and target_type, values are type names from entity ontology definition"""


USER_PROMPT_TEMPLATE = """## Candidate entity list
{entities_json}

## Original context
{chunks_json}

## Output format (JSON)
{{
  "entities": [
    {{"name": "Entity name", "type": "Entity type", "aliases": ["alias1"], "attributes": {{"key": "value"}}, "confidence": 0.95}}
  ],
  "relations": [
    {{"source": "Source entity", "source_type": "Entity type", "target": "Target entity", "target_type": "Entity type", "relation_type": "Relation type", "confidence": 0.9}}
  ]
}}"""


# ============================================================
# OntologyExtractor
# ============================================================


class OntologyExtractor:
    """Ontology extractor - uses LLM to classify candidate entities into ontology types."""

    def __init__(self, registry: OntologyRegistry):
        self._registry = registry

    async def extract(
        self,
        content_list: List[Dict[str, Any]],
        lightrag_entities: List[Dict[str, Any]],
        scope: Dict[str, Any],
    ) -> ExtractionResult:
        """Execute ontology extraction.

        Args:
            content_list: Original chunks, format same as content_list in _ingest_worker.
            lightrag_entities: Candidate entity list extracted by LightRAG,
                From paginated merge results of storage_reader.get_entities().
            scope: Task context {"tenant_id", "knowledge_base_id", "document_id"}.

        Returns:
            ExtractionResult: Structured extraction result.
        """
        domain = scope.get("domain", "default")
        schema = self._registry.get_or_default(domain)

        # Build ontology JSON (for system prompt)
        ontology_json = self._registry.to_prompt_json(domain)

        # Truncate entities and chunks (control token consumption)
        max_entities = int(os.getenv("ONTOLOGY_EXTRACT_MAX_ENTITIES", "200"))
        max_chunks = int(os.getenv("ONTOLOGY_EXTRACT_MAX_CHUNKS", "50"))

        entities_snapshot = [
            {
                "name": e.get("name", e.get("entity_name", "")),
                "original_type": e.get("type", ""),
                "description": e.get("description", "")[:200],
            }
            for e in lightrag_entities[:max_entities]
        ]
        chunks_snapshot = [
            {
                "content": (c.get("content", "") or "")[:500],
            }
            for c in (content_list or [])[:max_chunks]
        ]

        # Return empty result when no candidate entities (trigger pending retry)
        if not entities_snapshot:
            return ExtractionResult(
                errors=["No candidate entities, skipping ontology extraction"],
            )

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(ontology_json=ontology_json)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            entities_json=json.dumps(entities_snapshot, ensure_ascii=False),
            chunks_json=json.dumps(chunks_snapshot, ensure_ascii=False),
        )

        # LLM Invoke
        try:
            raw = await _openai_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=int(os.getenv("ONTOLOGY_EXTRACT_MAX_TOKENS", "4096")),
            )
        except Exception as e:
            logger.error(f"Ontology extraction LLM invocation failed: {e}")
            return ExtractionResult(
                errors=[f"LLM Invocation failed: {e}"],
            )

        result = self._parse_llm_response(raw)
        result.raw_llm_response = raw
        return result

    # ── Parsing ────────────────────────────────────

    @staticmethod
    def _parse_llm_response(raw: str) -> ExtractionResult:
        """Parse the JSON returned by the LLM."""
        import re

        # Extract JSON after removing optional Markdown code fence markers.
        cleaned = raw.strip()
        # Remove wrapping ```json ... ``` markers.
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try the content between the first opening and last closing brace.
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end > start:
                try:
                    data = json.loads(cleaned[start : end + 1])
                except json.JSONDecodeError:
                    return ExtractionResult(errors=["LLM Output is not valid JSON"])
            else:
                return ExtractionResult(errors=["LLM Output is not valid JSON"])

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
                errors.append(f"EntityParsing failed: {ent.get('name', '?')} → {e}")

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
                errors.append(f"RelationParsing failed: {rel.get('source', '?')}→{rel.get('target', '?')} → {e}")

        return ExtractionResult(
            entities=entities,
            relations=relations,
            errors=errors,
        )
