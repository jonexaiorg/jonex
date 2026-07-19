

import asyncio
import logging
from typing import List, Optional

from jonex_core.common.config import get_config
from jonex_core.common.database import get_db_session
from jonex_core.common.logger import get_logger

from capabilities.platform.models.audit_log import AuditLog

logger = get_logger(__name__)


class AuditLogSink:


    def __init__(self):
        self._queue: Optional[asyncio.Queue] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False



    def start(self):

        if self._running:
            return
        config = get_config()
        self._queue = asyncio.Queue(maxsize=config.AUDIT_QUEUE_MAX_SIZE)
        self._running = True
        self._task = asyncio.create_task(self._consumer_loop())
        logger.info("AuditLogSink started")

    async def stop(self):

        if not self._running:
            return
        self._running = False
        if self._queue is not None:

            await self._queue.put(None)
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("AuditLogSink stop timed out; forcing exit")
            self._task = None
        logger.info("AuditLogSink stopped")

    def put(self, entry: dict):

        if self._queue is None or not self._running:
            logger.warning("AuditLogSink is not running; dropping audit entry")
            return
        try:
            self._queue.put_nowait(entry)
        except asyncio.QueueFull:
            level = entry.get("log_level", "INFO")
            if level in ("ERROR", "WARN"):

                try:
                    self._queue.put_nowait(entry)
                except asyncio.QueueFull:
                    logger.warning("Audit queue full; attempting synchronous write")
                    asyncio.create_task(self._sync_write([entry]))
            else:
                logger.warning("Audit queue full; dropping INFO-level entry: %s", entry.get("action"))

    def put_batch(self, entries: List[dict]):

        for entry in entries:
            self.put(entry)



    async def _consumer_loop(self):

        config = get_config()
        batch_size = config.AUDIT_FLUSH_BATCH_SIZE
        interval = config.AUDIT_FLUSH_INTERVAL_MS / 1000.0

        while self._running:
            try:
                await self._flush_once(batch_size)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("AuditLogSink consumer failed")
            await asyncio.sleep(interval)


        await self._flush_remaining()

    async def _flush_once(self, batch_size: int):

        if self._queue is None:
            return
        batch: List[dict] = []

        while len(batch) < batch_size:
            try:
                item = self._queue.get_nowait()
                if item is None:
                    self._running = False
                    break
                batch.append(item)
            except asyncio.QueueEmpty:
                break
        if not batch:
            return
        await self._sync_write(batch)

    async def _flush_remaining(self):

        if self._queue is None:
            return
        remaining: List[dict] = []
        while True:
            try:
                item = self._queue.get_nowait()
                if item is not None:
                    remaining.append(item)
            except asyncio.QueueEmpty:
                break
        if remaining:
            await self._sync_write(remaining)

    async def _sync_write(self, entries: List[dict]):

        if not entries:
            return
        try:
            async with get_db_session() as session:
                objects = [AuditLog(**e) for e in entries]
                session.add_all(objects)
                await session.commit()
        except Exception:
            logger.exception("Failed to write audit log batch; dropping %d entries", len(entries))




_sink: Optional[AuditLogSink] = None


def get_audit_log_sink() -> AuditLogSink:
    global _sink
    if _sink is None:
        _sink = AuditLogSink()
    return _sink
