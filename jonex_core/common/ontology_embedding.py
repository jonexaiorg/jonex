

import hashlib
import logging
import math
import os
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)
_client: Optional[AsyncOpenAI] = None



_EMBED_TIMEOUT = float(os.getenv("ONTOLOGY_EMBED_TIMEOUT", "5"))
_EMBED_MAX_RETRIES = int(os.getenv("ONTOLOGY_EMBED_MAX_RETRIES", "1"))


def _target_dim() -> int:

    try:
        return int(os.getenv("EMBEDDING_DIM", "1024"))
    except ValueError:
        return 1024


def _send_dim_enabled() -> bool:

    return os.getenv("EMBEDDING_SEND_DIM", "false").lower() in ("1", "true", "yes", "on")


def _fit_dim(vec: Optional[list[float]], dim: int) -> Optional[list[float]]:

    if vec is None:
        return None
    n = len(vec)
    if n == dim:
        return vec
    if n < dim:
        logger.error("Ontology embedding dimension %d is below the expected %d; skipping write (possible model/configuration mismatch)", n, dim)
        return None
    head = vec[:dim]
    norm = math.sqrt(sum(x * x for x in head)) or 1.0
    logger.warning("Ontology embedding upstream returned %d dimensions; truncating to %d and normalizing on the client", n, dim)
    return [x / norm for x in head]


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=os.getenv("EMBEDDING_BINDING_HOST", "http://llm-gateway:8787/v1"),
            api_key=os.getenv("EMBEDDING_BINDING_API_KEY", ""),
            timeout=_EMBED_TIMEOUT,
            max_retries=_EMBED_MAX_RETRIES,
        )
    return _client


def build_embed_text(canonical_name: str, aliases: list[str], description: str) -> str:
    desc_max = int(os.getenv("ONTOLOGY_EMBED_DESC_MAXLEN", "300"))
    parts = [canonical_name or ""]
    if aliases:
        parts.append(" ".join(a for a in aliases if a))
    if description:
        parts.append((description or "")[:desc_max])
    return " ".join(p for p in parts if p).strip()


def embed_hash(text: str) -> str:
    model = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:8b")
    dim = os.getenv("EMBEDDING_DIM", "1024")
    return hashlib.sha256(f"{model}:{dim}:{text}".encode("utf-8")).hexdigest()


async def embed(text: str, *, tenant_id: Optional[str] = None,
                kb_id: Optional[str] = None, doc_id: Optional[str] = None,
                trace_id: Optional[str] = None) -> Optional[list[float]]:

    if not (text or "").strip():
        return None
    client = _get_client()
    model = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:8b")
    extra_headers = {
        "X-Jonex-Tenant-Id": tenant_id or "unknown",
        "X-Jonex-Scene": "ontology_embed",
    }
    if kb_id:
        extra_headers["X-Jonex-Kb-Id"] = kb_id
    if doc_id:
        extra_headers["X-Jonex-Doc-Id"] = doc_id
    if trace_id:
        extra_headers["X-Jonex-Trace-Id"] = trace_id
    dim = _target_dim()
    create_kwargs: dict = {"model": model, "input": text, "extra_headers": extra_headers}
    if _send_dim_enabled():

        create_kwargs["dimensions"] = dim
    try:
        resp = await client.embeddings.create(**create_kwargs)


        return _fit_dim(resp.data[0].embedding, dim)
    except Exception as e:
        logger.warning("Ontology embedding generation failed (degraded by skipping vector write): %s", e)
        return None
