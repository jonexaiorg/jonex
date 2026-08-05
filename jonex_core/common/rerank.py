"""Rerank 客户端：经 llm-gateway 统一出口，带计量链路头。

失败返回 None，由调用方兜底降级（不阻断主链路）。

⚠️ 配置在模块级读取（仿 ontology_embedding.py 现有模式）：运行时改这些环境变量
   不生效，需重启服务。灰度调参后务必重启相关服务。
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_BASE = os.getenv("RERANK_BINDING_HOST", "http://llm-gateway:8787/v1")
_KEY = os.getenv("RERANK_BINDING_API_KEY", "gw_lightrag")
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
    user_id: Optional[str] = None,
    doc_id: Optional[str] = None,
) -> Optional[list[dict]]:
    """对文档按与 query 的相关性打分。

    Returns:
        [{"index": i, "relevance_score": s}, ...]（按上游返回，未必排序）；失败返回 None。
    """
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
    if user_id:
        headers["X-Jonex-User-Id"] = user_id
    if doc_id:
        headers["X-Jonex-Doc-Id"] = doc_id
    payload: dict = {"model": _MODEL, "query": query, "documents": documents}
    if top_n is not None:
        payload["top_n"] = top_n
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as cli:
            resp = await cli.post(f"{_BASE}/rerank", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as e:
        logger.warning("[rerank] 调用失败，调用方将兜底降级: %s", e)
        return None


__all__ = ["rerank"]
