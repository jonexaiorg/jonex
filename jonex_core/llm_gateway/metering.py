

from typing import Any

from jonex_core.common.config import get_config


def extract_usage_chat(data: dict) -> dict | None:

    return data.get("usage")


def extract_usage_embedding(data: dict, body: dict) -> dict:

    usage = data.get("usage")
    if usage:
        return usage
    return estimate_embedding_usage(body)


def extract_usage_rerank(data: dict, body: dict, binding: str, template_overhead: int = 0) -> dict:

    usage = data.get("usage")
    if usage:
        return usage
    cfg = get_config()
    per_tok = max(1, cfg.LLMGW_EMBED_AVG_CHARS_PER_TOKEN)
    query = str(body.get("query") or "")
    docs = body.get("documents") or []
    if binding == "ollama-generate":
        total_chars = sum(len(query) + template_overhead + len(str(d)) for d in docs)
    else:
        total_chars = len(query) + sum(len(str(d)) for d in docs)
    pt = max(1, total_chars // per_tok)
    return {"prompt_tokens": pt, "completion_tokens": 0, "total_tokens": pt}



def estimate_embedding_usage(body: dict) -> dict:

    cfg = get_config()
    texts = body.get("input", "")
    n = sum(len(t) for t in texts) if isinstance(texts, list) else len(str(texts))
    pt = max(1, n // cfg.LLMGW_EMBED_AVG_CHARS_PER_TOKEN)
    return {"prompt_tokens": pt, "total_tokens": pt}


def extract_usage_stream(chunks: list[bytes]) -> dict | None:

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