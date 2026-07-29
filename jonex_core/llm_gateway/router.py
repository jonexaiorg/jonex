# -*- coding:utf-8 -*-
"""
LLM 网关路由：OpenAI 兼容端点 + 计量查询。
"""

import time
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from jonex_core.common.config import get_config
from jonex_core.llm_gateway.context import MeteringContext, derive_request_id, parse_ctx
from jonex_core.llm_gateway.metering import (
    extract_usage_chat,
    extract_usage_embedding,
    extract_usage_rerank,
    extract_usage_stream,
)
from jonex_core.llm_gateway.recorder import UsageRecord, get_recorder
from jonex_core.llm_gateway.rerank_profiles import get_profile
from jonex_core.llm_gateway.upstream import proxy_nonstream, proxy_rerank, proxy_stream

logger = logging.getLogger("llm_gateway")

router = APIRouter()


def _check_quota(ctx: MeteringContext) -> bool:
    """配额检查预留钩子（G5.2），默认放行。"""
    cfg = get_config()
    if not cfg.LLMGW_QUOTA_ENABLED:
        return True
    # TODO(G5a): 按 tenant/scene 日 token 上限检查，超额返回 429
    return True


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "llm-gateway"}


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, ctx: MeteringContext = Depends(parse_ctx)):
    """OpenAI 兼容 chat completions（支持流式与非流式）"""
    if not _check_quota(ctx):
        return JSONResponse({"error": "quota_exceeded", "message": "配额超限"}, status_code=429)
    body = await request.json()
    model = body.get("model", "unknown")
    stream = body.get("stream", False)

    logger.info(
        "chat 请求 | req_id=%s tenant=%s scene=%s model=%s stream=%s",
        ctx.request_id, ctx.tenant_id, ctx.scene, model, stream,
    )

    if stream:
        return await _stream_chat(request, body, ctx, model)

    # 非流式转发
    data, status_code, latency_ms = await proxy_nonstream(request, body, ctx)
    usage = extract_usage_chat(data)

    logger.info(
        "chat 完成 | req_id=%s model=%s status=%s latency_ms=%s usage=%s",
        ctx.request_id, model, status_code, latency_ms, usage,
    )

    # 计量记录
    _record_usage(ctx, model, usage, stream=False, estimated=(usage is None), latency_ms=latency_ms, body=body)

    return JSONResponse(data, status_code=status_code)


async def _stream_chat(
    request: Request,
    body: dict,
    ctx: MeteringContext,
    model: str,
):
    """流式 chat：边转发边缓存，结束后取 usage 计量"""
    t0 = time.monotonic()
    chunks: list[bytes] = []
    usage = None

    async def generate():
        nonlocal usage
        async for chunk in proxy_stream(request, body, ctx):
            chunks.append(chunk)
            yield chunk
        # 流结束后提取 usage
        latency_ms = int((time.monotonic() - t0) * 1000)
        usage = extract_usage_stream(chunks)
        logger.info(
            "chat 流式完成 | req_id=%s model=%s chunks=%s latency_ms=%s usage=%s",
            ctx.request_id, model, len(chunks), latency_ms, usage,
        )
        _record_usage(ctx, model, usage, stream=True, estimated=(usage is None), latency_ms=latency_ms, body=body)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/v1/embeddings")
async def embeddings(request: Request, ctx: MeteringContext = Depends(parse_ctx)):
    """OpenAI 兼容 embedding"""
    if not _check_quota(ctx):
        return JSONResponse({"error": "quota_exceeded", "message": "配额超限"}, status_code=429)
    body = await request.json()
    model = body.get("model", "unknown")

    logger.info(
        "embedding 请求 | req_id=%s tenant=%s scene=%s model=%s",
        ctx.request_id, ctx.tenant_id, ctx.scene, model,
    )

    data, status_code, latency_ms = await proxy_nonstream(request, body, ctx)
    usage = extract_usage_embedding(data, body)

    logger.info(
        "embedding 完成 | req_id=%s model=%s status=%s latency_ms=%s usage=%s",
        ctx.request_id, model, status_code, latency_ms, usage,
    )

    _record_usage(ctx, model, usage, stream=False, estimated=("prompt_tokens" not in data.get("usage", {})), latency_ms=latency_ms, body=body)

    return JSONResponse(data, status_code=status_code)


@router.post("/v1/rerank")
async def rerank(request: Request, ctx: MeteringContext = Depends(parse_ctx)):
    """Cohere 风格重排：{model, query, documents[], top_n} → {results:[{index, relevance_score}]}"""
    if not _check_quota(ctx):
        return JSONResponse({"error": "quota_exceeded", "message": "配额超限"}, status_code=429)
    cfg = get_config()
    body = await request.json()
    model = body.get("model") or cfg.LLMGW_RERANK_MODEL
    binding = cfg.LLMGW_RERANK_BINDING

    logger.info(
        "rerank 请求 | req_id=%s tenant=%s scene=%s model=%s binding=%s docs=%d",
        ctx.request_id, ctx.tenant_id, ctx.scene, model, binding,
        len(body.get("documents") or []),
    )

    data, status_code, latency_ms = await proxy_rerank(request, body, ctx)

    # 记录「检索期 rerank 命中」标记，供 kb-service reasoning 回读实测触发情况。
    # 仅对非平台引用重排（scene != ontology_rerank，即 LightRAG 检索期调用）打标；best-effort。
    if status_code == 200 and ctx.scene != "ontology_rerank":
        try:
            import hashlib
            from jonex_core.common.cache import CacheUtil
            q = (body.get("query") or "").strip()
            if q:
                qh = hashlib.sha1(q.encode("utf-8")).hexdigest()[:20]
                await CacheUtil.set(f"yx:rr:hit:{qh}", str(time.time()), expire=120)
        except Exception as e:
            logger.warning("记录 rerank 命中标记失败(忽略) | req_id=%s err=%s", ctx.request_id, e)

    # 计量：ollama-generate 需按 N 次带模板调用估算，传入模板固定开销字符数
    template_overhead = 0
    if binding == "ollama-generate":
        prof = get_profile(cfg.LLMGW_RERANK_PROMPT_PROFILE)
        template_overhead = len(prof.prefix) + len(prof.instruct) + len(prof.suffix)
    usage = extract_usage_rerank(data, body, binding, template_overhead)

    logger.info(
        "rerank 完成 | req_id=%s model=%s status=%s latency_ms=%s usage=%s",
        ctx.request_id, model, status_code, latency_ms, usage,
    )

    _record_usage(ctx, model, usage, stream=False, estimated=True,
                  latency_ms=latency_ms, body=body)

    return JSONResponse(data, status_code=status_code)


@router.get("/metering/usage")
async def metering_usage(
    request: Request,
    tenant_id: str = Query(..., description="租户 ID"),
    start: str = Query(..., description="开始时间 ISO 格式"),
    end: str = Query(..., description="结束时间 ISO 格式"),
    scene: Optional[str] = Query(None, description="按 scene 过滤"),
    ctx: MeteringContext = Depends(parse_ctx),
):
    """计量查询：按 tenant_id + 时间范围聚合 PG 明细"""
    # 按 tenant 过滤防止越权
    if ctx.tenant_id != tenant_id:
        return JSONResponse(
            {"error": "forbidden", "message": "只能查询本租户用量"},
            status_code=403,
        )

    # 查询 PG
    try:
        from jonex_core.common.database import get_db_session
        from sqlalchemy import text

        async with get_db_session() as session:
            filters = [
                "tenant_id = :tenant_id",
                "created_at >= :start",
                "created_at <= :end",
            ]
            params = {"tenant_id": tenant_id, "start": start, "end": end}
            if scene:
                filters.append("scene = :scene")
                params["scene"] = scene

            where = " AND ".join(filters)
            stmt = text(f"""
                SELECT
                    scene, model, kb_id,
                    SUM(call_count) AS call_count,
                    SUM(prompt_tokens) AS total_prompt,
                    SUM(completion_tokens) AS total_completion,
                    SUM(total_tokens) AS total_tokens,
                    AVG(latency_ms) AS avg_latency_ms
                FROM metering.llm_usage_log
                WHERE {where}
                GROUP BY scene, model, kb_id
                ORDER BY total_tokens DESC
            """)
            result = await session.execute(stmt, params)
            rows = result.fetchall()
            return JSONResponse({
                "tenant_id": tenant_id,
                "start": start,
                "end": end,
                "rows": [dict(r._mapping) for r in rows],
            })
    except Exception as e:
        return JSONResponse(
            {"error": "query_failed", "message": str(e)},
            status_code=500,
        )


def _record_usage(
    ctx: MeteringContext,
    model: str,
    usage: dict | None,
    stream: bool,
    estimated: bool,
    latency_ms: int,
    body: dict | None = None,
):
    """统一计量记录入口"""
    prompt_tokens = (usage or {}).get("prompt_tokens", 0) or 0
    completion_tokens = (usage or {}).get("completion_tokens", 0) or 0
    total_tokens = (usage or {}).get("total_tokens", 0) or (prompt_tokens + completion_tokens)

    # 幂等键：显式透传优先，否则按 trace_id + 请求体哈希确定性派生
    request_id = derive_request_id(ctx, body or {})

    rec = UsageRecord(
        ts=time.time(),
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        scene=ctx.scene,
        model=model,
        kb_id=ctx.kb_id,
        doc_id=ctx.doc_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        stream=stream,
        estimated=estimated,
        request_id=request_id,
        latency_ms=latency_ms,
        trace_id=ctx.trace_id,
    )
    recorder = get_recorder()
    import asyncio
    asyncio.create_task(recorder.record(rec))