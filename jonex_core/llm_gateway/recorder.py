


import asyncio
import hashlib
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

from jonex_core.common.config import get_config

logger = logging.getLogger("llm_gateway")


@dataclass
class UsageRecord:

    ts: float
    tenant_id: str
    user_id: Optional[str]
    scene: str
    model: str
    kb_id: Optional[str]
    doc_id: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    stream: bool
    estimated: bool
    request_id: str
    latency_ms: int
    trace_id: Optional[str] = None


class Recorder:


    def __init__(self, cfg=None):
        self._cfg = cfg or get_config()
        self._buf: list[UsageRecord] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        if self._cfg.LLMGW_METERING_ENABLED:
            self._flush_task = asyncio.create_task(self._periodic_flush())

    async def record(self, rec: UsageRecord):

        if not self._cfg.LLMGW_METERING_ENABLED:
            return
        try:

            asyncio.create_task(self._redis_count(rec))


            async with self._lock:
                self._buf.append(rec)
                if len(self._buf) >= self._cfg.LLMGW_PG_FLUSH_MAX_ROWS:
                    asyncio.create_task(self._flush_pg())


            logger.info(
                "llm_usage | req_id=%s trace=%s tenant=%s scene=%s model=%s "
                "prompt=%s completion=%s total=%s stream=%s estimated=%s latency_ms=%s",
                rec.request_id, rec.trace_id, rec.tenant_id, rec.scene, rec.model,
                rec.prompt_tokens, rec.completion_tokens, rec.total_tokens,
                rec.stream, rec.estimated, rec.latency_ms,
                extra=asdict(rec),
            )
        except Exception:
            logger.exception("Usage metering record failed (exception suppressed; main flow unaffected)")

    async def _redis_count(self, rec: UsageRecord):

        try:
            from jonex_core.common.cache import CacheUtil

            day = datetime.fromtimestamp(rec.ts).strftime("%Y%m%d")


            total_key = f"llm:usage:{rec.tenant_id}:{day}"
            await CacheUtil.hincrby(total_key, "total_tokens", rec.total_tokens)
            await CacheUtil.hincrby(total_key, "prompt_tokens", rec.prompt_tokens)
            await CacheUtil.hincrby(total_key, "completion_tokens", rec.completion_tokens)
            await CacheUtil.expire(total_key, 86400 * 400)


            dim_key = f"llm:usage:{rec.tenant_id}:{rec.scene}:{rec.model}:{day}"
            await CacheUtil.hincrby(dim_key, "total_tokens", rec.total_tokens)
            await CacheUtil.expire(dim_key, 86400 * 400)
        except Exception:
            logger.exception("Redis counter failed (exception suppressed)")

    def _agg_scenes(self) -> set[str]:

        if not self._cfg.LLMGW_EMBED_AGGREGATE_ENABLED:
            return set()
        return {s.strip() for s in (self._cfg.LLMGW_EMBED_AGGREGATE_SCENES or "").split(",") if s.strip()}

    async def _flush_pg(self):

        records = []
        async with self._lock:
            records = self._buf[:]
            self._buf.clear()

        if not records:
            return

        agg_scenes = self._agg_scenes()
        normal: list[UsageRecord] = []
        agg_map: dict[tuple, dict] = {}
        for r in records:
            if r.scene in agg_scenes:
                day = datetime.fromtimestamp(r.ts).strftime("%Y%m%d")
                kb = r.kb_id or "-"
                doc = r.doc_id or "-"
                key = (day, r.tenant_id, r.scene, r.model, kb, doc)
                agg = agg_map.get(key)
                if agg is None:


                    _digest = hashlib.sha1(
                        "|".join(key).encode("utf-8")
                    ).hexdigest()
                    agg = {
                        "request_id": f"emb-agg:{_digest}",
                        "tenant_id": r.tenant_id, "scene": r.scene, "model": r.model,
                        "kb_id": r.kb_id, "doc_id": r.doc_id,
                        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                        "call_count": 0, "is_estimated": False,
                    }
                    agg_map[key] = agg
                agg["prompt_tokens"] += r.prompt_tokens
                agg["completion_tokens"] += r.completion_tokens
                agg["total_tokens"] += r.total_tokens
                agg["call_count"] += 1
                agg["is_estimated"] = agg["is_estimated"] or r.estimated
            else:
                normal.append(r)

        try:
            from jonex_core.common.database import get_db_session
            from sqlalchemy import text

            insert_normal = text("""
                INSERT INTO metering.llm_usage_log
                    (request_id, tenant_id, user_id, scene, model,
                     kb_id, doc_id, prompt_tokens, completion_tokens,
                     total_tokens, latency_ms, is_stream, is_estimated, trace_id)
                VALUES
                    (:request_id, :tenant_id, :user_id, :scene, :model,
                     :kb_id, :doc_id, :prompt_tokens, :completion_tokens,
                     :total_tokens, :latency_ms, :is_stream, :is_estimated, :trace_id)
                ON CONFLICT (request_id) DO NOTHING
            """)

            upsert_agg = text("""
                INSERT INTO metering.llm_usage_log
                    (request_id, tenant_id, scene, model, kb_id, doc_id,
                     prompt_tokens, completion_tokens, total_tokens, call_count,
                     is_estimated, created_at)
                VALUES
                    (:request_id, :tenant_id, :scene, :model, :kb_id, :doc_id,
                     :prompt_tokens, :completion_tokens, :total_tokens, :call_count,
                     :is_estimated, now())
                ON CONFLICT (request_id) DO UPDATE SET
                    prompt_tokens     = metering.llm_usage_log.prompt_tokens     + EXCLUDED.prompt_tokens,
                    completion_tokens = metering.llm_usage_log.completion_tokens + EXCLUDED.completion_tokens,
                    total_tokens      = metering.llm_usage_log.total_tokens      + EXCLUDED.total_tokens,
                    call_count        = metering.llm_usage_log.call_count        + EXCLUDED.call_count,
                    is_estimated      = metering.llm_usage_log.is_estimated      OR EXCLUDED.is_estimated
            """)

            async with get_db_session() as session:
                for r in normal:
                    await session.execute(insert_normal, {
                        "request_id": r.request_id,
                        "tenant_id": r.tenant_id,
                        "user_id": r.user_id,
                        "scene": r.scene,
                        "model": r.model,
                        "kb_id": r.kb_id,
                        "doc_id": r.doc_id,
                        "prompt_tokens": r.prompt_tokens,
                        "completion_tokens": r.completion_tokens,
                        "total_tokens": r.total_tokens,
                        "latency_ms": r.latency_ms,
                        "is_stream": r.stream,
                        "is_estimated": r.estimated,
                        "trace_id": r.trace_id,
                    })
                for agg in agg_map.values():
                    await session.execute(upsert_agg, agg)
                await session.commit()
            logger.info("PG usage batch write completed | details=%s aggregates=%s", len(normal), len(agg_map))
        except Exception:
            logger.exception("PG batch write failed (exception suppressed)")

    async def _periodic_flush(self):

        while True:
            await asyncio.sleep(self._cfg.LLMGW_PG_FLUSH_MAX_SECONDS)
            try:
                async with self._lock:
                    if self._buf:
                        asyncio.create_task(self._flush_pg())
            except Exception:
                pass

    async def close(self):

        if self._flush_task:
            self._flush_task.cancel()
        await self._flush_pg()



_recorder: Optional[Recorder] = None


def get_recorder() -> Recorder:
    global _recorder
    if _recorder is None:
        _recorder = Recorder()
    return _recorder