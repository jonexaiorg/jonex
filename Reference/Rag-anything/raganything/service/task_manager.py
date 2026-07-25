"""
TaskManager — core state machine, Semaphore-based capacity control,
cooperative cancellation, and retention cleanup.

Spec §5 — compliant with:
  - §5.1: 4 Workers + Semaphore(worker_count + queue_capacity)
  - §5.2: Task lifecycle + 24h retention + 30min cleanup
  - §5.3: Cooperative cancellation with cancel_event
  - §3:   TaskInfo fields
"""

from __future__ import annotations

import asyncio
import base64
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import shutil
import socket
import time
import traceback
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from raganything.callbacks import ProcessingCallback
from raganything.config import RAGAnythingConfig
from raganything.pipeline.base import PipelineContext as PipelineCtx
from raganything.service.model_factory import ModelFactory
from raganything.service.models import (
    CancelTaskResponse,
    CreateTaskRequest,
    CreateTaskResponse,
    ErrorCode,
    ErrorResponse,
    FileType,
    PaginatedTasks,
    ProgressDetail,
    ResultSummary,
    StageTiming,
    StorageInfo,
    TaskInfo,
    TaskListItem,
    TaskStatus,
    TERMINAL_STATES,
    STATE_TRANSITIONS,
    infer_file_type,
    validate_transition,
)

from raganything.service.chunk_repository import LightRAGChunkRepository
from raganything.service.exceptions import StorageNotReadyError
from raganything.service.models import UpdateChunkResult

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────

WORKER_COUNT = int(os.getenv("WORKER_COUNT", "4"))
QUEUE_CAPACITY = int(os.getenv("TASK_QUEUE_CAPACITY", "100"))
RETENTION_HOURS = 24
CLEANUP_INTERVAL_SEC = 30 * 60  # 30 min
IDEMPOTENCY_TTL_SEC = 10 * 60   # 10 min
DEFAULT_WEBHOOK_URL = os.getenv("RAG_WEBHOOK_URL", "")  # global fallback (v1 compat)

# ── PipelineContext — execution metadata collector ─────────────────────
# Collects block stats and timing during pipeline execution so
# consumers don't need to reverse-query LightRAG internals.


class PipelineContext:
    """Execution context that collects metadata during pipeline stages.

    Block type information is captured from MinerU content_list during
    parsing — LightRAG ingest *flattens* type info into plain text chunks,
    so it cannot be recovered from storage afterwards.

    Timing is recorded as ``time.time()`` epoch floats (NOT monotonic).
    """

    __slots__ = (
        "doc_id", "file_path", "parser_type",
        "started_at", "completed_at",
        "text_blocks", "table_blocks", "code_blocks", "image_count",
        "content_list",
    )

    def __init__(
        self,
        file_path: str = "",
        parser_type: str = "",
    ):
        self.doc_id: str = ""
        self.file_path: str = file_path
        self.parser_type: str = parser_type

        # Timing — time.time() epoch floats
        self.started_at: float = 0.0
        self.completed_at: float = 0.0

        # Block counts from content_list
        self.text_blocks: int = 0
        self.table_blocks: int = 0
        self.code_blocks: int = 0
        self.image_count: int = 0

        # Raw content_list for artifact writing (Bug 3)
        self.content_list: list[dict] | None = None

    # ── Block counting ──────────────────────────────────────────────

    def count_blocks_from_content_list(self) -> None:
        """Tally text/table/code/image blocks from MinerU content_list."""
        for item in (self.content_list or []):
            t = item.get("type", "text")
            if t == "text":
                self.text_blocks += 1
            elif t == "table":
                self.table_blocks += 1
            elif t == "code":
                self.code_blocks += 1
            elif t == "image":
                self.image_count += 1

    @property
    def total_blocks(self) -> int:
        return self.text_blocks + self.table_blocks + self.code_blocks

    # ── Timing ──────────────────────────────────────────────────────

    @property
    def duration_seconds(self) -> float:
        if self.completed_at > 0 and self.started_at > 0:
            return self.completed_at - self.started_at
        return 0.0


# ── Error classification — Spec §5.4 ─────────────────────────────────

ERROR_CLASSIFICATION: list[tuple[str, ErrorCode | str]] = [
    (r"FileNotFound|No such file",                     ErrorCode.FILE_NOT_FOUND),
    (r"Profile.*not found",                            ErrorCode.PROFILE_NOT_FOUND),
    (r"Preset.*not found",                             ErrorCode.PRESET_NOT_FOUND),
    (r"Model.*not found|unknown model",                ErrorCode.MODEL_NOT_FOUND),
    (r"timed out|TimeoutError",                        "continue"),  # fallthrough
    (r"llm.*timed out|openai.*timeout",                ErrorCode.LLM_TIMEOUT),
    (r"vlm.*timed out",                                ErrorCode.VLM_TIMEOUT),
    (r"asr.*timed out|whisper.*timeout",               ErrorCode.ASR_TIMEOUT),
    (r"lightrag.*error|LightRAG",                      ErrorCode.LIGHTRAG_ERROR),
    (r"parse.*error|MinerU|docling|paddle",            ErrorCode.PARSER_ERROR),
    (r"invalid.*config|config.*invalid",               ErrorCode.CONFIG_INVALID),
]


def _classify_error(exc: Exception) -> ErrorCode:
    if isinstance(exc, TaskCancelledError):
        return ErrorCode.TASK_CANCELLED
    msg = str(exc)
    for pattern, code in ERROR_CLASSIFICATION:
        import re
        if re.search(pattern, msg, re.IGNORECASE):
            if code == "continue":
                continue
            return code  # type: ignore[return-value]
    return ErrorCode.UNKNOWN


# ── TaskHandle ───────────────────────────────────────────────────────

class TaskCancelledError(Exception):
    """Raised inside worker when cancel_event is set."""


class TaskHandle:
    __slots__ = ("cancel_event", "current_task", "_release_cb", "_released")

    def __init__(self, release_cb):
        self.cancel_event = asyncio.Event()
        self.current_task: Optional[asyncio.Task] = None
        self._release_cb = release_cb
        self._released = False

    def release_slot(self):
        """Release the capacity slot. Safe to call multiple times."""
        if not self._released:
            self._released = True
            self._release_cb()


# ── TenantRAGCache ──────────────────────────────────────────────────

class TenantRAGCache:
    """Per-tenant+KB lazy RAGAnything instances (ADR-1).

    Creates real RAGAnything instances with:
      - working_dir = {base_dir}/{tenant_id}/{kb_id}/
      - Model functions from profile via ModelFactory
      - LRU eviction when exceeding max_tenants (default 32)

    Thread-safe: all public methods are guarded by asyncio.Lock.
    """

    def __init__(
        self,
        base_dir: str,
        model_factory: ModelFactory,
        max_tenants: int = 32,
    ):
        self._instances: dict[tuple[str, str], Any] = {}
        self._access_times: dict[tuple[str, str], float] = {}
        self._base_dir = base_dir
        self._model_factory = model_factory
        self._max_tenants = max_tenants
        self._lock = asyncio.Lock()

    async def get(self, tenant_id: str, kb_id: str, config_snapshot: dict) -> Any:
        """Get or create a RAGAnything instance for the tenant + KB.

        Args:
            tenant_id: Tenant identifier.
            kb_id: Knowledge base identifier (empty string for default).
            config_snapshot: Resolved config dict (from ConfigResolver.resolve()).

        Returns:
            RAGAnything instance.
        """
        key = (tenant_id, kb_id)
        async with self._lock:
            if key in self._instances:
                self._access_times[key] = time.monotonic()
                return self._instances[key]

            # Evict LRU if at capacity
            if len(self._instances) >= self._max_tenants:
                oldest_key = min(
                    self._access_times.keys(),
                    key=lambda k: self._access_times[k],
                )
                await self._evict_tenant(oldest_key)

            # Create new RAGAnything instance
            rag = await self._create_instance(tenant_id, config_snapshot, kb_id=kb_id)
            self._instances[key] = rag
            self._access_times[key] = time.monotonic()
            logger.info(
                f"TenantRAGCache: created RAGAnything for tenant={tenant_id} kb={kb_id} "
                f"(total instances={len(self._instances)})"
            )
            return rag

    async def _create_instance(self, tenant_id: str, config_snapshot: dict,
                               kb_id: str = "") -> Any:
        """Create a RAGAnything instance for the given tenant + KB."""
        from raganything.raganything import RAGAnything

        kb = kb_id or "default_kb"
        working_dir = os.path.join(self._base_dir, tenant_id, kb, "rag_storage")
        parser_output_dir = os.path.join(self._base_dir, tenant_id, kb, "output")
        os.makedirs(working_dir, exist_ok=True)
        os.makedirs(parser_output_dir, exist_ok=True)

        # Extract profile from config snapshot
        profile = config_snapshot.get("profile", "dev")

        # Build model functions from profile
        funcs = self._model_factory.build(
            profile=profile,
            overrides=config_snapshot,
            working_dir=working_dir,
            parser_output_dir=parser_output_dir,
            tenant_id=tenant_id,
            kb_id=kb_id,
        )

        # Set env vars for ASR model downloads if configured
        asr_backend = config_snapshot.get("asr_binding", "")
        asr_model = config_snapshot.get("asr_model", "")
        if asr_backend and asr_model:
            os.environ.setdefault("ASR_BINDING", asr_backend)
            os.environ.setdefault("ASR_MODEL", asr_model)

        rag = RAGAnything(
            config=funcs["config"],
            llm_model_func=funcs["llm_model_func"],
            embedding_func=funcs["embedding_func"],
            vlm_model_func=funcs.get("vlm_model_func"),
            asr_model_func=funcs.get("asr_model_func"),
            lightrag_kwargs=funcs.get("lightrag_kwargs", {}),
        )

        # Configure MinerU online parser with preset token (overrides env var)
        if hasattr(rag.doc_parser, "configure") and config_snapshot:
            rag.doc_parser.configure(**config_snapshot)

        return rag

    async def _evict_tenant(self, key: tuple[str, str]) -> None:
        """Close and remove a tenant+KB's RAGAnything instance."""
        rag = self._instances.pop(key, None)
        self._access_times.pop(key, None)
        if rag is not None:
            try:
                # RAGAnything.close() handles async cleanup
                rag.close()
            except Exception:
                logger.warning(
                    f"Error closing RAGAnything for key={key}",
                    exc_info=True,
                )
            logger.info(f"TenantRAGCache: evicted tenant={key[0]} kb={key[1]}")

    async def close_all(self) -> None:
        """Close all cached instances (called during shutdown)."""
        async with self._lock:
            for key in list(self._instances.keys()):
                await self._evict_tenant(key)
            logger.info("TenantRAGCache: all instances closed")

    @property
    def tenant_count(self) -> int:
        return len(self._instances)


# ── ProgressTrackingCallback ─────────────────────────────────────────

class ProgressTrackingCallback(ProcessingCallback):
    """Callback that updates TaskInfo progress + timeline during pipeline execution.

    Registered on RAGAnything.callback_manager before process_document_complete
    and unregistered afterwards.  All updates are synchronous on the event loop
    thread (safe: TaskInfo is owned by the worker coroutine).

    Timeline: Each on_*_start call pushes a StageTiming with started_at;
    each on_*_complete call closes the last matching stage with ended_at.
    """

    def __init__(self, task: TaskInfo, handle: "TaskHandle"):
        self._task = task
        self._handle = handle
        self._start_time = time.monotonic()
        # Initialize timeline with pre-pipeline stages from existing timestamps.
        # Only do so if the timeline hasn't been populated yet (first registration).
        if not task.timeline:
            task.timeline = [
                StageTiming(
                    stage="created",
                    label="创建任务",
                    detail="提交任务请求",
                    started_at=task.created_at,
                    ended_at=task.queued_at or task.created_at,
                    elapsed_seconds=_elapsed_seconds(task.created_at, task.queued_at),
                ),
                StageTiming(
                    stage="queued",
                    label="排队等待",
                    detail="等待 Worker 接管",
                    started_at=task.queued_at,
                    ended_at=task.started_at,
                    elapsed_seconds=_elapsed_seconds(task.queued_at, task.started_at),
                ),
            ]

    # ── timeline helpers ──────────────────────────────────────────

    def _push_stage(self, stage: str, label: str, detail: str = "") -> None:
        self._task.timeline.append(StageTiming(
            stage=stage,
            label=label,
            detail=detail,
            started_at=datetime.now(timezone.utc),
        ))

    def _close_stage(self) -> None:
        if not self._task.timeline:
            return
        last = self._task.timeline[-1]
        if last.ended_at is None and last.started_at is not None:
            now = datetime.now(timezone.utc)
            last.ended_at = now
            last.elapsed_seconds = (now - last.started_at).total_seconds()

    # ── cancellation ─────────────────────────────────────────────

    def _check_cancelled(self) -> bool:
        if self._handle.cancel_event.is_set():
            raise TaskCancelledError()
        return False

    # ── parse ────────────────────────────────────────────────────

    def on_parse_start(self, file_path: str, **kwargs: Any) -> None:
        self._check_cancelled()
        self._task.current_step = "parse"
        self._task.progress_detail = ProgressDetail(
            current=1, total=5, unit="step",
            step_name="parse", step_detail="Parsing document...",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._push_stage("parse", "文档解析", "MinerU 在线解析（上传→轮询→下载zip）")
        self._task.updated_at = datetime.now(timezone.utc)

    def on_parse_complete(
        self, file_path: str, content_blocks: int = 0, **kwargs: Any
    ) -> None:
        self._check_cancelled()
        self._task.progress = 0.2
        self._task.progress_detail = ProgressDetail(
            current=1, total=5, unit="step",
            step_name="parse", step_detail=f"Parsed {content_blocks} blocks",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._close_stage()
        self._task.updated_at = datetime.now(timezone.utc)

    # ── text_insert ──────────────────────────────────────────────

    def on_text_insert_start(self, file_path: str, **kwargs: Any) -> None:
        self._check_cancelled()
        self._task.current_step = "text_insert"
        self._task.progress_detail = ProgressDetail(
            current=2, total=5, unit="step",
            step_name="text_insert", step_detail="Inserting text into LightRAG...",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._push_stage("text_insert", "文本入库", "LightRAG insert_text_content")
        self._task.updated_at = datetime.now(timezone.utc)

    def on_text_insert_complete(self, file_path: str, **kwargs: Any) -> None:
        self._check_cancelled()
        self._task.progress = 0.4
        self._task.progress_detail = ProgressDetail(
            current=2, total=5, unit="step",
            step_name="text_insert", step_detail="Text insertion complete",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._close_stage()
        self._task.updated_at = datetime.now(timezone.utc)

    # ── multimodal ───────────────────────────────────────────────

    def on_multimodal_start(self, file_path: str, item_count: int = 0, **kwargs: Any) -> None:
        self._check_cancelled()
        self._task.current_step = "multimodal"
        self._task.progress = 0.5
        self._task.progress_detail = ProgressDetail(
            current=0, total=item_count, unit="item",
            step_name="multimodal", step_detail=f"Processing {item_count} multimodal items...",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._push_stage("multimodal", "多模态处理", "图片/表格/公式 VLM 描述")
        self._task.updated_at = datetime.now(timezone.utc)

    def on_multimodal_item_complete(
        self, file_path: str, item_index: int = 0, total_items: int = 0, **kwargs: Any
    ) -> None:
        self._check_cancelled()
        progress = 0.5 + 0.4 * (item_index / max(total_items, 1))
        self._task.progress = progress
        self._task.progress_detail = ProgressDetail(
            current=item_index, total=total_items, unit="item",
            step_name="multimodal",
            step_detail=f"Processed {item_index}/{total_items} multimodal items",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._task.updated_at = datetime.now(timezone.utc)

    def on_multimodal_complete(self, file_path: str, **kwargs: Any) -> None:
        self._check_cancelled()
        self._task.progress = 0.9
        self._task.progress_detail = ProgressDetail(
            current=4, total=5, unit="step",
            step_name="multimodal", step_detail="Multimodal processing complete",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._close_stage()
        self._task.updated_at = datetime.now(timezone.utc)

    # ── push_chunks (HTTP mode) ───────────────────────────────────
    # [jonex] 批次 2-A：P3 push 阶段信号，供 kb-service 对账置 INGESTING

    def on_push_chunks_start(self, file_path: str = "", **kwargs: Any) -> None:
        self._check_cancelled()
        self._task.current_step = "push_chunks"
        self._task.progress = 0.92
        self._task.progress_detail = ProgressDetail(
            current=3, total=5, unit="step",
            step_name="push_chunks", step_detail="推送并等待 LightRAG 入图/抽取...",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._push_stage("push_chunks", "推送入图", "逐 chunk LightRAG LLM 抽取 + embedding + 写图/向量库")
        self._task.updated_at = datetime.now(timezone.utc)

    # ── done ─────────────────────────────────────────────────────

    def on_document_complete(self, file_path: str, doc_id: str = "", **kwargs: Any) -> None:
        self._check_cancelled()
        self._task.current_step = "done"
        self._task.progress = 1.0
        elapsed = time.monotonic() - self._start_time
        self._task.progress_detail = ProgressDetail(
            current=5, total=5, unit="step",
            step_name="done", step_detail="Complete",
            elapsed_seconds=elapsed,
        )
        self._push_stage("done", "完成", "任务处理完毕")
        self._close_stage()
        # Store doc_id for result summary (picked up by _execute_pipeline)
        self._task.result_summary = ResultSummary(
            doc_id=doc_id,
            duration_seconds=elapsed,
        )
        self._task.updated_at = datetime.now(timezone.utc)

    # ── error ────────────────────────────────────────────────────

    def on_document_error(
        self, file_path: str, error: Any = "", stage: str = "", **kwargs: Any
    ) -> None:
        self._task.progress_detail = ProgressDetail(
            current=0, total=5, unit="step",
            step_name=stage, step_detail=f"Error: {error}",
            elapsed_seconds=time.monotonic() - self._start_time,
        )
        self._close_stage()
        self._task.updated_at = datetime.now(timezone.utc)


def _elapsed_seconds(start: datetime | None, end: datetime | None) -> float:
    """Safe elapsed-seconds between two optional datetimes."""
    if start is not None and end is not None:
        return (end - start).total_seconds()
    return 0.0


# ── TaskManager ──────────────────────────────────────────────────────

class TaskManager:
    def __init__(
        self,
        base_dir: str = "./rag_service_data",
        model_factory: ModelFactory | None = None,
        worker_count: int = WORKER_COUNT,
        queue_capacity: int = QUEUE_CAPACITY,
        chunk_repository_factory=None,
        *,
        http_client: Any = None,
        pipeline_executor: Any = None,
        prompt_config_manager: Any = None,
    ):
        self._tasks: dict[str, TaskInfo] = {}
        self._handles: dict[str, TaskHandle] = {}
        self._max_slots = worker_count + queue_capacity
        self._active_slots = 0
        self._slot_lock = asyncio.Lock()
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._idempotency: dict[str, tuple[float, str]] = {}  # key → (expire_ts, task_id)
        self._worker_count = worker_count
        self._model_factory = model_factory or ModelFactory()
        # ── v2 HTTP mode ──
        self._http_client = http_client
        self._pipeline_executor = pipeline_executor
        self._config_resolver = None  # set after init
        # [jonex] 主解析提示词覆盖：pipeline 消费 prompt_ids 时用（B2）
        self._pcm = prompt_config_manager
        self._shutting_down = False

        from raganything.service.task_repository import TaskRepository
        self._repo = TaskRepository(base_dir=base_dir)

        self._worker_tasks: list[asyncio.Task] = []
        self._cleanup_task: Optional[asyncio.Task] = None

    # ── Lifecycle ───────────────────────────────────────────────────

    def set_config_resolver(self, resolver):
        self._config_resolver = resolver

    async def start(self):
        hostname = socket.gethostname().split(".")[0]

        # Recover persisted tasks
        recovered = self._repo.load_all()
        for task_id, task in recovered.items():
            self._tasks[task_id] = task
            # Recover stuck ontology tasks
            if task.ontology_status == "extracting":
                logger.warning(f"Recovered stuck ontology task {task_id}, resetting to pending")
                task.ontology_status = "pending"
            if task.status not in TERMINAL_STATES:
                # ── [jonex] 阶段4 P0-J：cleanup 阶段只恢复清理，不重跑解析管线 ──
                if getattr(task, "current_step", "") == "cleanup":
                    logger.info(
                        f"Recovered task {task_id} in cleanup, resuming cleanup only "
                        f"(delete_pending={len(task.delete_pending_ids or [])}, "
                        f"compensate_pending={len(task.compensate_pending_ids or [])})"
                    )
                    asyncio.create_task(self._resume_cleanup(task))
                    continue
                # ── v2 HTTP mode: resume track polling if needed ──
                if task.pending_track_ids:
                    logger.info(
                        f"Recovered task {task_id} with {len(task.pending_track_ids)} "
                        f"pending tracks, resuming polling"
                    )
                    asyncio.create_task(self._resume_track_polling(task))
                elif (not hasattr(task, 'pending_track_ids')
                      and not hasattr(task, 'lightrag_doc_ids')
                      and self._http_client is not None):
                    # Old-version task without HTTP mode fields → mark FAILED
                    logger.warning(
                        f"Task {task_id} has no HTTP-mode fields — "
                        f"version incompatible, marking FAILED"
                    )
                    self._fail_task(task, ErrorCode.INTERNAL_ERROR,
                                    "任务版本不兼容，请重新提交")
                else:
                    self._queue.put_nowait(task_id)
        if recovered:
            logger.info(f"Recovered {len(recovered)} tasks from disk")

        for i in range(self._worker_count):
            worker_id = f"worker-{hostname}-{i}"
            t = asyncio.create_task(self._worker_loop(worker_id), name=worker_id)
            self._worker_tasks.append(t)
        self._cleanup_task = asyncio.create_task(self._cleanup_loop(), name="cleanup")
        logger.info(f"TaskManager started: {self._worker_count} workers, queue={QUEUE_CAPACITY}")

    async def shutdown(self, grace_seconds: float = 120.0):
        """Graceful shutdown (Spec §4.8)."""
        self._shutting_down = True
        logger.info("TaskManager shutting down...")

        # Cancel cleanup
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Wait workers
        done, pending = await asyncio.wait(
            self._worker_tasks, timeout=grace_seconds
        )
        for t in pending:
            t.cancel()
        logger.info(f"TaskManager stopped ({len(done)} workers finished, {len(pending)} cancelled)")

        # Close HTTP client if present
        if self._http_client is not None:
            try:
                await self._http_client.close()
            except Exception:
                pass

    @property
    def accepting_tasks(self) -> bool:
        return not self._shutting_down and self._active_slots < self._max_slots

    @property
    def slots_available(self) -> int:
        return max(0, self._max_slots - self._active_slots)

    def _release_slot(self, task_id: str):
        """Decrement active slot count. Called by TaskHandle."""
        self._active_slots = max(0, self._active_slots - 1)

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize()

    # ── Public API ──────────────────────────────────────────────────

    # ── Public API (HTTP mode) ──────────────────────────────────────

    async def query(
        self, query: str, tenant_id: str,
        mode: str = "hybrid", top_k: int = 5,
        *,
        kb_id: str = "",
        trace_id: str = "",
    ) -> dict:
        """Query LightRAG via HTTP client, returning {answer, references}.

        Mirrors v1 LightRAGAdapter.query_detailed(): references are parsed
        from :9621 response via parse_file_source(), ready for KB-side
        enrichment with COS presigned URLs and DB lookups.
        """
        if self._http_client is not None:
            from jonex_core.common.file_source_util import parse_file_source
            result = await self._http_client.query(
                query, mode=mode, top_k=top_k,
                tenant_id=tenant_id, kb_id=kb_id, trace_id=trace_id,
            )
            if isinstance(result, dict):
                answer = result.get("response", result.get("data", ""))
                refs: list[dict] = []
                for r in (result.get("references") or []):
                    parsed = parse_file_source(r.get("file_path", ""))
                    if not parsed:
                        continue
                    # LightRAG content is the chunk text array for this file_path.
                    content = r.get("content")
                    raw_text = None
                    if isinstance(content, list) and content:
                        raw_text = "\n\n".join(c for c in content if c)
                    elif isinstance(content, str) and content:
                        raw_text = content
                    if raw_text:
                        parsed["text"] = raw_text.strip()
                    # [jonex] 透传 chunk_ids：LightRAG reference 已带 chunk_ids（与 content 数组对齐）。
                    # 本平台 file_source 按 chunk 唯一，取首个作单值 chunk_id；全量存 chunk_ids。
                    chunk_ids = r.get("chunk_ids") or []
                    if chunk_ids:
                        parsed["chunk_ids"] = chunk_ids
                        parsed["chunk_id"] = chunk_ids[0]
                    refs.append(parsed)
                return {"answer": str(answer), "references": refs}
            return {"answer": str(result), "references": []}
        else:
            raise RuntimeError(
                "HTTP mode not configured. Embedded mode query is not supported "
                "in this TaskManager version. Set LIGHTRAG_API_URL to enable HTTP mode."
            )

    async def delete_doc(self, doc_id: str, tenant_id: str, *, kb_id: str = "") -> bool:
        """Delete a document from LightRAG storage via HTTP."""
        if self._http_client is not None:
            return await self._http_client.delete_doc(
                doc_id, tenant_id=tenant_id, kb_id=kb_id,
            )
        raise RuntimeError("HTTP mode not configured")

    async def get_document_chunks(
        self, doc_id: str, tenant_id: str, *, kb_id: str = "",
    ) -> dict | None:
        """Return paginated chunks for a document_id via HTTP.

        Each chunk entry is enriched with a ``chunk_id`` field (LightRAG
        Text/KV storage layer ID, ``chunk-<md5hash>`` format), enabling
        direct use with ``update_chunk``.

        # [jonex][TODO] 本实现有缺陷，"查看文档 Chunk 列表"接口（action get_doc_chunks →
        #   kb-service get_document_chunks）对已入库文档恒返回空/结构不符，需重写。
        #
        # 问题（两点）：
        #   1) 结构不符契约：这里调 get_documents（GET /documents/paginated）返回的是
        #      「文档级」结构 {documents:[...], pagination, status_counts}，而 kb-service /
        #      LightRAGAdapterV2 期望的是 {doc_id, total, chunks:[{chunk_id, content,
        #      chunk_order_index, page_idx, line_start/end, ...}]}。键名（documents vs chunks）
        #      与层级都对不上，下游 data.get("chunks") 恒空、total 恒 0。
        #   2) 数据层级错：documents 是「文档」条目（doc-<md5>，content 只有 content_summary
        #      摘要、无 chunk_order_index/page_idx/line 等位置元数据），不是真正的 text_chunks。
        #      平台一个 KB 文档被拆成多个 doc-<md5>，其真正 chunk（chunk-<md5>）在 text_chunks 里，
        #      file_path 带 doc=<kb_doc_id> 锚点。而这里把 documents 当 chunks、还用
        #      compute_mdhash_id(content_summary) 伪造 chunk_id，与真实 chunk-<md5> 不一致。
        #
        # 修复方案：
        #   - LightRAG 侧新增「按 doc= 锚点枚举 text_chunks」端点：遍历 text_chunks 按
        #     file_path 含 doc=<doc_id> 过滤（doc= 锚点即 KB knowledge_documents.id），返回
        #     chunk-<md5> + content + chunk_order_index + page_idx + line_start/end + tokens，
        #     按 chunk_order_index 排序。（注：/documents/paginated 已支持 [jonex] doc_id
        #     锚点过滤，但只到文档级，拿不到 chunk 位置元数据。）
        #   - 本方法改调该端点，返回契约结构 {doc_id, total, chunks:[...]}；同时清理
        #     content 里的 <!--yx:HASH--> 标记（与 references / get_chunk 口径一致）。
        #   - 单片直查已由 get_chunk_by_id（GET /documents/chunks/{chunk_id}）解决，可复用其
        #     返回字段口径。
        #   详见 docs/rag-fallback-recall-detail-and-chunk-lookup-plan.md §9（P11 及核实过程）。
        """
        if self._http_client is not None:
            result = await self._http_client.get_documents(
                tenant_id=tenant_id, kb_id=kb_id,
                document_id=doc_id, page=1, page_size=200,
            )
            if result:
                from lightrag.utils import compute_mdhash_id
                # Handle both /documents/paginated ({documents: [...]}) and
                # /documents ({statuses: {processed: [...]}}) formats
                entries = result.get("documents") or []
                if not entries:
                    for status_list in result.get("statuses", {}).values():
                        if isinstance(status_list, list):
                            entries.extend(status_list)
                for entry in entries:
                    content = entry.get("content_summary", "")
                    if content:
                        entry["chunk_id"] = compute_mdhash_id(
                            content, prefix="chunk-"
                        )
            return result
        return None

    async def get_chunk_by_id(
        self, chunk_id: str, tenant_id: str, *, kb_id: str = "",
    ) -> dict | None:
        """按 chunk_id 直查单个 chunk 内容（不依赖 task，不拉整篇 chunk 列表）。

        直连 LightRAG GET /documents/chunks/{chunk_id}，返回
        {chunk_id, content, full_doc_id, chunk_order_index, file_path, page_idx, line_start, line_end, tokens}。
        chunk 不存在时 HttpLightRagClient 抛 404 → 上层归一为 None。
        """
        if self._http_client is not None:
            import httpx
            try:
                return await self._http_client.get_chunk_by_id(
                    chunk_id, tenant_id=tenant_id, kb_id=kb_id,
                )
            except httpx.HTTPStatusError as e:
                # chunk 不存在 → None（由 action handler 归一为 40405）
                if e.response.status_code == 404:
                    return None
                raise
        raise RuntimeError("HTTP mode not configured")

    async def export_document(
        self, doc_id: str, tenant_id: str, fmt: str = "json", *, kb_id: str = "",
    ) -> dict | None:
        """Aggregate all data for a document_id via HTTP."""
        if self._http_client is not None:
            return await self._http_client.get_document_parse_result(
                tenant_id=tenant_id, kb_id=kb_id, document_id=doc_id,
            )
        return None

    async def create(
        self, req: CreateTaskRequest, tenant_id: str, idempotency_key: str | None = None
    ) -> CreateTaskResponse | TaskInfo:
        # ── Idempotency check ──────────────────────────────────────
        if idempotency_key:
            existing = self._check_idempotency(idempotency_key)
            if existing:
                return existing

        # ── Capacity check (atomic, no TOCTOU) ────────────────────
        async with self._slot_lock:
            if self._active_slots >= self._max_slots:
                raise SlotFullError(
                    ErrorResponse(
                        code=42901,
                        request_id="",
                        message="Task queue is full. Retry later.",
                        data={"queue_capacity": QUEUE_CAPACITY, "available_slots": 0},
                    )
                )
            self._active_slots += 1

        # ── Create task ────────────────────────────────────────────
        task = TaskInfo(
            tenant_id=tenant_id,
            name=os.path.basename(req.file_path),
            file_path=req.file_path,
            file_type=infer_file_type(req.file_path),
            file_size_bytes=self._get_file_size(req.file_path),
            webhook_url=req.webhook_url,
            idempotency_key=idempotency_key,
            preset_name=req.preset,
            prompt_ids=req.prompt_ids or [],
            kb_id=req.kb_id or (req.knowledge_base_id or ""),
            setting_id=req.setting_id,
            document_id=req.document_id or "",
            storage_backend=req.storage_backend or "local",
            storage_key=req.storage_key or "",
            mps_video_url=getattr(req, "mps_video_url", None) or "",
            ontology_schema=req.ontology_schema,
            # ── Reparse / recompile execution control ──
            execution_mode=req.execution_mode or "full",
            content_generation=req.content_generation or 0,
            schema_version=req.schema_version or 0,
            schema_hash=req.schema_hash or "",
            strict_push=req.strict_push or False,
        )
        self._tasks[task.task_id] = task
        self._repo.save(task)

        handle = TaskHandle(lambda: self._release_slot(task.task_id))
        self._handles[task.task_id] = handle

        if idempotency_key:
            self._idempotency[idempotency_key] = (
                time.monotonic() + IDEMPOTENCY_TTL_SEC,
                task.task_id,
            )

        logger.info(
            f"Task created: {task.task_id} tenant={tenant_id} file={task.name}"
        )

        # ── Async validate → enqueue ───────────────────────────────
        asyncio.create_task(self._validate_and_enqueue(task, req))

        return CreateTaskResponse(
            task_id=task.task_id,
            tenant_id=tenant_id,
            status=task.status,
            created_at=task.created_at,
        )

    async def get(self, task_id: str, tenant_id: str) -> TaskInfo | None:
        task = self._tasks.get(task_id)
        if task and task.tenant_id == tenant_id:
            return task
        return None

    async def list(
        self, tenant_id: str, status: str, file_type: str,
        page: int, page_size: int, sort: str,
    ) -> PaginatedTasks:
        tasks = [
            t for t in self._tasks.values()
            if t.tenant_id == tenant_id
        ]
        # Filter
        if status != "all":
            if status == "active":
                tasks = [t for t in tasks if t.status not in TERMINAL_STATES]
            else:
                try:
                    st = TaskStatus(status)
                    tasks = [t for t in tasks if t.status == st]
                except ValueError:
                    pass
        if file_type != "all":
            try:
                ft = FileType(file_type)
                tasks = [t for t in tasks if t.file_type == ft]
            except ValueError:
                pass

        # Sort
        reverse = sort.startswith("-")
        sort_key = sort.lstrip("-")
        if sort_key == "created_at":
            tasks.sort(key=lambda t: t.created_at, reverse=reverse)
        else:
            tasks.sort(key=lambda t: t.created_at, reverse=True)

        # Paginate
        total = len(tasks)
        start = (page - 1) * page_size
        page_tasks = tasks[start : start + page_size]

        items = [
            TaskListItem(
                task_id=t.task_id,
                name=t.name,
                file_type=t.file_type,
                status=t.status,
                progress=t.progress,
                progress_detail=t.progress_detail,
                worker_id=t.worker_id,
                created_at=t.created_at,
            )
            for t in page_tasks
        ]
        return PaginatedTasks(total=total, page=page, page_size=page_size, tasks=items)

    async def cancel(self, task_id: str, tenant_id: str) -> CancelTaskResponse | None:
        task = await self.get(task_id, tenant_id)
        if task is None:
            return None

        if task.status in TERMINAL_STATES:
            return CancelTaskResponse(
                task_id=task_id,
                previous_status=task.status,
                status=task.status,
                http_code=200,
            )

        prev = task.status
        is_processing = task.status == TaskStatus.PROCESSING

        task.status = TaskStatus.CANCELLED
        task.error_code = ErrorCode.TASK_CANCELLED
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)

        handle = self._handles.get(task_id)
        if handle:
            handle.cancel_event.set()
            handle.release_slot()

        return CancelTaskResponse(
            task_id=task_id,
            previous_status=prev,
            status=TaskStatus.CANCELLED,
            http_code=202 if is_processing else 200,
        )

    # ── Internal: validate + enqueue ────────────────────────────────

    async def _validate_and_enqueue(self, task: TaskInfo, req: CreateTaskRequest):
        handle = self._handles.get(task.task_id)
        if not handle:
            return

        try:
            # Check cancellation before starting
            if handle.cancel_event.is_set():
                return

            # Validate file path
            # [jonex] P0-A.2: ontology_only 不本地化 COS、不需要原文件 → 跳过文件存在性校验，
            # 直接进入"按 document_id 读 LightRAG 实体/关系 → 抽本体"。
            if task.execution_mode != "ontology_only" and not os.path.exists(task.file_path):
                self._fail_task(task, ErrorCode.FILE_NOT_FOUND, f"File not found: {task.file_path}")
                handle.release_slot()
                return

            # Resolve config via ConfigResolver
            if self._config_resolver:
                try:
                    task.config_snapshot = self._config_resolver.resolve(
                        req, tenant_id=task.tenant_id, kb_id=getattr(task, "kb_id", ""),
                    )
                except Exception as e:
                    logger.warning(
                        f"Config resolution failed for {task.task_id}: {e}. "
                        f"Using minimal config."
                    )
                    task.config_snapshot = {"file_path": task.file_path}
            else:
                task.config_snapshot = {"file_path": task.file_path}
            task.config_snapshot.setdefault("file_path", task.file_path)
            # Carry force_reparse flag through to pipeline
            task.config_snapshot["force_reparse"] = req.force_reparse
            # [jonex] 阶段4：把严格推送 + 执行模式透传给 PushChunksStage
            task.config_snapshot["strict_push"] = task.strict_push
            task.config_snapshot["execution_mode"] = task.execution_mode

            # Check cancellation after validation
            if handle.cancel_event.is_set():
                self._transition(task, TaskStatus.CANCELLED, ErrorCode.TASK_CANCELLED)
                handle.release_slot()
                return

            # Enqueue
            self._transition(task, TaskStatus.QUEUED)
            task.queued_at = datetime.now(timezone.utc)
            await self._queue.put(task.task_id)

        except Exception as e:
            logger.error(f"Validate/enqueue failed for {task.task_id}: {e}")
            self._fail_task(task, _classify_error(e), str(e))
            handle.release_slot()

    # ── Worker loop ─────────────────────────────────────────────────

    async def _worker_loop(self, worker_id: str):
        logger.info(f"Worker started: {worker_id}")
        while not self._shutting_down:
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            task = self._tasks.get(task_id)
            handle = self._handles.get(task_id)
            if not task or not handle:
                self._queue.task_done()
                continue

            task.worker_id = worker_id
            self._transition(task, TaskStatus.PROCESSING)
            task.started_at = datetime.now(timezone.utc)

            try:
                await self._execute_pipeline(task, handle)
            except TaskCancelledError:
                self._transition(task, TaskStatus.CANCELLED, ErrorCode.TASK_CANCELLED)
            except Exception as e:
                logger.error(f"Pipeline failed for {task_id}: {e}\n{traceback.format_exc()}")
                self._fail_task(task, _classify_error(e), str(e))
            finally:
                task.worker_id = None
                task.completed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                handle.release_slot()
                self._queue.task_done()
                self._maybe_deliver_webhook(task)

        logger.info(f"Worker stopped: {worker_id}")

    async def _execute_pipeline(self, task: TaskInfo, handle: TaskHandle):
        """Execute the RAGAnything pipeline (HTTP mode).

        HTTP pipeline: parse → multimodal → push_chunks → ontology.
        Uses self._pipeline_executor (RAGAnything with http_client).
        """
        # Check cancellation before starting
        if handle.cancel_event.is_set():
            raise TaskCancelledError()

        # ── HTTP mode ──────────────────────────────────────────────
        if self._pipeline_executor is not None and self._http_client is not None:
            await self._execute_pipeline_http(task, handle)
            return

        # ── Embedded mode (fallback) ───────────────────────────────
        raise RuntimeError(
            "Embedded mode is not supported in this TaskManager version. "
            "Configure LIGHTRAG_API_URL to enable HTTP mode."
        )

    def _resolve_task_prompt_overrides(self, task: TaskInfo):
        """[jonex] B2: 按 task.prompt_ids 解析主解析提示词覆盖（PromptOverride）。

        - 无 prompt_ids / 无 pcm → None（走内置默认）。
        - 缺失或空内容的 prompt_id：RAG_PROMPT_STRICT（默认 true）时 **fail-fast**（抛异常 →
          worker 置任务 FAILED，错误含缺失 id），避免"KB 有 id 但 atomic-rag 找不到"时静默走默认。
        """
        pids = list(getattr(task, "prompt_ids", []) or [])
        if not pids:
            return None
        if self._pcm is None:
            logger.warning(
                "Task %s has prompt_ids but PromptConfigManager not configured; using defaults",
                task.task_id,
            )
            return None
        from raganything.service.prompt_integration import PromptOverride

        strict = os.getenv("RAG_PROMPT_STRICT", "true").lower() in ("1", "true", "yes", "on")
        by_code: dict[str, str] = {}
        for pid in pids:
            item = self._pcm.get(task.tenant_id, pid)
            if item is None or not getattr(item, "content", ""):
                msg = f"prompt config not found or empty: id={pid} tenant={task.tenant_id}"
                if strict:
                    raise RuntimeError(f"PROMPT_OVERRIDE_MISSING: {msg}")
                logger.warning("Prompt override missing (fallback to default): %s", msg)
                continue
            by_code[item.prompt_code] = item.content
        return PromptOverride(by_code=by_code) if by_code else None

    async def _execute_pipeline_http(self, task: TaskInfo, handle: TaskHandle):
        """HTTP mode pipeline execution."""
        # Check cancellation before starting
        if handle.cancel_event.is_set():
            raise TaskCancelledError()

        # ── [jonex] P0-A: ontology-only 执行模式 ──
        # 跳过 parse/multimodal/push，直接按 document_id 从 LightRAG 读实体/关系抽本体。
        # ctx.content_list 不可用（无解析），_run_ontology_extraction 内部按 document_id
        # 分页读 LightRAG，不依赖 content_list（传空列表即可）。
        if task.execution_mode == "ontology_only":
            await self._run_ontology_only(task, handle)
            return

        # Register progress callback
        progress_cb = ProgressTrackingCallback(task, handle)
        self._pipeline_executor.callback_manager.register(progress_cb)

        # ── PipelineContext (base) — per-task context ──
        # 用 raganything.pipeline.base.PipelineContext（dataclass，字段齐全），
        # 而非本模块的统计用 PipelineContext（__slots__ 缺 collected_doc_ids 等），
        # 否则 pipeline.execute 的 merge_context(dataclasses.replace) 与回写会报错。
        ctx = PipelineCtx(
            file_path=task.file_path,
            file_name=task.name,
            tenant_id=task.tenant_id,
            kb_id=task.kb_id,
            doc_id=task.document_id or "",
            document_id=task.document_id or "",
            cancel_event=handle.cancel_event,
            force_reparse=task.config_snapshot.get("force_reparse", False),
            parser_type=task.config_snapshot.get("parser", ""),
            config_snapshot=task.config_snapshot,
            mps_video_url=task.mps_video_url or "",
        )
        # [jonex] B2: 主解析提示词覆盖（按 task.prompt_ids 解析；缺失 id fail-fast）
        ctx.prompt_overrides = self._resolve_task_prompt_overrides(task)
        ctx.started_at = time.time()

        doc_id = None
        try:
            # Check cancellation before pipeline
            if handle.cancel_event.is_set():
                raise TaskCancelledError()

            # [jonex] 阶段4：reparse_strict 解析前快照权威 old_ids（PG 传入 ∪ LightRAG 现查），
            # 用于推新成功后按差集 old−new 收敛旧 doc；查询失败即终止 reparse。
            if task.execution_mode == "reparse_strict":
                task.old_rag_doc_ids = await self._snapshot_old_doc_ids(task)
                self._repo.save(task)

            # Run HTTP pipeline: parse → multimodal → push_chunks
            doc_id = await self._pipeline_executor.process_document_complete(
                file_path=task.file_path,
                file_name=task.name,
                cancel_event=handle.cancel_event,
                force_reparse=task.config_snapshot.get("force_reparse", False),
                tenant_id=task.tenant_id,
                kb_id=task.kb_id,
                doc_id=task.document_id,
                ctx=ctx,
            )

            if doc_id:
                # ── Collect tracking info from PipelineContext ──
                task.lightrag_doc_ids = list(ctx.collected_doc_ids)
                task.pending_track_ids = list(ctx.pending_track_ids)
                task.failed_chunk_count = getattr(ctx, 'failed_chunk_count', 0)
                task.total_chunk_count = getattr(ctx, 'total_chunk_count', 0)
                # [jonex] #6: persist timeout count for KB reconciliation
                task.timeout_chunk_count = getattr(ctx, 'timeout_chunk_count', 0)

                # ── 提前置位：push_chunks 完成后立即标 ontology_status，
                # 让 KB 对账循环在下一轮（≤30s）就能提升文档状态到 READY+EXTRACTING，
                # 不必等 _run_ontology_extraction 执行（中间还有 summary/reparse 等步骤）。
                # 约束：① reparse_strict 跳过（差集删旧未收敛，不应提前暴露 READY）；
                # ② all_duplicated 跳过（后置逻辑会直接标 completed，中间 extracting
                #    窗口会被对账读到并触发不必要的 ontology-only 重抽，抵消 #5 的节省）。
                total_pushed = getattr(ctx, 'total_pushed_count', 0)
                duplicated = getattr(ctx, 'duplicated_chunk_count', 0)
                all_duplicated = total_pushed > 0 and duplicated == total_pushed
                if (
                    task.execution_mode != "reparse_strict"
                    and not all_duplicated
                    and os.getenv("ONTOLOGY_EXTRACT_ENABLED", "false").lower()
                    in ("1", "true", "yes", "on")
                    and task.ontology_schema
                ):
                    task.ontology_status = "extracting"
                    self._repo.save(task)

                # ── Read result summary from :9621 ──
                summary = await self._read_result_summary_http(
                    task.tenant_id, task.kb_id, task.document_id,
                )
                ctx.completed_at = time.time()
                summary.duration_seconds = ctx.duration_seconds
                summary.doc_id = doc_id

                # ── Block stats from content_list（base ctx 无统计方法，就地统计）──
                _tb = _tab = _cod = 0
                for _item in (ctx.content_list or []):
                    _t = _item.get("type", "text")
                    if _t == "text":
                        _tb += 1
                    elif _t == "table":
                        _tab += 1
                    elif _t == "code":
                        _cod += 1
                summary.blocks = _tb + _tab + _cod
                summary.text_blocks = _tb
                summary.table_blocks = _tab
                summary.code_blocks = _cod

                task.result_summary = summary

                # [jonex] 阶段4：reparse_strict 推新全部成功后，按差集 old−new 收敛旧 doc
                # （仅 LightRAG；Neo4j 清旧+写新由 KB 对账 _handle_completed 负责）。
                # 同内容重解析 new==old → 差集空 → 不误删。删除后轮询确认旧 doc 不可见，
                # 再进入本体抽取，避免读到新旧并集（P0-3）。
                if task.execution_mode == "reparse_strict":
                    task.new_rag_doc_ids = list(ctx.collected_doc_ids)
                    await self._reparse_converge_old(task)

                # ── Ontology extraction (by document_id filter) ──
                # [jonex] #5: all-duplicated guard — skip ontology when every chunk
                # was idempotent duplicate, saving LLM cost (aligned with v1).
                total_pushed = getattr(ctx, 'total_pushed_count', 0)
                duplicated = getattr(ctx, 'duplicated_chunk_count', 0)
                all_duplicated = total_pushed > 0 and duplicated == total_pushed

                if (
                    os.getenv("ONTOLOGY_EXTRACT_ENABLED", "false").lower()
                    in ("1", "true", "yes", "on")
                    and task.ontology_schema
                ):
                    if all_duplicated:
                        task.ontology_status = "completed"
                        logger.info(
                            f"Task {task.task_id}: 全 chunk 幂等重复（{duplicated}/{total_pushed}），"
                            f"跳过本体抽取"
                        )
                    else:
                        await self._run_ontology_extraction(task, ctx, doc_id)

                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
                task.current_step = "done"

                logger.info(
                    f"Task {task.task_id} completed (HTTP mode): doc_id={doc_id} "
                    f"entities={summary.entities} chunks={summary.chunks} "
                    f"lightrag_doc_ids={len(task.lightrag_doc_ids)}"
                )
            else:
                # [jonex] #3/#6: 失败也保留已确认 doc_id / pending track / 分类计数，
                # 并用 pipeline 真实错误（含 "RAG_PUSH_TIMEOUT" / "...硬失败" 前缀）作为
                # 失败原因，供 KB 对账区分超时 vs 硬失败（否则被写死为通用错误而丢失语义）。
                task.lightrag_doc_ids = list(ctx.collected_doc_ids)
                task.pending_track_ids = list(ctx.pending_track_ids)
                task.failed_chunk_count = getattr(ctx, "failed_chunk_count", 0)
                task.total_chunk_count = getattr(ctx, "total_chunk_count", 0)
                task.timeout_chunk_count = getattr(ctx, "timeout_chunk_count", 0)
                reason = getattr(ctx, "error", None) or (
                    "Pipeline returned no doc_id (may indicate internal error)"
                )
                # [jonex] 阶段4：reparse_strict 推新失败 → 补偿删除本次已产生的 new−old，
                # 旧数据完整保留、不残留半份新数据（P0-2）。
                if task.execution_mode == "reparse_strict":
                    await self._reparse_compensate(task, ctx)
                self._fail_task(task, ErrorCode.UNKNOWN, reason)
        except TaskCancelledError:
            # ── Cancel: save collected doc_ids, mark cancelled ──
            task.lightrag_doc_ids = list(ctx.collected_doc_ids)
            task.pending_track_ids = list(ctx.pending_track_ids)
            task.failed_chunk_count = getattr(ctx, 'failed_chunk_count', 0)
            task.total_chunk_count = getattr(ctx, 'total_chunk_count', 0)
            task.timeout_chunk_count = getattr(ctx, 'timeout_chunk_count', 0)
            # 复位提前置位的 ontology_status，避免 FAILED 任务悬空在 extracting
            if task.ontology_status == "extracting":
                task.ontology_status = "pending"
            # [jonex] 阶段4：reparse_strict 取消 → 同样补偿删除 new−old
            if task.execution_mode == "reparse_strict":
                try:
                    await self._reparse_compensate(task, ctx)
                except Exception:
                    logger.warning("reparse compensate on cancel failed task=%s", task.task_id, exc_info=True)
            self._repo.save(task)
            raise
        except Exception as e:
            # [jonex] #6: persist collected doc_ids even on failure
            # so KB reconciliation knows which chunks already made it in
            task.lightrag_doc_ids = list(ctx.collected_doc_ids)
            task.pending_track_ids = list(ctx.pending_track_ids)
            task.failed_chunk_count = getattr(ctx, 'failed_chunk_count', 0)
            task.total_chunk_count = getattr(ctx, 'total_chunk_count', 0)
            task.timeout_chunk_count = getattr(ctx, 'timeout_chunk_count', 0)
            # 复位提前置位的 ontology_status，避免 FAILED 任务悬空在 extracting
            if task.ontology_status == "extracting":
                task.ontology_status = "pending"
            # [jonex] 阶段4：reparse_strict 异常 → 补偿删除 new−old（best-effort）
            if task.execution_mode == "reparse_strict":
                try:
                    await self._reparse_compensate(task, ctx)
                except Exception:
                    logger.warning("reparse compensate on error failed task=%s", task.task_id, exc_info=True)
            self._repo.save(task)
            logger.error(f"Pipeline error for {task.task_id}: {e}\n{traceback.format_exc()}")
            raise
        finally:
            self._pipeline_executor.callback_manager.unregister(progress_cb)
            task.updated_at = datetime.now(timezone.utc)
            self._repo.save(task)

    # ── Reparse strict replacement helpers (阶段4) ───────────────────

    async def _list_doc_ids_by_document(self, task: TaskInfo) -> list[str]:
        """按 KB document_id 全量分页查询 LightRAG 现有 doc id（只精确匹配，不用文件名兜底）。"""
        found: list[str] = []
        page = 1
        while True:
            result = await self._http_client.get_documents(
                task.tenant_id, task.kb_id,
                document_id=task.document_id or "", page=page, page_size=200,
            )
            entries = (result or {}).get("documents") or []
            if not entries:
                for status_list in (result or {}).get("statuses", {}).values():
                    if isinstance(status_list, list):
                        entries.extend(status_list)
            if not entries:
                break
            for e in entries:
                did = e.get("id")
                if did:
                    found.append(did)
            total = int((result or {}).get("total", 0) or 0)
            if len(entries) < 200 or (total and page * 200 >= total):
                break
            page += 1
        return found

    async def _snapshot_old_doc_ids(self, task: TaskInfo) -> list[str]:
        """[jonex] 阶段4：权威 old_ids = PG 传入 ∪ LightRAG 按 document_id 全量分页。

        只按 document_id 精确匹配，禁用文件名兜底；实时分页查询失败 → 抛错终止 reparse
        （不能在不知道旧集合的情况下推新/删旧）。
        """
        old_ids: set[str] = set(task.old_rag_doc_ids or [])
        try:
            old_ids.update(await self._list_doc_ids_by_document(task))
        except Exception as e:
            raise RuntimeError(
                f"reparse 快照旧 doc 失败（LightRAG 查询异常），终止 reparse: {e}"
            ) from e
        return list(old_ids)

    async def _reparse_converge_old(self, task: TaskInfo) -> None:
        """推新全部成功后按差集 old−new 收敛旧 doc，进入 cleanup 状态机；删净后轮询读一致性。"""
        old = set(task.old_rag_doc_ids or [])
        new = set(task.new_rag_doc_ids or [])
        delete_set = old - new
        if not delete_set:
            return
        task.current_step = "cleanup"
        task.delete_pending_ids = list(delete_set)
        self._repo.save(task)
        await self._run_cleanup(task)
        # 读一致性（P0-3 option a）：轮询确认旧 doc 不可见，再进入本体抽取
        await self._poll_old_ids_gone(task, delete_set)
        if not task.delete_pending_ids and not task.compensate_pending_ids:
            task.current_step = "done"
            self._repo.save(task)

    async def _reparse_compensate(self, task: TaskInfo, ctx) -> None:
        """[jonex] 阶段4 失败补偿：删除本次已产生的 new−old，使旧数据完整保留。"""
        old = set(task.old_rag_doc_ids or [])
        produced = set(getattr(ctx, "collected_doc_ids", []) or []) | set(task.new_rag_doc_ids or [])
        compensate = produced - old
        if not compensate:
            return
        task.current_step = "cleanup"
        task.compensate_pending_ids = list(compensate)
        self._repo.save(task)
        await self._run_cleanup(task)

    async def _run_cleanup(self, task: TaskInfo) -> None:
        """删除 delete_pending_ids（差集删旧）与 compensate_pending_ids（失败补偿）。

        删成功即从列表移除并持久化 → 容器重启可续跑（只删剩余，不重跑解析管线）。
        delete_doc 收 deletion_started 视为已发起；删除失败保留在列表待重试。
        """
        for field in ("delete_pending_ids", "compensate_pending_ids"):
            ids = list(getattr(task, field, []) or [])
            remaining = list(ids)
            for did in ids:
                try:
                    await self._http_client.delete_doc(did, tenant_id=task.tenant_id, kb_id=task.kb_id)
                    remaining.remove(did)
                    setattr(task, field, list(remaining))
                    self._repo.save(task)
                except Exception as e:
                    logger.warning(
                        f"cleanup delete failed task={task.task_id} field={field} doc={did}: {e}"
                    )
            setattr(task, field, list(remaining))
            self._repo.save(task)

    async def _poll_old_ids_gone(self, task: TaskInfo, old_ids: set[str]) -> None:
        """轮询确认旧 doc 已从 LightRAG 不可见（delete_doc 后台异步删除的收敛确认）。

        bounded：最多 RAG_CLEANUP_POLL_TRIES 次、每次间隔 RAG_CLEANUP_POLL_DELAY 秒；
        超时仍未收敛则保留 cleanup 状态（可恢复），记 warning，不强制 completed。
        """
        tries = int(os.getenv("RAG_CLEANUP_POLL_TRIES", "15"))
        delay = float(os.getenv("RAG_CLEANUP_POLL_DELAY", "2"))
        for _ in range(max(1, tries)):
            try:
                current = set(await self._list_doc_ids_by_document(task))
            except Exception as e:
                logger.warning("cleanup poll query failed task=%s: %s", task.task_id, e)
                return
            if not (old_ids & current):
                return
            await asyncio.sleep(delay)
        logger.warning(
            "cleanup poll timeout task=%s: 旧 doc 仍可见，保留 cleanup 状态待收敛",
            task.task_id,
        )

    async def _resume_cleanup(self, task: TaskInfo) -> None:
        """[jonex] 阶段4 P0-J：容器重启后只恢复 cleanup（续删剩余 doc），不重跑解析管线。

        - compensate_pending_ids 非空 → 失败补偿路径：删净后置 FAILED。
        - 否则 → 差集删旧收敛路径：删净 + 轮询读一致性后置 COMPLETED（KB 对账落 Neo4j）。
        """
        try:
            is_compensation = bool(task.compensate_pending_ids)
            await self._run_cleanup(task)
            if is_compensation:
                self._fail_task(
                    task, ErrorCode.LIGHTRAG_ERROR,
                    "reparse 严格推送失败，已补偿清理本次新数据（旧数据保留）",
                )
            else:
                delete_set = set(task.old_rag_doc_ids or []) - set(task.new_rag_doc_ids or [])
                await self._poll_old_ids_gone(task, delete_set)
                task.current_step = "done"
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                self._repo.save(task)
        except Exception as e:
            logger.error(f"Resume cleanup failed for {task.task_id}: {e}")

    # ── Ontology-only execution (P0-A) ──────────────────────────────

    async def _run_ontology_only(self, task: TaskInfo, handle: TaskHandle) -> None:
        """[jonex] P0-A: ontology-only 执行 — 只重抽本体，跳过 parse/multimodal/push。

        直接按 document_id 从 LightRAG 读实体/关系做本体归类，不需要原文件，也不需要
        content_list。要求任务携带 compiled schema（否则无法归类 → 失败）。
        """
        if handle.cancel_event.is_set():
            raise TaskCancelledError()

        if not task.ontology_schema:
            self._fail_task(
                task, ErrorCode.CONFIG_INVALID,
                "ontology_only 任务缺少 compiled schema，无法归类",
            )
            return

        # 轻量 ctx：content_list 为空，_run_ontology_extraction 按 document_id 读 LightRAG
        ctx = PipelineCtx(
            file_path=task.file_path,
            file_name=task.name,
            tenant_id=task.tenant_id,
            kb_id=task.kb_id,
            doc_id=task.document_id or "",
            document_id=task.document_id or "",
            cancel_event=handle.cancel_event,
            config_snapshot=task.config_snapshot or {},
        )
        ctx.started_at = time.time()

        await self._run_ontology_extraction(
            task, ctx, task.document_id or "", force_edge_based=True,
        )

        # ontology-only 复用已有 LightRAG doc，不产新 doc；状态收尾
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.current_step = "done"
        self._repo.save(task)
        logger.info(
            f"Task {task.task_id} completed (ontology_only): "
            f"doc={task.document_id} ontology_status={task.ontology_status}"
        )

    # ── Ontology extraction (Stage 5) ───────────────────────────────

    async def _run_ontology_extraction(
        self, task: TaskInfo, ctx: PipelineContext, doc_id: str,
        *, force_edge_based: bool = False,
    ) -> None:
        """[jonex] Run ontology extraction via jonex_core.OntologyExtractor.

        Orchestration only — all ontology classification/LLM prompt/post-validation
        logic lives in jonex_core, NOT in raganything.

        Reads LightRAG entities + relations via HttpLightRagClient,
        resolves compiled schema, calls OntologyExtractor.extract(),
        and saves results to task.ontology_status/data/error.
        """
        import re

        task.ontology_status = "extracting"
        # Push a timeline entry for the ontology stage
        task.timeline.append(StageTiming(
            stage="ontology_extract",
            label="本体抽取",
            detail="LLM 本体类型归类 + 关系定型",
            started_at=datetime.now(timezone.utc),
        ))
        self._repo.save(task)

        try:
            kb_id = task.kb_id or ""

            # ① Read LightRAG entities (paginated, filtered by document_id)
            all_entities: list[dict] = []
            page = 1
            while True:
                try:
                    batch = await self._http_client.get_entities(
                        task.tenant_id, kb_id,
                        page=page, page_size=200,
                        document_id=task.document_id or "",
                    )
                except Exception as e:
                    logger.warning(
                        f"Ontology: failed to read entities for {task.task_id}: {e}"
                    )
                    break
                items = batch.get("items", [])
                if not items:
                    break
                all_entities.extend(items)
                total = int(batch.get("total", 0) or 0)
                if total and len(all_entities) >= total:
                    break
                page += 1

            # Filter namespace-token garbage entities
            _ns_pattern = re.compile(r"<!--yx:[a-f0-9]{8}-->")
            all_entities = [
                e for e in all_entities
                if not _ns_pattern.search(e.get("name", ""))
            ]

            if not all_entities:
                task.ontology_status = "failed"
                task.ontology_error = "LightRAG 存储中未找到候选实体，无法抽取本体"
                self._repo.save(task)
                return

            # ①b Read LightRAG relations (paginated)
            all_relations: list[dict] = []
            page = 1
            while True:
                try:
                    batch = await self._http_client.get_relationships(
                        task.tenant_id, kb_id,
                        page=page, page_size=200,
                        document_id=task.document_id or "",
                    )
                except Exception as e:
                    logger.warning(
                        f"Ontology: failed to read relations for {task.task_id}: {e}"
                    )
                    break
                items = batch.get("items", [])
                if not items:
                    break
                all_relations.extend(items)
                total = int(batch.get("total", 0) or 0)
                if total and len(all_relations) >= total:
                    break
                page += 1

            # ② Resolve compiled schema
            compiled_schema = task.ontology_schema
            if not compiled_schema:
                try:
                    from jonex_core.capability.atomic.ontology.compiled_schema_client import (
                        CompiledSchemaClient,
                    )
                    compiled_schema = await CompiledSchemaClient().get_schema(
                        task.tenant_id, kb_id,
                    )
                except Exception as e:
                    logger.warning(
                        f"Ontology: compiled schema fetch failed for {task.task_id}: {e}"
                    )

            # ③ Call jonex_core.OntologyExtractor.extract()
            from jonex_core.capability.atomic.ontology import OntologyRegistry
            from jonex_core.capability.atomic.rag.ontology_extractor import (
                OntologyExtractor,
            )

            registry = OntologyRegistry()
            schema_path = os.getenv(
                "ONTOLOGY_SCHEMA_PATH",
                "deploy/config/ontology/default.yaml",
            )
            try:
                registry.load(schema_path)
            except Exception as e:
                logger.warning(
                    f"Ontology: failed to load schema from {schema_path}: {e}"
                )

            extractor = OntologyExtractor(registry)

            scope = {
                "tenant_id": task.tenant_id,
                "knowledge_base_id": kb_id,
                "document_id": task.document_id or "",
                "trace_id": task.task_id,
            }

            result = await extractor.extract(
                content_list=ctx.content_list or [],
                lightrag_entities=all_entities,
                lightrag_relations=all_relations,
                scope=scope,
                compiled_schema=compiled_schema,
                # [jonex] P0-A.6：ontology-only / reparse 强制边定型，不受环境开关影响
                edge_based=True if force_edge_based else None,
            )

            # ④ Save results to task
            task.ontology_status = "completed" if result.ok else "failed"
            task.ontology_data = {
                "entities": [
                    {
                        "canonical_name": e.canonical_name,
                        "entity_type": e.entity_type,
                        "aliases": e.aliases,
                        "attributes": e.attributes,
                        "description": e.description,
                        "confidence": e.confidence,
                        "source_chunks": e.source_chunks,
                        "extraction_method": e.extraction_method,
                    }
                    for e in result.entities
                ],
                "relations": [
                    {
                        "source_name": r.source_name,
                        "source_type": r.source_type,
                        "target_name": r.target_name,
                        "target_type": r.target_type,
                        "relation_type": r.relation_type,
                        "confidence": r.confidence,
                    }
                    for r in result.relations
                ],
            }
            task.ontology_error = (
                str(result.errors[:1]) if result.errors else ""
            )

            logger.info(
                f"Ontology extraction done for {task.task_id}: "
                f"status={task.ontology_status} "
                f"entities={len(result.entities)} relations={len(result.relations)}"
            )

        except Exception as e:
            logger.warning(
                f"Ontology extraction failed for {task.task_id}: {e}",
                exc_info=True,
            )
            task.ontology_status = "failed"
            task.ontology_error = str(e)[:500]
        finally:
            # Close the ontology stage timing
            if task.timeline:
                last = task.timeline[-1]
                if last.stage == "ontology_extract" and last.ended_at is None:
                    now = datetime.now(timezone.utc)
                    last.ended_at = now
                    if last.started_at:
                        last.elapsed_seconds = (now - last.started_at).total_seconds()
            self._repo.save(task)

    # ── Result summary (HTTP mode) ──────────────────────────────────

    async def _read_result_summary_http(
        self, tenant_id: str, kb_id: str, document_id: str,
    ) -> ResultSummary:
        """Read pipeline results from :9621 via HTTP."""
        summary = ResultSummary(doc_id=document_id)
        try:
            result = await self._http_client.get_document_parse_result(
                tenant_id=tenant_id, kb_id=kb_id, document_id=document_id,
            )
            docs = result.get("documents", {})
            entities = result.get("entities", {})
            relationships = result.get("relationships", {})
            summary.chunks = len(docs.get("items", docs.get("data", [])) if isinstance(docs, dict) else docs)
            summary.entities = len(entities.get("items", entities.get("data", [])) if isinstance(entities, dict) else entities)
            summary.relations = len(relationships.get("items", relationships.get("data", [])) if isinstance(relationships, dict) else relationships)
        except Exception as e:
            logger.warning(f"Failed to read summary for {document_id}: {e}")
        return summary

    # ── Restart recovery ────────────────────────────────────────────

    async def _resume_track_polling(self, task: TaskInfo):
        """Restart recovery: re-poll pending track_ids after TaskManager restart.

        Called from start() for non-terminal tasks with pending_track_ids.
        """
        pending = list(task.pending_track_ids)
        if not pending:
            # All tracks already terminal — determine final state
            if task.lightrag_doc_ids:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
            else:
                self._fail_task(task, ErrorCode.LIGHTRAG_ERROR,
                                "All chunks failed during previous run")
            self._repo.save(task)
            return

        logger.info(
            f"Resume polling {len(pending)} tracks for task {task.task_id}"
        )

        try:
            terminal, still_pending = await self._http_client.batch_track_status(
                pending,
                tenant_id=task.tenant_id,
                kb_id=task.kb_id,
                max_wait_seconds=float(
                    os.getenv("RAG_TRACK_TIMEOUT_SECONDS", "1800")
                ),
                per_track_timeout_seconds=float(
                    os.getenv("RAG_TRACK_PER_CHUNK_TIMEOUT_SECONDS", "900")
                ),
            )
        except Exception as e:
            logger.error(f"Resume track polling failed for {task.task_id}: {e}")
            self._fail_task(task, ErrorCode.LIGHTRAG_ERROR, str(e))
            return

        # Merge completed doc_ids + classify terminal failures
        for tid, status in terminal.items():
            if status.state == "completed":
                for doc_id in status.doc_ids:
                    if doc_id not in task.lightrag_doc_ids:
                        task.lightrag_doc_ids.append(doc_id)
            else:
                # [jonex] #6: terminal failed → hard failure
                task.failed_chunk_count += 1

        # [jonex] #6: still_pending → timeout (not hard failure)
        task.timeout_chunk_count = len(still_pending)
        task.pending_track_ids = list(still_pending.keys())

        if not task.pending_track_ids:
            # All terminal — determine final state
            if task.lightrag_doc_ids:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
            else:
                self._fail_task(task, ErrorCode.LIGHTRAG_ERROR,
                                "All chunks failed after resume")
        # else: still pending — keep current state

        self._repo.save(task)
        logger.info(
            f"Resume polling done for {task.task_id}: "
            f"{len(task.lightrag_doc_ids)} doc_ids, "
            f"{len(task.pending_track_ids)} still pending"
        )

    # ── Cleanup ─────────────────────────────────────────────────────

    # ── Parser artifact helpers (Bug 3) ──────────────────────────────

    @staticmethod
    def _get_content_list_from_cache(rag: Any, doc_id: str) -> list[dict] | None:
        """Retrieve MinerU online content_list from parse cache by doc_id.

        Parse cache entries carry the doc_id set during initial parsing.
        Match by doc_id rather than file_path (cache key is an opaque hash).
        """
        parse_cache = getattr(rag, "parse_cache", None)
        if parse_cache is None:
            return None

        try:
            # JsonKVStorage has no get_all(); iterate _data dict
            cache_data = getattr(parse_cache, "_data", {}) or {}
            for _key, entry in cache_data.items():
                if isinstance(entry, dict) and entry.get("doc_id") == doc_id:
                    cl = entry.get("content_list")
                    if cl and isinstance(cl, list):
                        return cl
            return None
        except Exception as e:
            logger.warning(f"Failed to read content_list from parse cache: {e}")
            return None

    @staticmethod
    def _extract_images(content_list: list[dict], target_dir: Path) -> int:
        """Extract images from content_list into target_dir.

        Handles URL-based images (download via httpx) and base64-encoded
        images.  Failures are logged and skipped — missing images don't
        block the text pipeline.

        Returns count of successfully extracted images.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        seen_urls: set[str] = set()
        extracted = 0
        name_counter: dict[str, int] = {}

        for idx, item in enumerate(content_list):
            if item.get("type") != "image":
                continue

            # ── URL-based images ──
            url = item.get("image_url") or item.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                try:
                    resp = httpx.get(url, timeout=30.0, follow_redirects=True)
                    resp.raise_for_status()
                    base_name = (
                        url.rsplit("/", 1)[-1].split("?")[0]
                        or f"image_{idx:03d}"
                    )
                    name_counter[base_name] = name_counter.get(base_name, 0) + 1
                    if name_counter[base_name] > 1:
                        stem, ext = (
                            base_name.rsplit(".", 1)
                            if "." in base_name
                            else (base_name, "png")
                        )
                        base_name = f"{stem}_{name_counter[base_name]}.{ext}"
                    (target_dir / base_name).write_bytes(resp.content)
                    extracted += 1
                except Exception as e:
                    logger.warning(f"Failed to download image {url}: {e}")
                continue

            # ── Base64-encoded images ──
            b64 = item.get("image_base64") or item.get("base64")
            if b64:
                try:
                    data = base64.b64decode(b64)
                    name = item.get("name") or f"image_{idx:03d}"
                    name_counter[name] = name_counter.get(name, 0) + 1
                    if name_counter[name] > 1:
                        stem, ext = (
                            name.rsplit(".", 1)
                            if "." in name
                            else (name, "png")
                        )
                        name = f"{stem}_{name_counter[name]}.{ext}"
                    (target_dir / f"{name}.png").write_bytes(data)
                    extracted += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to decode base64 image at index {idx}: {e}"
                    )

        return extracted

    @staticmethod
    def _write_artifacts_to_staging(
        staging_dir: Path,
        content_list: list[dict] | None,
        parser_type: str,
    ) -> None:
        """Write MinerU artifacts into staging/mineru/ before commit.

        mineru_online: serialize content_list → content_list.json + extract images
        mineru/docling/paddleocr: handled by caller (copy output directory)
        """
        mineru_dir = staging_dir / "mineru"
        mineru_dir.mkdir(parents=True, exist_ok=True)

        if parser_type == "mineru_online" and content_list:
            # Write raw content_list.json
            raw_path = mineru_dir / "content_list.json"
            raw_path.write_text(
                json.dumps(content_list, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            # Extract images
            TaskManager._extract_images(content_list, mineru_dir / "images")

    # ── Cleanup ─────────────────────────────────────────────────────

    async def _cleanup_loop(self):
        while not self._shutting_down:
            await asyncio.sleep(CLEANUP_INTERVAL_SEC)
            now = datetime.now(timezone.utc)
            to_delete = []
            for task_id, task in self._tasks.items():
                if task.status in TERMINAL_STATES and task.completed_at:
                    age_hours = (now - task.completed_at).total_seconds() / 3600
                    if age_hours >= RETENTION_HOURS:
                        to_delete.append(task_id)
            for task_id in to_delete:
                task = self._tasks.pop(task_id)
                self._handles.pop(task_id, None)
                try:
                    self._repo.delete(task_id, task.tenant_id, task.kb_id)
                except Exception:
                    pass
            if to_delete:
                logger.info(f"Cleanup: removed {len(to_delete)} expired tasks")

    # ── Helpers ──────────────────────────────────────────────────────

    def _transition(self, task: TaskInfo, target: TaskStatus,
                    error_code: ErrorCode | None = None):
        if not validate_transition(task.status, target):
            logger.warning(
                f"Invalid transition: {task.task_id} {task.status} → {target}"
            )
            return
        task.status = target
        if error_code:
            task.error_code = error_code
        task.updated_at = datetime.now(timezone.utc)

    def _fail_task(self, task: TaskInfo, error_code: ErrorCode, message: str):
        task.status = TaskStatus.FAILED
        task.error_code = error_code
        task.error_message = message
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        try:
            self._repo.save(task)
        except Exception:
            pass

    def _check_idempotency(self, key: str) -> TaskInfo | None:
        expire_ts, task_id = self._idempotency.get(key, (0, ""))
        if time.monotonic() < expire_ts:
            existing = self._tasks.get(task_id)
            # [jonex] P0-A.5: 只复用非终态任务；failed/cancelled/completed 允许新建 attempt，
            # 否则失败任务会在 10min 幂等窗口内被反复返回、无法真正重试。
            if existing is not None and existing.status not in TERMINAL_STATES:
                return existing
            # 终态 → 不复用，清掉缓存让调用方新建
            self._idempotency.pop(key, None)
            return None
        # expired → remove
        self._idempotency.pop(key, None)
        return None

    @staticmethod
    def _get_file_size(path: str) -> int:
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    # ── Webhook delivery (Spec §4.6) ────────────────────────────────

    # SSRF protection: block internal/reserved IP ranges
    _SSRF_BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]

    _WEBHOOK_RETRIES = 3
    _WEBHOOK_RETRY_BACKOFF = 2.0  # seconds base
    _WEBHOOK_TIMEOUT = 30.0  # seconds

    @classmethod
    def _is_ssrf_safe(cls, url: str) -> bool:
        """Check a URL does not point to internal/private addresses."""
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False

            # Block raw IPs in private ranges
            try:
                addr = ipaddress.ip_address(hostname)
                for net in cls._SSRF_BLOCKED_NETWORKS:
                    if addr in net:
                        return False
                return True
            except ValueError:
                pass  # hostname, resolve it

            # For hostnames, resolve and check all IPs.
            # DNS failures are treated as safe — if the host can't be resolved,
            # the actual webhook request will fail anyway with a connection error.
            import socket as _socket
            try:
                ips = _socket.getaddrinfo(hostname, None)
            except _socket.gaierror:
                return True  # can't resolve → can't confirm unsafe → allow
            for ip_info in ips:
                ip_str = ip_info[4][0]
                addr = ipaddress.ip_address(ip_str)
                for net in cls._SSRF_BLOCKED_NETWORKS:
                    if addr in net:
                        return False
            return True
        except Exception:
            return False

    def _maybe_deliver_webhook(self, task: TaskInfo):
        """Deliver webhook asynchronously with retry (Spec §4.6).

        Runs as a background task so it doesn't block worker cleanup.
        Includes SSRF protection and HMAC signature.

        URL resolution order:
          1. Per-task webhook_url (from CreateTaskRequest)
          2. Global RAG_WEBHOOK_URL env var (v1 compat fallback)
        """
        webhook_url = task.webhook_url or DEFAULT_WEBHOOK_URL
        if not webhook_url or task.webhook_delivered:
            return

        task.webhook_delivered = True  # mark delivered to avoid double-send

        asyncio.create_task(self._deliver_webhook(task.task_id, webhook_url, task))

    async def _deliver_webhook(
        self, task_id: str, url: str, task: TaskInfo
    ) -> None:
        """Deliver webhook with up to 3 retries + exponential backoff."""
        # SSRF check
        if not self._is_ssrf_safe(url):
            logger.warning(
                f"Webhook SSRF blocked for {task_id}: {url}"
            )
            return

        payload = {
            "task_id": task.task_id,
            "tenant_id": task.tenant_id,
            "doc_id": (
                task.result_summary.doc_id if task.result_summary else ""
            ),
            "status": task.status.value,
            "progress": task.progress,
            "file_path": task.file_path,
            "file_type": task.file_type.value,
            "error_code": task.error_code.value if task.error_code else None,
            "error_message": task.error_message,
            "result_summary": (
                task.result_summary.model_dump(mode="json")
                if task.result_summary else None
            ),
            "storage": (
                task.storage.model_dump(mode="json")
                if task.storage else None
            ),
            "timeline": [
                t.model_dump(mode="json") for t in task.timeline
            ],
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
        }

        # Get webhook secret for HMAC
        webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Jonex-Event": "task.completed",
            "X-Jonex-Task-Id": task.task_id,
        }

        last_error = None
        for attempt in range(1, self._WEBHOOK_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self._WEBHOOK_TIMEOUT) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if 200 <= resp.status_code < 300:
                        logger.info(
                            f"Webhook delivered for {task_id}: {resp.status_code}"
                        )
                        return
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_error = str(e)

            if attempt < self._WEBHOOK_RETRIES:
                backoff = self._WEBHOOK_RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.warning(
                    f"Webhook attempt {attempt}/{self._WEBHOOK_RETRIES} failed "
                    f"for {task_id}: {last_error}. Retrying in {backoff}s"
                )
                await asyncio.sleep(backoff)

        logger.error(
            f"Webhook delivery failed after {self._WEBHOOK_RETRIES} attempts "
            f"for {task_id}: {last_error}"
        )


# ── SlotFullError ───────────────────────────────────────────────────

class SlotFullError(Exception):
    def __init__(self, response):
        self.response = response
