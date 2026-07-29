"""本体实体 embedding 客户端：经 llm-gateway 统一出口，带计量链路头。"""

import hashlib
import logging
import math
import os
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)
_client: Optional[AsyncOpenAI] = None

# embedding 调用超时（秒）与最大重试次数：避免 openai SDK 默认 600s 超时 + 2 次重试
# 在上游冷启动/排队时把单次 embedding 拖到十几秒，进而拖慢本体匹配（ontology_match）阶段。
_EMBED_TIMEOUT = float(os.getenv("ONTOLOGY_EMBED_TIMEOUT", "5"))
_EMBED_MAX_RETRIES = int(os.getenv("ONTOLOGY_EMBED_MAX_RETRIES", "1"))


def _target_dim() -> int:
    """本体向量目标维度：须与 Neo4j 向量索引 ont_entity_embedding 维度一致。"""
    try:
        return int(os.getenv("EMBEDDING_DIM", "1024"))
    except ValueError:
        return 1024


def _send_dim_enabled() -> bool:
    """是否向上游发送 dimensions 参数（与 LightRAG 的 EMBEDDING_SEND_DIM 对齐）。

    默认 false：先靠 _fit_dim 客户端截断兜底（零静默失败风险，不依赖上游是否支持
    dimensions）；待直连 ollama 确认支持 dimensions 后再置 true，把截断下沉到上游。
    见 docs/ontology-vector-embedding-dim-mismatch-fix-plan.md §5.2。
    """
    return os.getenv("EMBEDDING_SEND_DIM", "false").lower() in ("1", "true", "yes", "on")


def _fit_dim(vec: Optional[list[float]], dim: int) -> Optional[list[float]]:
    """把上游返回向量收敛到目标维度，保证与 Neo4j 向量索引维度一致。

    - len == dim：直接返回；
    - len  > dim：截断前 dim 维并 L2 归一化（cosine 相似度要求归一化），并告警
      （说明上游未按 dimensions 截断，已客户端兜底）；
    - len  < dim：视为模型/配置错配，返回 None（不写脏向量，调用方据此跳过）。
    """
    if vec is None:
        return None
    n = len(vec)
    if n == dim:
        return vec
    if n < dim:
        logger.error("本体 embedding 维度 %d < 期望 %d，跳过写入（疑似模型/配置错配）", n, dim)
        return None
    head = vec[:dim]
    norm = math.sqrt(sum(x * x for x in head)) or 1.0
    logger.warning("本体 embedding 上游返回 %d 维，客户端截断到 %d 并归一化", n, dim)
    return [x / norm for x in head]


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=os.getenv("EMBEDDING_BINDING_HOST", "http://llm-gateway:8787/v1"),
            api_key=os.getenv("EMBEDDING_BINDING_API_KEY", "gw_lightrag"),
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
    """生成单条 embedding；失败返回 None（调用方据此跳过向量写入，不阻断主链路）。

    计量维度：入库场景应透传 kb_id/doc_id/trace_id，使 metering.llm_usage_log 的
    ontology_embed 行可按知识库/文档归因、并携带稳定 trace（避免 request_id 落成
    auto: 兜底前缀）；查询场景无 doc 概念，doc_id/trace_id 可缺省。
    """
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
        # 与 LightRAG 一致：让上游按 MRL 截断到目标维度（省带宽、语义更优）。
        create_kwargs["dimensions"] = dim
    try:
        resp = await client.embeddings.create(**create_kwargs)
        # 客户端兜底：无论上游是否按 dimensions 截断，都把维度收敛到 dim，
        # 保证与 Neo4j 向量索引（EMBEDDING_DIM）一致，杜绝 4096 vs 1024 冲突。
        return _fit_dim(resp.data[0].embedding, dim)
    except Exception as e:
        logger.warning("本体 embedding 生成失败（降级跳过向量写入）: %s", e)
        return None
