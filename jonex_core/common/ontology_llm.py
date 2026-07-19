

import json
import logging
import os
from typing import Any, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=os.getenv(
                "ONTOLOGY_LLM_BINDING_HOST",
                "http://llm-gateway:8787/v1",
            ),
            api_key=os.getenv("ONTOLOGY_LLM_BINDING_API_KEY", ""),
        )
    return _client


async def answer_from_facts(
    query: str,
    hits: list[dict],
    facts: list[dict],
    tenant_id: Optional[str] = None,
    kb_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> str:

    client = _get_client()
    model = os.getenv("ONTOLOGY_LLM_MODEL", "deepseek-v4-flash-202605")

    system_prompt = (
        "You are a knowledge graph query assistant. Answer based solely on the "
        "provided facts. If the facts do not contain enough information to answer "
        'the question, respond with exactly "INSUFFICIENT". Do not make up information.'
    )

    facts_text = json.dumps(
        {"entities": hits, "relations": facts}, ensure_ascii=False,
    )


    extra_headers = {
        "X-Jonex-Tenant-Id": tenant_id or "unknown",
        "X-Jonex-Scene": "ontology_qa",
    }
    if kb_id:
        extra_headers["X-Jonex-Kb-Id"] = kb_id
    if user_id:
        extra_headers["X-Jonex-User-Id"] = user_id




    import uuid
    extra_headers["X-Jonex-Trace-Id"] = trace_id or f"ontology_qa:{uuid.uuid4().hex}"

    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Facts:\n{facts_text}\n\nQuestion: {query}",
                },
            ],
            temperature=0.1,
            max_tokens=2048,
            extra_headers=extra_headers,
        )
        content = resp.choices[0].message.content
        if not content or not content.strip():
            logger.warning(
                "Ontology LLM returned empty content, finish_reason=%s",
                resp.choices[0].finish_reason,
            )
            return "INSUFFICIENT"
        return content.strip()
    except Exception as e:
        logger.warning("Ontology LLM call failed: %s", e)
        return "INSUFFICIENT"


async def fuse_rag_answers(
    query: str,
    per_kb_answers: list[dict],
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> str:

    if len(per_kb_answers) < 2:
        return per_kb_answers[0]["answer"] if per_kb_answers else ""

    client = _get_client()
    model = os.getenv("ONTOLOGY_LLM_MODEL", "deepseek-v4-flash-202605")

    system_prompt = (
        "You are a RAG answer fusion assistant. Given multiple answers from different "
        "knowledge bases for the same question, produce a single, accurate, non-redundant "
        "answer. Resolve factual conflicts. When possible, note which knowledge base each "
        "piece of information comes from. Do not make up information."
    )

    import json, uuid
    kb_texts = json.dumps(per_kb_answers, ensure_ascii=False)

    extra_headers = {
        "X-Jonex-Tenant-Id": tenant_id or "unknown",
        "X-Jonex-Scene": "rag_fusion",
    }
    if user_id:
        extra_headers["X-Jonex-User-Id"] = user_id
    extra_headers["X-Jonex-Trace-Id"] = trace_id or f"rag_fusion:{uuid.uuid4().hex}"

    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Query: {query}\n\n"
                        f"Answers from different knowledge bases:\n{kb_texts}\n\n"
                        "Please produce a single fused answer."
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=1000,
            extra_headers=extra_headers,
        )
        content = resp.choices[0].message.content
        return (content or "").strip() or "\n\n---\n\n".join(
            [a["answer"] for a in per_kb_answers]
        )
    except Exception as e:
        logger.warning("RAG answer fusion LLM call failed: %s", e)

        parts = [a["answer"] for a in per_kb_answers]
        return "\n\n---\n\n".join(parts)