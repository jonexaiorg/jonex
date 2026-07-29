# -*- coding:utf-8 -*-
"""
usage 抽取：从 chat / embedding / 流式响应提取 token 用量。

Phase G2 完整实现。G1 阶段为桩函数。
"""
from typing import Any

from jonex_core.common.config import get_config


def extract_usage_chat(data: dict) -> dict | None:
    """非流式 chat：从响应 JSON 读 usage"""
    return data.get("usage")


def extract_usage_embedding(data: dict, body: dict) -> dict:
    """非流式 embedding：优先读 usage，缺失则粗估"""
    usage = data.get("usage")
    if usage:
        return usage
    return estimate_embedding_usage(body)


def extract_usage_rerank(data: dict, body: dict, binding: str, template_overhead: int = 0) -> dict:
    """rerank 用量估算：上游不返回标准 usage 时按字符数粗估。

    - cohere：上游一次调用；若返回 usage 优先用真实值，否则按 query + Σdoc 估算。
    - ollama-generate：对每个 doc 各发一次 /api/generate，每次含完整模板
      （prefix+instruct+suffix+query+doc），故按 Σ_i(query + 模板固定开销 + doc_i)
      估算，避免只算「一次 query + documents」导致的显著低估。

    template_overhead：单次调用模板固定部分（prefix+instruct+suffix）的字符数，
    由调用方（router）从选中 profile 计算后传入；cohere 分支忽略。
    """
    usage = data.get("usage")
    if usage:
        return usage
    cfg = get_config()
    per_tok = max(1, cfg.LLMGW_EMBED_AVG_CHARS_PER_TOKEN)
    query = str(body.get("query") or "")
    docs = body.get("documents") or []
    if binding == "ollama-generate":
        total_chars = sum(len(query) + template_overhead + len(str(d)) for d in docs)
    else:  # cohere / 其它
        total_chars = len(query) + sum(len(str(d)) for d in docs)
    pt = max(1, total_chars // per_tok)
    return {"prompt_tokens": pt, "completion_tokens": 0, "total_tokens": pt}



def estimate_embedding_usage(body: dict) -> dict:
    """按输入字符数粗估 embedding token 用量"""
    cfg = get_config()
    texts = body.get("input", "")
    n = sum(len(t) for t in texts) if isinstance(texts, list) else len(str(texts))
    pt = max(1, n // cfg.LLMGW_EMBED_AVG_CHARS_PER_TOKEN)
    return {"prompt_tokens": pt, "total_tokens": pt}


def extract_usage_stream(chunks: list[bytes]) -> dict | None:
    """流式响应：扫描最后一个 data: {…} chunk 提取 usage"""
    for chunk in reversed(chunks):
        decoded = chunk.decode("utf-8", errors="ignore")
        if decoded.startswith("data: "):
            import json
            try:
                data = json.loads(decoded[len("data: "):].strip())
                if data.get("usage"):
                    return data["usage"]
            except (json.JSONDecodeError, KeyError):
                continue
    return None