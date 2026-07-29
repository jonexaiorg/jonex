"""AuditLogSink — 非阻塞异步审计日志写入器

单例模式，用于 platform 进程内异步批量落库。
参考 `jonex_core/llm_gateway/recorder.py` 的 Recorder 模式。
"""

import asyncio
import logging
from typing import List, Optional

from jonex_core.common.config import get_config
from jonex_core.common.database import get_db_session
from jonex_core.common.logger import get_logger

from capabilities.platform.models.audit_log import AuditLog

logger = get_logger(__name__)


class AuditLogSink:
    """异步审计日志写入器

    用法：
        sink = AuditLogSink()
        sink.start()
        sink.put(entry)
        sink.put_batch(entries)
        sink.stop()  # 等待 flush 后退出
    """

    def __init__(self):
        self._queue: Optional[asyncio.Queue] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False

    # ---- 生命周期 ----

    def start(self):
        """启动后台消费协程（在 platform 服务 startup 时调用）"""
        if self._running:
            return
        config = get_config()
        self._queue = asyncio.Queue(maxsize=config.AUDIT_QUEUE_MAX_SIZE)
        self._running = True
        self._task = asyncio.create_task(self._consumer_loop())
        logger.info("AuditLogSink 已启动")

    async def stop(self):
        """停止后台消费协程，flush 剩余队列后退出"""
        if not self._running:
            return
        self._running = False
        if self._queue is not None:
            # 放入哨兵让 consumer loop 退出
            await self._queue.put(None)
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("AuditLogSink 停止超时，强制退出")
            self._task = None
        logger.info("AuditLogSink 已停止")

    def put(self, entry: dict):
        """投递单条审计条目到队列（非阻塞，满时按级别降级）"""
        if self._queue is None or not self._running:
            logger.warning("AuditLogSink 未启动，丢弃审计条目")
            return
        try:
            self._queue.put_nowait(entry)
        except asyncio.QueueFull:
            level = entry.get("log_level", "INFO")
            if level in ("ERROR", "WARN"):
                # 关键级别：阻塞短超时后同步兜底
                try:
                    self._queue.put_nowait(entry)
                except asyncio.QueueFull:
                    logger.warning("审计队列满，尝试同步直写")
                    asyncio.create_task(self._sync_write([entry]))
            else:
                logger.warning("审计队列满，丢弃 INFO 级条目: %s", entry.get("action"))

    def put_batch(self, entries: List[dict]):
        """批量投递（逐个 put，由背压策略处理）"""
        for entry in entries:
            self.put(entry)

    # ---- 后台消费 ----

    async def _consumer_loop(self):
        """后台消费循环：批量取 → add_all 落库"""
        config = get_config()
        batch_size = config.AUDIT_FLUSH_BATCH_SIZE
        interval = config.AUDIT_FLUSH_INTERVAL_MS / 1000.0

        while self._running:
            try:
                await self._flush_once(batch_size)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("AuditLogSink 消费异常")
            await asyncio.sleep(interval)

        # 最后 flush 剩余
        await self._flush_remaining()

    async def _flush_once(self, batch_size: int):
        """一次批量 flush"""
        if self._queue is None:
            return
        batch: List[dict] = []
        # 尽量取满一批
        while len(batch) < batch_size:
            try:
                item = self._queue.get_nowait()
                if item is None:  # 哨兵
                    self._running = False
                    break
                batch.append(item)
            except asyncio.QueueEmpty:
                break
        if not batch:
            return
        await self._sync_write(batch)

    async def _flush_remaining(self):
        """flush 队列中剩余的所有条目"""
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
        """同步写入数据库（批量 add_all）"""
        if not entries:
            return
        try:
            async with get_db_session() as session:
                objects = [AuditLog(**e) for e in entries]
                session.add_all(objects)
                await session.commit()
        except Exception:
            logger.exception("审计日志批量写入失败，丢弃 %d 条", len(entries))


# ---- 全局单例 ----

_sink: Optional[AuditLogSink] = None


def get_audit_log_sink() -> AuditLogSink:
    global _sink
    if _sink is None:
        _sink = AuditLogSink()
    return _sink
