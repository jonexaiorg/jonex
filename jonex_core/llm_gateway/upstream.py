


import time
import logging
import asyncio
import math
from typing import AsyncGenerator

import httpx
from fastapi import Request

from jonex_core.common.config import get_config
from jonex_core.llm_gateway.context import MeteringContext
from jonex_core.llm_gateway.rerank_profiles import get_profile

logger = logging.getLogger("llm_gateway")



MODEL_ROUTE_OVERRIDES: dict[str, str] = {}


def _upstream_path(request_path: str) -> str:

    if request_path.endswith("/embeddings"):
        return "/embeddings"
    return "/chat/completions"


def resolve_upstream(path: str, body: dict | None = None) -> tuple[str, str]:

    cfg = get_config()

    if path.endswith("/embeddings"):
        return cfg.LLMGW_UPSTREAM_EMBED_HOST, cfg.LLMGW_UPSTREAM_EMBED_API_KEY


    if body and body.get("model"):
        model = body["model"]
        if model in MODEL_ROUTE_OVERRIDES:
            return MODEL_ROUTE_OVERRIDES[model], cfg.LLMGW_UPSTREAM_LLM_API_KEY

    return cfg.LLMGW_UPSTREAM_LLM_HOST, cfg.LLMGW_UPSTREAM_LLM_API_KEY


def upstream_headers(upstream_key: str, request: Request) -> dict[str, str]:

    headers = {
        "Authorization": f"Bearer {upstream_key}",
        "Content-Type": "application/json",
    }


    ua = request.headers.get("User-Agent")
    if ua:
        headers["User-Agent"] = ua

    return headers


def _maybe_disable_thinking(path: str, body: dict, ctx: MeteringContext) -> None:

    if path.endswith("/embeddings"):
        return
    cfg = get_config()
    if not getattr(cfg, "LLMGW_DISABLE_THINKING_ENABLED", False):
        return
    if not isinstance(body, dict) or "thinking" in body:
        return
    model = body.get("model") or ""
    models = {m.strip() for m in (cfg.LLMGW_DISABLE_THINKING_MODELS or "").split(",") if m.strip()}
    if models and model not in models:
        return
    scenes = {s.strip() for s in (cfg.LLMGW_DISABLE_THINKING_SCENES or "").split(",") if s.strip()}
    if scenes and ctx.scene not in scenes:
        return
    body["thinking"] = {"type": "disabled"}
    logger.info(
        "Injected thinking.disabled | req_id=%s model=%s scene=%s",
        ctx.request_id, model, ctx.scene,
    )


async def proxy_nonstream(
    request: Request,
    body: dict,
    ctx: MeteringContext,
) -> tuple[dict, int, float]:

    host, key = resolve_upstream(request.url.path, body)
    cfg = get_config()

    _maybe_disable_thinking(request.url.path, body, ctx)

    url = f"{host}{_upstream_path(request.url.path)}"
    logger.info("Forwarding to upstream (non-streaming) | req_id=%s url=%s model=%s", ctx.request_id, url, body.get("model"))

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=cfg.LLMGW_REQUEST_TIMEOUT) as cli:
            resp = await cli.post(
                url,
                json=body,
                headers=upstream_headers(key, request),
            )
    except Exception as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.exception("Upstream request exception | req_id=%s url=%s latency_ms=%s err=%s", ctx.request_id, url, latency_ms, e)
        return {"error": {"message": f"upstream request failed: {e}", "type": "upstream_error"}}, 502, latency_ms
    latency_ms = int((time.monotonic() - t0) * 1000)

    try:
        data = resp.json()
    except Exception:
        data = {"error": {"message": f"upstream returned {resp.status_code}", "type": "upstream_error"}}

    if resp.status_code >= 400:



        logger.warning(
            "upstream_error Upstream returned an error | req_id=%s scene=%s model=%s url=%s "
            "status=%s latency_ms=%s retry_after=%s body=%s",
            ctx.request_id, getattr(ctx, "scene", ""), body.get("model"), url,
            resp.status_code, latency_ms, resp.headers.get("Retry-After"), resp.text[:500],
            extra={
                "event": "upstream_error",
                "req_id": ctx.request_id,
                "scene": getattr(ctx, "scene", ""),
                "model": body.get("model"),
                "status": resp.status_code,
                "retry_after": resp.headers.get("Retry-After"),
            },
        )
    return data, resp.status_code, latency_ms


async def proxy_stream(
    request: Request,
    body: dict,
    ctx: MeteringContext,
) -> AsyncGenerator[bytes, None]:

    host, key = resolve_upstream(request.url.path, body)
    cfg = get_config()

    _maybe_disable_thinking(request.url.path, body, ctx)


    body["stream_options"] = {
        **body.get("stream_options", {}),
        "include_usage": True,
    }

    t0 = time.monotonic()
    url = f"{host}{_upstream_path(request.url.path)}"
    logger.info("Forwarding to upstream (streaming) | req_id=%s url=%s model=%s", ctx.request_id, url, body.get("model"))
    try:
        async with httpx.AsyncClient(timeout=cfg.LLMGW_REQUEST_TIMEOUT) as cli:
            async with cli.stream(
                "POST",
                url,
                json=body,
                headers=upstream_headers(key, request),
            ) as resp:
                if resp.status_code >= 400:


                    err_body = (await resp.aread())[:500]
                    logger.warning(
                        "upstream_error Upstream streaming response returned an error | req_id=%s scene=%s model=%s "
                        "url=%s status=%s retry_after=%s body=%s",
                        ctx.request_id, getattr(ctx, "scene", ""), body.get("model"), url,
                        resp.status_code, resp.headers.get("Retry-After"), err_body,
                        extra={
                            "event": "upstream_error",
                            "req_id": ctx.request_id,
                            "scene": getattr(ctx, "scene", ""),
                            "model": body.get("model"),
                            "status": resp.status_code,
                            "retry_after": resp.headers.get("Retry-After"),
                        },
                    )
                async for chunk in resp.aiter_bytes():
                    yield chunk
    except Exception as e:
        logger.exception("Upstream streaming request exception | req_id=%s url=%s err=%s", ctx.request_id, url, e)
        raise









def _aggregate_score(profile, top_logprobs: list[dict]) -> float:

    yes_p = no_p = 0.0
    for t in top_logprobs or []:
        tok = str(t.get("token", "")).strip().lower()
        try:
            p = math.exp(t.get("logprob", -99))
        except (TypeError, ValueError, OverflowError):
            continue
        if tok in profile.yes_set:
            yes_p += p
        elif tok in profile.no_set:
            no_p += p
    return yes_p / (yes_p + no_p) if (yes_p + no_p) > 0 else 0.0


async def _score_one(cli, host, key, model, query, doc, profile) -> float:

    payload = {
        "model": model,
        "prompt": profile.render(query, doc),
        "raw": True,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 1},
        "logprobs": True,
        "top_logprobs": 20,
    }
    resp = await cli.post(
        f"{host}/api/generate", json=payload,
        headers={"Authorization": f"Bearer {key}"},
    )
    resp.raise_for_status()
    data = resp.json()
    lp = data.get("logprobs") or []
    if lp:
        first = lp[0] if isinstance(lp, list) else lp
        return _aggregate_score(profile, first.get("top_logprobs") or [])

    tok = (data.get("response") or "").strip().lower()
    return 1.0 if tok in profile.yes_set else (0.0 if tok in profile.no_set else 0.5)


async def _ollama_rerank_scores(host, key, model, query, docs, cfg) -> list[dict]:

    profile = get_profile(cfg.LLMGW_RERANK_PROMPT_PROFILE)
    sem = asyncio.Semaphore(cfg.LLMGW_RERANK_CONCURRENCY)
    failures = 0

    async def _bounded(cli, i, doc):
        nonlocal failures
        async with sem:
            try:
                s = await _score_one(cli, host, key, model, query, doc, profile)
            except Exception as e:
                failures += 1
                logger.warning("[rerank] doc#%d scoring failed; assigning neutral score 0.5: %s", i, e)
                s = 0.5
            return {"index": i, "relevance_score": s}

    async with httpx.AsyncClient(timeout=cfg.LLMGW_RERANK_TIMEOUT) as cli:
        results = await asyncio.gather(*[_bounded(cli, i, d) for i, d in enumerate(docs)])


    if docs and failures / len(docs) > 0.3:
        raise RuntimeError(f"rerank 失败率过高 {failures}/{len(docs)}，整体降级")
    return results


async def proxy_rerank(
    request: Request,
    body: dict,
    ctx: MeteringContext,
) -> tuple[dict, int, float]:

    cfg = get_config()
    binding = cfg.LLMGW_RERANK_BINDING
    host = cfg.LLMGW_UPSTREAM_RERANK_HOST
    key = cfg.LLMGW_UPSTREAM_RERANK_API_KEY
    model = body.get("model") or cfg.LLMGW_RERANK_MODEL
    query = body.get("query") or ""
    docs = (body.get("documents") or [])[: cfg.LLMGW_RERANK_MAX_DOCS]
    top_n = body.get("top_n")

    t0 = time.monotonic()

    if binding == "cohere":
        url = f"{host}/rerank"
        payload = {"model": model, "query": query, "documents": docs}
        if top_n is not None:
            payload["top_n"] = top_n
        try:
            async with httpx.AsyncClient(timeout=cfg.LLMGW_RERANK_TIMEOUT) as cli:
                resp = await cli.post(
                    url, json=payload,
                    headers={"Authorization": f"Bearer {key}"},
                )
            latency_ms = int((time.monotonic() - t0) * 1000)
            return resp.json(), resp.status_code, latency_ms
        except Exception as e:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.exception("Rerank upstream exception (cohere) | req_id=%s err=%s", ctx.request_id, e)
            return ({"error": {"message": f"rerank upstream failed: {e}"}}, 502, latency_ms)


    try:
        results = await _ollama_rerank_scores(host, key, model, query, docs, cfg)
    except Exception as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.warning("Rerank fully degraded (ollama-generate) | req_id=%s err=%s", ctx.request_id, e)
        return ({"error": {"message": f"rerank degraded: {e}"}}, 502, latency_ms)

    if top_n:
        results = sorted(results, key=lambda r: r["relevance_score"], reverse=True)[:top_n]
    latency_ms = int((time.monotonic() - t0) * 1000)
    return {"results": results}, 200, latency_ms
