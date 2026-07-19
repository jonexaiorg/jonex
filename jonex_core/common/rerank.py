

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_BASE = os.getenv("RERANK_BINDING_HOST", "http://llm-gateway:8787/v1")
_KEY = os.getenv("RERANK_BINDING_API_KEY", "")
_MODEL = os.getenv("RERANK_MODEL", "awenleven/Qwen3-Reranker-4B:Q4_K_M")
_TIMEOUT = float(os.getenv("RERANK_CLIENT_TIMEOUT", "30"))


async def rerank(
    query: str,
    documents: list[str],
    *,
    top_n: Optional[int] = None,
    tenant_id: Optional[str] = None,
    kb_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Optional[list[dict]]:

    if not query or not documents:
        return None
    headers = {
        "Authorization": f"Bearer {_KEY}",
        "X-Jonex-Tenant-Id": tenant_id or "unknown",
        "X-Jonex-Scene": "ontology_rerank",
    }
    if kb_id:
        headers["X-Jonex-Kb-Id"] = kb_id
    if trace_id:
        headers["X-Jonex-Trace-Id"] = trace_id
    payload: dict = {"model": _MODEL, "query": query, "documents": documents}
    if top_n is not None:
        payload["top_n"] = top_n
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as cli:
            resp = await cli.post(f"{_BASE}/rerank", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as e:
        logger.warning("[rerank] Call failed; the caller will apply fallback behavior: %s", e)
        return None


__all__ = ["rerank"]
