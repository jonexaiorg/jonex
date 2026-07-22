#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
RAG-Anything + LightRAG Server HTTP Adapter (atomic.rag.lightrag.v1)

Dependencies:
- raganything.Parser (Document parsing, does not depend on lightrag-hku)
- httpx (HTTP client, calls lightrag-server REST API)

Atomic capability: runs in atomic-rag container, responsible for document parsing + HTTP push
Search and graph are independently handled by lightrag-server container.
"""

from __future__ import annotations

import json
import os
import asyncio
import uuid
from functools import wraps
from typing import Any, AsyncGenerator, Optional, Dict, List

import httpx

from jonex_core.capability.atomic.rag.base import BaseRAGCapability
from jonex_core.capability.atomic.rag.storage_reader import LightRAGStorageReader
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)
from jonex_core.common import get_logger
from jonex_core.common.cache import get_redis_client
from jonex_core.common.exceptions import (
    UpstreamServiceError,
    CapabilityTimeoutError,
    TenantIsolationError,
    OperationNotSupportedError,
)

logger = get_logger("capability.atomic.rag.lightrag")


def _retry_on_transient(max_retries: int = 3, base_delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"LightRAG invoke {func.__name__} failed (attempt {attempt+1}/{max_retries}), "
                            f"retry after {delay:.1f}s: {e}"
                        )
                        await asyncio.sleep(delay)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code >= 500 and attempt < max_retries - 1:
                        last_exc = e
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"LightRAG returned 5xx (attempt {attempt+1}/{max_retries}), "
                            f"retry after {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise
            raise last_exc
        return wrapper
    return decorator


class LightRAGServerClient:
    """LightRAG Server REST API thin client"""

    def __init__(self):
        self.base_url = os.getenv("LIGHTRAG_API_URL", "http://lightrag:9621")
        self.api_key = os.getenv("LIGHTRAG_API_KEY", "")
        self.timeout = float(os.getenv("LIGHTRAG_API_TIMEOUT", "300"))
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=self.timeout,
        )
        for attempt in range(60):
            try:
                resp = await self._client.get("/health")
                if resp.status_code == 200:
                    logger.info(f"LightRAG Server ready: {self.base_url}")
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(2)
        raise UpstreamServiceError(
            message=f"LightRAG server start timed out (120s): {self.base_url}",
        )

    @_retry_on_transient(max_retries=3, base_delay=1.0)
    async def upload_text(self, text: str, file_source: str) -> dict:
        try:
            resp = await self._client.post(
                "/documents/text",
                json={
                    "text": text,
                    "file_source": file_source,
                },
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"LightRAG ingestion failed: HTTP {e.response.status_code}",
                details={"body": e.response.text[:200]},
            )
        except httpx.TimeoutException:
            raise CapabilityTimeoutError(message="LightRAG ingestion timed out")

    @staticmethod
    def _normalize_doc_ids(value: Any) -> List[str]:
        if isinstance(value, str):
            value = value.strip()
            return [value] if value else []
        if isinstance(value, list):
            doc_ids: List[str] = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    doc_ids.append(item.strip())
                elif isinstance(item, dict):
                    item_id = item.get("id") or item.get("doc_id")
                    if isinstance(item_id, str) and item_id.strip():
                        doc_ids.append(item_id.strip())
            return doc_ids
        return []

    @classmethod
    def extract_doc_ids(cls, data: dict) -> List[str]:
        """Compatible with LightRAG different versions of sync ingestion return format."""
        for key in ("doc_id", "doc_ids", "ids"):
            doc_ids = cls._normalize_doc_ids(data.get(key))
            if doc_ids:
                return doc_ids

        nested = data.get("data")
        if isinstance(nested, dict):
            for key in ("doc_id", "doc_ids", "ids"):
                doc_ids = cls._normalize_doc_ids(nested.get(key))
                if doc_ids:
                    return doc_ids

        return cls._normalize_doc_ids(data.get("documents"))

    async def get_doc_ids_by_track(
        self, track_id: str, max_retries: int = 30, delay: float = 1.0
    ) -> List[str]:
        """Poll track_status, confirm LightRAG processing completed then get doc_id.

        LightRAG 1.4.x 's POST /documents/text returns track_id, actual indexing completes asynchronously in background.
        Must wait here until documents.status=processed, to avoid falsely reporting success when "received but not ingested".
        """
        try:
            max_retries = int(os.getenv("RAG_TRACK_STATUS_RETRIES", str(max_retries)))
        except ValueError:
            logger.warning("RAG_TRACK_STATUS_RETRIES invalid, using default polling count")
        if max_retries <= 0:
            max_retries = 30

        try:
            delay = float(os.getenv("RAG_TRACK_STATUS_DELAY_SECONDS", str(delay)))
        except ValueError:
            logger.warning("RAG_TRACK_STATUS_DELAY_SECONDS invalid, using default polling interval")
        if delay < 0:
            delay = 1.0

        last_statuses: List[dict] = []

        for attempt in range(max_retries):
            try:
                resp = await self._client.get(
                    f"/documents/track_status/{track_id}",
                )
                resp.raise_for_status()
                data = resp.json()
                documents = data.get("documents", [])
                if documents:
                    last_statuses = [
                        {
                            "id": doc.get("id"),
                            "status": str(doc.get("status", "")).lower(),
                            "error": doc.get("error") or doc.get("error_msg"),
                        }
                        for doc in documents
                    ]
                    failed_docs = [
                        status for status in last_statuses
                        if status["status"] == "failed"
                    ]
                    if failed_docs:
                        raise UpstreamServiceError(
                            message="LightRAG document processing failed",
                            details={"track_id": track_id, "documents": failed_docs},
                        )

                    ready_doc_ids = [
                        status["id"] for status in last_statuses
                        if status["id"] and status["status"] == "processed"
                    ]
                    document_ids = [
                        status["id"] for status in last_statuses
                        if status["id"]
                    ]
                    has_status = any(status["status"] for status in last_statuses)

                    if ready_doc_ids and len(ready_doc_ids) == len(document_ids):
                        return ready_doc_ids

                    # Compatible with old track_status: if documents have id but no status field,
                    # can only process by returned doc_id.
                    if document_ids and not has_status:
                        return document_ids

                    if attempt == 0 or (attempt + 1) % 10 == 0:
                        logger.info(
                            f"track_id={track_id} waiting for LightRAG ingestion to complete "
                            f"({attempt + 1}/{max_retries}): {last_statuses}"
                        )
            except httpx.HTTPError as e:
                logger.debug(f"track_id={track_id} polling attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(delay)

        raise UpstreamServiceError(
            message="LightRAG document processing timed out, ingestion completion not confirmed",
            details={"track_id": track_id, "last_statuses": last_statuses},
        )

    @_retry_on_transient(max_retries=3, base_delay=1.0)
    async def query(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        try:
            resp = await self._client.post(
                "/query",
                json={
                    "query": query,
                    "mode": mode,
                    "top_k": top_k,
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"LightRAG query failed: HTTP {e.response.status_code}",
            )

    @_retry_on_transient(max_retries=3, base_delay=1.0)
    async def delete_doc(self, doc_id: str) -> bool:
        resp = await self._client.request(
            "DELETE",
            "/documents/delete_document",
            json={"doc_ids": [doc_id]},
        )
        return resp.status_code == 200

    async def stream_query(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> AsyncGenerator[str, None]:
        """Stream query LightRAG, yield raw JSON line by line (outer wrapper as SSE)"""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=self.timeout,
        ) as client:
            async with client.stream(
                "POST",
                "/query/stream",
                json={"query": query, "mode": mode, "top_k": top_k},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield line

    async def close(self):
        if self._client:
            await self._client.aclose()


# ---------------------------------------------------------------------------
# Video/audio processing: ffmpeg audio extraction + whisper transcription
# ---------------------------------------------------------------------------

# File extension collection (imported from raganything parser, keep in sync)
from raganything.parser import Parser as _RagParser

_VIDEO_EXTENSIONS = _RagParser.VIDEO_FORMATS
_AUDIO_EXTENSIONS = _RagParser.AUDIO_FORMATS
_TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
_TEXT_FILE_ENCODINGS = ("utf-8", "utf-8-sig", "gb18030", "gbk", "latin-1")
_DEFAULT_TEXT_CHUNK_CHARS = 12000

_whisper_model_cache: dict[str, object] = {}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_plain_text_blocks(file_path: str) -> List[Dict[str, str]]:
    """Lightweight reading of plain text files, to avoid md/txt being converted to PDF by MinerU and going through VLM."""
    try:
        max_chars = int(os.getenv("RAG_TEXT_CHUNK_CHARS", str(_DEFAULT_TEXT_CHUNK_CHARS)))
    except ValueError:
        max_chars = _DEFAULT_TEXT_CHUNK_CHARS
    if max_chars <= 0:
        logger.warning(
            f"RAG_TEXT_CHUNK_CHARS={max_chars} invalid, using default value {_DEFAULT_TEXT_CHUNK_CHARS}"
        )
        max_chars = _DEFAULT_TEXT_CHUNK_CHARS

    last_decode_error: Optional[UnicodeDecodeError] = None
    text = ""

    for encoding in _TEXT_FILE_ENCODINGS:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                text = file.read()
            break
        except UnicodeDecodeError as exc:
            last_decode_error = exc
        except OSError as exc:
            raise ValueError(f"Read text file failed: {file_path}: {exc}") from exc
    else:
        raise ValueError(
            f"Text file encoding not recognized: {file_path}: {last_decode_error}"
        ) from last_decode_error

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    chunks: List[Dict[str, str]] = []
    current_parts: List[str] = []
    current_len = 0

    for part in text.split("\n\n"):
        part = part.strip()
        if not part:
            continue

        if len(part) > max_chars:
            if current_parts:
                chunks.append({"type": "text", "text": "\n\n".join(current_parts)})
                current_parts = []
                current_len = 0
            for start in range(0, len(part), max_chars):
                chunks.append({"type": "text", "text": part[start:start + max_chars]})
            continue

        next_len = current_len + len(part) + (2 if current_parts else 0)
        if current_parts and next_len > max_chars:
            chunks.append({"type": "text", "text": "\n\n".join(current_parts)})
            current_parts = [part]
            current_len = len(part)
        else:
            current_parts.append(part)
            current_len = next_len

    if current_parts:
        chunks.append({"type": "text", "text": "\n\n".join(current_parts)})

    return chunks


def _get_whisper_model(model_name: str = "base"):
    """Lazy load whisper model to avoid repeated loading (module-level cache, shared by all workers)"""
    if model_name not in _whisper_model_cache:
        import whisper
        logger.info(f"Loading Whisper model: {model_name}...")
        _whisper_model_cache[model_name] = whisper.load_model(model_name)
        logger.info(f"Whisper model {model_name} ready")
    return _whisper_model_cache[model_name]


def _extract_audio(video_path: str, output_dir: str) -> Optional[str]:
    """Use ffmpeg to extract audio from video into 16kHz mono wav"""
    import subprocess
    from pathlib import Path

    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, f"{Path(video_path).stem}_audio.wav")

    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
        logger.info(f"Audio cache hit: {audio_path}")
        return audio_path

    cmd = [
        "ffmpeg", "-y", "-v", "quiet",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path,
    ]
    try:
        subprocess.run(cmd, check=True, timeout=300)
        logger.info(f"Audio extraction completed: {audio_path}")
        return audio_path
    except subprocess.CalledProcessError as e:
        logger.warning(f"Video has no audio track or ffmpeg failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"Audio extraction exception: {e}")
        return None


def _transcribe_audio(audio_path: str, model_name: str = "base") -> dict:
    """whisper transcribe audio, returns {text, language, segments}"""
    model = _get_whisper_model(model_name)
    result = model.transcribe(
        audio_path,
        language=None,
        task="transcribe",
        verbose=False,
    )
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg.get("start", 0),
            "end": seg.get("end", 0),
            "text": seg.get("text", "").strip(),
        })
    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language", "unknown"),
        "segments": segments,
    }


class LightRAGAdapter(BaseRAGCapability):
    """RAG-Anything parser (parsing) + LightRAG server (search/graph) adapter"""

    # Redis task TTL (7 days, enough to cover the longest RAG parsing task; terminal state info will be written back to PG by knowledge-base)
    _TASK_TTL = 7 * 86400
    _REDIS_TASK_PREFIX = "rag:task:"

    def __init__(self):
        super().__init__()
        self._initialized = False
        self._client: Optional[LightRAGServerClient] = None
        self._parser = None
        self._task_queue: Optional[asyncio.Queue] = None
        self._tasks: Dict[str, dict] = {}
        self._storage_reader: Optional[LightRAGStorageReader] = None
        self._ontology_extractor = None
    # ── Redis task persistence ──

    @classmethod
    def _task_redis_key(cls, task_id: str) -> str:
        return f"{cls._REDIS_TASK_PREFIX}{task_id}"

    async def _save_task(self, task_id: str, task_data: dict):
        """Initial write task to Redis (with TTL)."""
        client = get_redis_client()
        try:
            key = self._task_redis_key(task_id)
            await client.set(key, json.dumps(task_data, default=str), ex=self._TASK_TTL)
        finally:
            await client.aclose()

    async def _get_task(self, task_id: str) -> Optional[dict]:
        """Read task from Redis."""
        client = get_redis_client()
        try:
            data = await client.get(self._task_redis_key(task_id))
            return json.loads(data) if data else None
        finally:
            await client.aclose()

    async def _patch_task(self, task_id: str, **fields):
        """Partially update task fields in Redis (read-modify-write, keep TTL)."""
        client = get_redis_client()
        try:
            key = self._task_redis_key(task_id)
            data = await client.get(key)
            if data:
                task = json.loads(data)
                task.update(fields)
                await client.set(key, json.dumps(task, default=str), keepttl=True)
        finally:
            await client.aclose()

    async def _cleanup_orphan_tasks(self):
        """On startup, mark all pending/processing tasks as failed.

        asyncio.Queue is an in-memory queue, cannot recover after process restart.
        If not cleaned, residual non-terminal tasks in Redis will cause knowledge-base reconciliation to always find
        processing/pending, documents stuck in PARSING.
        After cleanup, knowledge-base gets failed status and can mark documents as FAILED, letting users re-upload.
        """
        client = get_redis_client()
        try:
            orphan_count = 0
            async for key in client.scan_iter(
                match=f"{self._REDIS_TASK_PREFIX}*", count=100
            ):
                data = await client.get(key)
                if not data:
                    continue
                try:
                    task = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if task.get("status") in ("pending", "processing"):
                    task["status"] = "failed"
                    task["error"] = "atomic-rag process restarted, task context lost, please resubmit"
                    await client.set(
                        key, json.dumps(task, default=str), keepttl=True
                    )
                    orphan_count += 1
            if orphan_count:
                logger.warning(
                    f"Startup cleanup: marked {orphan_count} orphan tasks as failed"
                )
            else:
                logger.info("Startup cleanup: no non-terminal orphan tasks")
        except Exception as e:
            # Cleanup failure does not block startup
            logger.exception(f"Startup cleanup of orphan tasks failed (non-fatal, will continue startup): {e}")
        finally:
            await client.aclose()
        

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="rag.lightrag",
            capability_name="RAG-Anything + LightRAG Server",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="Document parsing + LightRAG Server HTTP integration",
        )

    async def initialize(self):
        if self._initialized:
            return

        from raganything.parser import get_parser

        parser_name = os.getenv("RAG_PARSER", "mineru").lower()
        try:
            self._parser = get_parser(parser_name)
        except ValueError as e:
            raise OperationNotSupportedError(
                message=f"Unsupported parser: {parser_name}, options: mineru, docling, paddleocr"
            ) from e

        installed = self._parser.check_installation()
        if not installed:
            logger.warning(
                f"{parser_name} not properly installed, may cause parsing failure"
            )

        self._client = LightRAGServerClient()
        await self._client.initialize()

        # Cleanup residual non-terminal tasks from previous process (asyncio.Queue is lost, cannot continue processing)
        await self._cleanup_orphan_tasks()

        self._task_queue = asyncio.Queue(maxsize=100)
        worker_num = int(os.getenv("RAG_WORKER_NUM", "2"))
        for i in range(worker_num):
            asyncio.create_task(self._ingest_worker(i))

        self._storage_reader = LightRAGStorageReader()

        # Ontology extractor (only initialized when ONTOLOGY_EXTRACT_ENABLED=true)
        if _env_bool("ONTOLOGY_EXTRACT_ENABLED", False):
            try:
                from jonex_core.capability.atomic.ontology import OntologyRegistry

                registry = OntologyRegistry()
                registry.load(
                    os.getenv(
                        "ONTOLOGY_SCHEMA_PATH",
                        "deploy/config/ontology/default.yaml",
                    )
                )
                # Lazy import to avoid circular dependency
                from jonex_core.capability.atomic.rag.ontology_extractor import (
                    OntologyExtractor,
                )

                self._ontology_extractor = OntologyExtractor(registry)
                logger.info("Ontology extractor initialized (ONTOLOGY_EXTRACT_ENABLED=true)")
            except Exception as e:
                logger.warning(
                    f"Ontology extractor initialization failed (non-fatal, will continue startup): {e}"
                )
                self._ontology_extractor = None

        self._initialized = True
        logger.info(f"LightRAG adapter initialization completed (HTTP mode + {parser_name} parser)")

    async def validate_input(self, request: CapabilityRequest) -> bool:
        action = request.payload.get("action")
        return action in {
            "insert", "query", "delete", "get_task_status",
            "get_storage_summary", "get_storage_documents",
            "get_storage_entities", "get_storage_relationships",
            "get_storage_graph_summary", "get_storage_graph",
            "get_document_parse_result",
            "retry_ontology_extract",
        }

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        action = request.payload.get("action")

        if action == "insert":
            result = await self.insert(
                file_path=request.payload["file_path"],
                tenant_id=request.tenant_id,
                output_dir=request.payload.get("output_dir"),
                knowledge_base_id=request.payload.get("knowledge_base_id"),
                document_id=request.payload.get("document_id"),
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data=result
            )

        if action == "query":
            answer = await self.query(
                query=request.payload["query"],
                tenant_id=request.tenant_id,
                mode=request.payload.get("mode", "hybrid"),
                top_k=request.payload.get("top_k", 5),
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data={"answer": answer}
            )

        if action == "delete":
            success = await self.delete(
                doc_id=request.payload["doc_id"],
                tenant_id=request.tenant_id,
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data={"success": success}
            )

        if action == "get_task_status":
            status = await self.get_task_status(
                task_id=request.payload["task_id"],
                tenant_id=request.tenant_id,
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data=status
            )

        if action == "retry_ontology_extract":
            result = await self.retry_ontology_extract(
                document_id=request.payload.get("document_id", ""),
                knowledge_base_id=request.payload.get("knowledge_base_id", ""),
                tenant_id=request.tenant_id,
                file_path=request.payload.get("file_path", ""),
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data=result
            )

        if action == "get_storage_summary":
            scope = request.payload.get("scope", {})
            data = self._storage_reader.get_summary(scope)
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_documents":
            scope = request.payload.get("scope", {}) or {}
            keyword = request.payload.get("keyword")
            # Inject keyword into scope.file_names to enable exact basename matching,
            # avoid same-name files across KBs being mistakenly matched by fuzzy keyword
            if keyword and not scope.get("file_names") and not scope.get("file_paths"):
                scope["file_names"] = [keyword]
            data = self._storage_reader.get_documents(
                scope,
                page=request.payload.get("page", 1),
                page_size=request.payload.get("page_size", 20),
                keyword=keyword,
                status=request.payload.get("status"),
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_entities":
            scope = request.payload.get("scope", {})
            data = self._storage_reader.get_entities(
                scope,
                page=request.payload.get("page", 1),
                page_size=request.payload.get("page_size", 20),
                keyword=request.payload.get("keyword"),
                entity_type=request.payload.get("entity_type"),
                file_path=request.payload.get("file_path"),
                document_id=request.payload.get("document_id"),
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_relationships":
            scope = request.payload.get("scope", {})
            data = self._storage_reader.get_relationships(
                scope,
                page=request.payload.get("page", 1),
                page_size=request.payload.get("page_size", 20),
                keyword=request.payload.get("keyword"),
                file_path=request.payload.get("file_path"),
                document_id=request.payload.get("document_id"),
                source_entity=request.payload.get("source_entity"),
                target_entity=request.payload.get("target_entity"),
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_graph_summary":
            scope = request.payload.get("scope", {})
            data = self._storage_reader.get_graph_summary(scope)
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_graph":
            scope = request.payload.get("scope", {})
            data = self._storage_reader.get_graph(
                scope,
                limit=request.payload.get("limit", 200),
                keyword=request.payload.get("keyword"),
                file_path=request.payload.get("file_path"),
                document_id=request.payload.get("document_id"),
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_document_parse_result":
            scope = request.payload.get("scope", {})
            data = self._storage_reader.get_document_parse_result(scope)
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        return CapabilityResponse.error(
            request_id=request.request_id,
            code=400,
            message=f"Unsupported action: {action}",
        )

    async def insert(
        self,
        file_path: str,
        tenant_id: str,
        output_dir: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> dict:
        if tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")

        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "file_path": file_path,
            "output_dir": output_dir,
            "knowledge_base_id": knowledge_base_id,
            "document_id": document_id,
            "status": "pending",
            "progress": 0.0,
            "lightrag_doc_ids": [],
            "error": None,
        }
        await self._save_task(task_id, task)
        await self._task_queue.put(task)
        logger.info(f"Document enqueued: task_id={task_id}, tenant={tenant_id}, file={file_path}")
        return {
            "task_id": task_id,
            "status": "pending",
            "file_path": file_path,
            "tenant_id": tenant_id,
        }

    async def query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        if tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        return await self._client.query(
            query=query,
            mode=mode,
            top_k=top_k,
        )

    async def delete(self, doc_id: str, tenant_id: str) -> bool:
        if tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        return await self._client.delete_doc(
            doc_id=doc_id,
        )

    async def stream_query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> AsyncGenerator[str, None]:
        """Streaming RAG query"""
        if tenant_id == "default":
            raise TenantIsolationError("Default tenant is prohibited")
        async for line in self._client.stream_query(
            query=query, mode=mode, top_k=top_k
        ):
            yield line

    async def get_task_status(self, task_id: str, tenant_id: str) -> dict:
        task = await self._get_task(task_id)
        if not task:
            logger.debug(
                f"Task does not exist or expired: task_id={task_id}, tenant={tenant_id}"
            )
            return {
                "task_id": task_id,
                "status": "not_found",
                "progress": 0.0,
                "error": "task not found",
            }
        if task.get("tenant_id") != tenant_id:
            raise TenantIsolationError("Cannot query task status of other tenants")
        return {
            "task_id": task_id,
            "status": task.get("status", "unknown"),
            "progress": task.get("progress", 0.0),
            "error": task.get("error"),
            "lightrag_doc_ids": task.get("lightrag_doc_ids", []),
            "ontology_status": task.get("ontology_status"),
            "ontology_error": task.get("ontology_error"),
            "ontology_data": task.get("ontology_data"),
        }

    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:
        """Re-trigger document ontology extraction.

        Enqueue the document with force_ontology_only=True, worker only executes Stage4.
        """
        if not self._ontology_extractor:
            return {"status": "skipped", "reason": "Ontology extraction not enabled (ONTOLOGY_EXTRACT_ENABLED=false)"}

        # Create a task that only does ontology
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "knowledge_base_id": knowledge_base_id,
            "document_id": document_id,
            "file_path": file_path,  # Pass original file_path for Stage4 entity scope filtering
            "output_dir": "",
            "force_ontology_only": True,
            "status": "pending",
            "progress": 0.0,
            "lightrag_doc_ids": [],
        }
        await self._save_task(task_id, task)
        self._task_queue.put_nowait(task)
        logger.info(
            f"Retry ontology extraction enqueued: task_id={task_id}, doc={document_id}, kb={knowledge_base_id}"
        )
        return {"status": "queued", "task_id": task_id}

    async def _ingest_worker(self, worker_id: int):
        logger.info(f"RAG ingest worker {worker_id} started")
        while True:
            task = await self._task_queue.get()
            task_id = task["task_id"]
            try:
                task["status"] = "processing"
                task["progress"] = 0.1
                await self._patch_task(task_id, status="processing", progress=0.1)

                # Auto-detect GPU availability
                device = None
                try:
                    import torch
                    if torch.cuda.is_available():
                        device = "cuda"
                        logger.info(f"task={task_id} detected GPU ({torch.cuda.get_device_name(0)}), enabling GPU acceleration")
                except ImportError:
                    pass

                output_dir = task.get("output_dir") or "/tmp/rag_output"
                whisper_model = os.getenv("WHISPER_MODEL", "base")

                force_ontology_only = task.get("force_ontology_only", False)

                # ── Stage 1: file type detection + parsing ──
                ext = os.path.splitext(task["file_path"])[1].lower()
                is_video = ext in _VIDEO_EXTENSIONS
                is_audio = ext in _AUDIO_EXTENSIONS
                is_plain_text = ext in _TEXT_EXTENSIONS

                if force_ontology_only:
                    # Ontology extraction only: skip file parsing and ingestion, content_list is empty
                    content_list = []
                    logger.info(f"task={task_id} ontology extraction only mode, skipping file parsing")
                elif is_video:
                    content_list = await asyncio.to_thread(
                        self._parser.parse_video,
                        video_path=task["file_path"],
                        output_dir=output_dir,
                    )
                    logger.info(f"task={task_id} video metadata parsing completed")
                elif is_audio:
                    content_list = await asyncio.to_thread(
                        self._parser.parse_audio,
                        audio_path=task["file_path"],
                        output_dir=output_dir,
                    )
                    logger.info(f"task={task_id} audio metadata parsing completed")
                elif is_plain_text:
                    content_list = await asyncio.to_thread(
                        _read_plain_text_blocks,
                        task["file_path"],
                    )
                    logger.info(
                        f"task={task_id} text fast parsing completed, skipping MinerU, "
                        f"got {len(content_list)} chunks"
                    )
                else:
                    parse_method = os.getenv("PARSE_METHOD", "auto")
                    parse_kwargs = {
                        "file_path": task["file_path"],
                        "method": parse_method,
                        "output_dir": output_dir,
                        "device": device,
                    }
                    mineru_backend = os.getenv("MINERU_BACKEND", "").strip()
                    mineru_source = os.getenv("MINERU_SOURCE", "").strip()
                    mineru_timeout = os.getenv("MINERU_TIMEOUT_SECONDS", "").strip()
                    if mineru_backend:
                        parse_kwargs["backend"] = mineru_backend
                    if mineru_source:
                        parse_kwargs["source"] = mineru_source
                    if mineru_timeout:
                        try:
                            parse_kwargs["timeout"] = int(mineru_timeout)
                        except ValueError:
                            logger.warning(
                                f"MINERU_TIMEOUT_SECONDS={mineru_timeout} invalid, using MinerU default timeout"
                            )
                    content_list = await asyncio.to_thread(
                        self._parser.parse_document,
                        **parse_kwargs,
                    )
                logger.info(
                    f"task={task_id} parsing completed, got {len(content_list)} blocks"
                )
                task["progress"] = 0.3
                await self._patch_task(task_id, progress=0.3)

                # ── Stage 2 + Stage 3: video/audio ASR + push text to LightRAG ──
                # Note: force_ontology_only mode skips this part
                if force_ontology_only:
                    lightrag_doc_ids = task.get("lightrag_doc_ids", [])
                elif is_video:
                    audio_path = await asyncio.to_thread(
                        _extract_audio, task["file_path"], output_dir
                    )
                    if audio_path:
                        task["progress"] = 0.4
                        await self._patch_task(task_id, progress=0.4)
                        asr_result = await asyncio.to_thread(
                            _transcribe_audio, audio_path, whisper_model
                        )
                        transcript = asr_result.get("text", "")
                        if transcript:
                            content_list.append({
                                "type": "text",
                                "text": f"[Video transcription] Language: {asr_result.get('language', 'unknown')}\n\n{transcript}",
                            })
                            logger.info(
                                f"task={task_id} video ASR completed: lang={asr_result.get('language')}, "
                                f"{len(transcript)} chars"
                            )
                        task["progress"] = 0.5
                        await self._patch_task(task_id, progress=0.5)
                    else:
                        logger.info(f"task={task_id} video has no audio track, only pushing metadata")

                elif is_audio:
                    task["progress"] = 0.4
                    await self._patch_task(task_id, progress=0.4)
                    asr_result = await asyncio.to_thread(
                        _transcribe_audio, task["file_path"], whisper_model
                    )
                    transcript = asr_result.get("text", "")
                    if transcript:
                        content_list.append({
                            "type": "text",
                            "text": f"[Audio transcription] Language: {asr_result.get('language', 'unknown')}\n\n{transcript}",
                        })
                        logger.info(
                            f"task={task_id} audio ASR completed: lang={asr_result.get('language')}, "
                            f"{len(transcript)} chars"
                        )
                    task["progress"] = 0.5
                    await self._patch_task(task_id, progress=0.5)

                # ── Stage 3: push text to LightRAG ──
                lightrag_doc_ids: List[str] = []
                text_chunk_count = 0
                uploaded_chunk_count = 0
                upload_errors: List[str] = []
                require_doc_ids = _env_bool("RAG_REQUIRE_DOC_IDS", True)

                for idx, chunk in enumerate(content_list):
                    if chunk.get("type") == "table":
                        # Convert table block to plain text: header + row data + footnote
                        table_text = ""
                        caption = chunk.get("table_caption", "") or ""
                        if caption:
                            table_text += f"{caption}\n"
                        body = chunk.get("table_body", []) or []
                        if body:
                            # Each row joined with tab
                            for row in body:
                                row_text = "\t".join(str(c) for c in row if c is not None)
                                if row_text.strip():
                                    table_text += row_text + "\n"
                        footnote = chunk.get("table_footnote", "") or ""
                        if footnote:
                            table_text += f"\n{footnote}"
                        text = table_text.strip()
                        if not text:
                            continue
                    else:
                        if chunk.get("type") != "text":
                            continue
                        text = chunk.get("text", "")
                        if not text.strip():
                            continue
                    text_chunk_count += 1
                    file_source = (
                        f"kb={task.get('knowledge_base_id') or ''}"
                        f"|doc={task.get('document_id') or ''}"
                        f"|tenant={task['tenant_id']}"
                        f"|file={task['file_path']}"
                        f"|chunk={idx}"
                    )
                    try:
                        result = await self._client.upload_text(
                            text=text,
                            file_source=file_source,
                        )
                        result_status = str(result.get("status", "")).lower()
                        if result_status in {"failed", "failure", "error"}:
                            raise UpstreamServiceError(
                                message="LightRAG rejected ingestion request",
                                details={"response": result},
                            )

                        track_id = result.get("track_id")
                        doc_ids = self._client.extract_doc_ids(result)

                        if doc_ids:
                            lightrag_doc_ids.extend(doc_ids)
                        elif track_id:
                            try:
                                doc_ids = await self._client.get_doc_ids_by_track(track_id)
                            except UpstreamServiceError:
                                if require_doc_ids:
                                    raise
                                logger.warning(
                                    f"task={task_id} chunk {idx} track_id={track_id} "
                                    "doc_id not confirmed, treating HTTP upload as success"
                                )
                                doc_ids = []
                            if require_doc_ids and not doc_ids:
                                raise UpstreamServiceError(
                                    message="LightRAG received text, but no confirmable doc_id returned",
                                    details={"track_id": track_id},
                                )
                            lightrag_doc_ids.extend(doc_ids)
                        else:
                            if require_doc_ids:
                                raise UpstreamServiceError(
                                    message="LightRAG ingestion response missing doc_id/track_id, cannot confirm ingestion result",
                                    details={"response": result},
                                )
                            logger.warning(
                                f"task={task_id} chunk {idx} missing doc_id/track_id, "
                                "treating HTTP upload as success"
                            )
                        uploaded_chunk_count += 1
                    except Exception as e:
                        detail = ""
                        if isinstance(e, UpstreamServiceError) and e.details:
                            detail = f" | {e.details}"
                        logger.warning(
                            f"task={task_id} chunk {idx} upload failed (recorded): {e}{detail}"
                        )
                        task["error"] = f"chunk {idx} failed: {e}"
                        await self._patch_task(task_id, error=task["error"])
                        upload_errors.append(f"chunk {idx}: {e}{detail}")

                task["lightrag_doc_ids"] = lightrag_doc_ids

                if not force_ontology_only:
                    if text_chunk_count == 0:
                        raise ValueError("Parsing completed but no text extractable for ingestion")
                    if uploaded_chunk_count == 0:
                        raise UpstreamServiceError(
                            message="LightRAG ingestion failed: no text chunk uploaded successfully",
                            details={"errors": upload_errors[:5]},
                        )
                    if upload_errors:
                        raise UpstreamServiceError(
                            message=(
                                f"LightRAG ingestion partially failed: "
                                f"{len(upload_errors)}/{text_chunk_count} text chunks failed"
                            ),
                            details={"errors": upload_errors[:5]},
                        )

                # ── Stage 4: ontology extraction (only executes when ONTOLOGY_EXTRACT_ENABLED=true) ──
                if self._ontology_extractor:
                    try:
                        # Read LightRAG extracted entities from shared volume (pagination loop, prevent truncation)
                        all_entities = []
                        page = 1
                        while True:
                            batch = self._storage_reader.get_entities(
                                scope={
                                    "file_paths": [task.get("file_path", "")]
                                },
                                page=page,
                                page_size=500,
                            )
                            items = batch.get("items", [])
                            if not items:
                                break
                            all_entities.extend(items)
                            page += 1

                        if not all_entities:
                            # No candidate entities = terminal state, mark failed to avoid KB layer infinite retry
                            await self._patch_task(
                                task_id,
                                ontology_status="failed",
                                ontology_error="No candidate entities found in LightRAG storage, cannot extract ontology",
                            )
                            logger.info(
                                f"task={task_id} no candidate entities yet, ontology status set to pending"
                            )
                        else:
                            scope_info = {
                                "tenant_id": task["tenant_id"],
                                "knowledge_base_id": task.get(
                                    "knowledge_base_id", ""
                                ),
                                "document_id": task.get("document_id", ""),
                            }
                            result = await self._ontology_extractor.extract(
                                content_list=content_list,
                                lightrag_entities=all_entities,
                                scope=scope_info,
                            )
                            ontology_status = (
                                "completed"
                                if not result.errors
                                else "failed"
                            )
                            ontology_data = {
                                "entities": [
                                    {
                                        "canonical_name": e.canonical_name,
                                        "entity_type": e.entity_type,
                                        "aliases": e.aliases,
                                        "attributes": e.attributes,
                                        "confidence": e.confidence,
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
                            await self._patch_task(
                                task_id,
                                ontology_status=ontology_status,
                                ontology_data=ontology_data,
                                ontology_error=str(result.errors[:1])
                                if result.errors
                                else None,
                            )
                            logger.info(
                                f"task={task_id} ontology extraction completed: "
                                f"{len(result.entities)} entities, "
                                f"{len(result.relations)} relations, "
                                f"status={ontology_status}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"task={task_id} ontology extraction failed (non-fatal): {e}"
                        )
                        await self._patch_task(
                            task_id,
                            ontology_status="failed",
                            ontology_error=str(e)[:500],
                        )

                task["status"] = "completed"
                task["progress"] = 1.0
                await self._patch_task(
                    task_id,
                    status="completed",
                    progress=1.0,
                    lightrag_doc_ids=lightrag_doc_ids,
                )
                logger.info(
                    f"task={task_id} completed, submitted {uploaded_chunk_count} chunks, "
                    f"obtained {len(lightrag_doc_ids)} doc_ids"
                )

                await self._send_webhook(
                    task_id=task_id,
                    tenant_id=task["tenant_id"],
                    status=task["status"],
                    doc_ids=lightrag_doc_ids,
                )

            except Exception as e:
                task["status"] = "failed"
                task["error"] = str(e)
                await self._patch_task(task_id, status="failed", error=str(e))
                logger.exception(f"task={task_id} failed: {e}")
                await self._send_webhook(
                    task_id=task_id,
                    tenant_id=task["tenant_id"],
                    status=task["status"],
                    doc_ids=task.get("lightrag_doc_ids", []),
                    error=task["error"],
                )
            finally:
                self._task_queue.task_done()

    def register_routes(self, app) -> None:
        """Register streaming query endpoint (internal NDJSON, Gateway outer wrapper as SSE)"""
        from fastapi.responses import StreamingResponse

        @app.get("/query/stream")
        async def stream_query_endpoint(
            query: str = "",
            mode: str = "hybrid",
            top_k: int = 5,
            tenant_id: str = "default",
        ):
            async def _generate():
                async for line in self.stream_query(
                    query=query, tenant_id=tenant_id, mode=mode, top_k=top_k
                ):
                    yield line + "\n"

            return StreamingResponse(_generate(), media_type="application/x-ndjson")

    async def _send_webhook(
        self,
        task_id: str,
        tenant_id: str,
        status: str,
        doc_ids: list,
        error: Optional[str] = None,
    ):
        webhook_url = os.getenv("RAG_WEBHOOK_URL", "")
        if not webhook_url:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    webhook_url,
                    json={
                        "task_id": task_id,
                        "tenant_id": tenant_id,
                        "status": status,
                        "doc_ids": doc_ids,
                        "error": error,
                    },
                )
        except httpx.HTTPError as e:
            logger.warning(f"Webhook callback failed (non-fatal): {e}")
