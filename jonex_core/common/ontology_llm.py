"""
Ontology QA LLM client: answers queries based on graph facts, returns INSUFFICIENT when insufficient.
"""

import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=os.getenv(
                "ONTOLOGY_LLM_BINDING_HOST",
                "https://tokenhub.tencentmaas.com/v1",
            ),
            api_key=os.getenv("ONTOLOGY_LLM_BINDING_API_KEY", ""),
        )
    return _client


async def answer_from_facts(query: str, hits: list[dict], facts: list[dict]) -> str:
    """Answer based on ontology entity + neighbor facts, return "INSUFFICIENT" when insufficient."""
    client = _get_client()
    model = os.getenv("ONTOLOGY_LLM_MODEL", "deepseek-v4-flash")

    system_prompt = (
        "You are a knowledge graph query assistant. Answer based solely on the "
        "provided facts. If the facts do not contain enough information to answer "
        'the question, respond with exactly "INSUFFICIENT". Do not make up information.'
    )

    facts_text = json.dumps(
        {"entities": hits, "relations": facts}, ensure_ascii=False,
    )

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
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Ontology LLM invocation failed: %s", e)
        return "INSUFFICIENT"