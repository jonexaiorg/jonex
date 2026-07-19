#!/usr/bin/python3



from __future__ import annotations

import hashlib
import json
import os
import asyncio
import re
import time
import types
import urllib.parse
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, AsyncGenerator, Optional, Dict, List

import httpx

from jonex_core.capability.atomic.rag.base import BaseRAGCapability
from jonex_core.capability.atomic.rag.graph_reader import LightRAGGraphReader
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)
from jonex_core.common import get_logger, require_tenant
from jonex_core.common.file_source_util import (
    build_file_source,
    lightrag_workspace,
    parse_file_source,
)
from jonex_core.common.cache import get_redis_client
from jonex_core.common.timing import StageTimer
from jonex_core.common.exceptions import (
    UpstreamServiceError,
    CapabilityTimeoutError,
    InvalidParameterError,
    TenantIsolationError,
    OperationNotSupportedError,
)

logger = get_logger("capability.atomic.rag.lightrag")




_LIGHTRAG_MIN_QUERY_LEN = max(3, int(os.getenv("RAG_MIN_QUERY_LEN", "3")))


def _safe_tenant_id(tenant_id: str) -> str:

    return re.sub(r"[^A-Za-z0-9_-]", "_", tenant_id or "")


def _require_knowledge_base_id(knowledge_base_id: Optional[str]) -> str:
    return (knowledge_base_id or "").strip()


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
                            f"LightRAG call to {func.__name__} failed (attempt {attempt+1}/{max_retries}), "
                            f"retrying in {delay:.1f}s: {e}"
                        )
                        await asyncio.sleep(delay)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code >= 500 and attempt < max_retries - 1:
                        last_exc = e
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"LightRAG returned 5xx (attempt {attempt+1}/{max_retries}), "
                            f"retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise
            raise last_exc
        return wrapper
    return decorator


async def _delete_doc_with_retry(client: "LightRAGServerClient", doc_id: str, workspace: str = "", max_retries: int = 5, base_delay: float = 2.0) -> bool:

    last_status = None
    delete_headers = {"LIGHTRAG-WORKSPACE": workspace} if workspace else None
    for attempt in range(max_retries):
        try:
            resp = await client._client.request(
                "DELETE",
                "/documents/delete_document",
                json={
                    "doc_ids": [doc_id],
                    "delete_file": True,
                    "delete_llm_cache": True,
                },
                headers=delete_headers,
            )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"LightRAG delete_doc({doc_id}) network error (attempt {attempt+1}/{max_retries}), "
                    f"retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)
                continue
            raise UpstreamServiceError(message=f"LightRAG 删除文档失败: {e}")

        if resp.status_code >= 500:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"LightRAG delete_doc({doc_id}) HTTP {resp.status_code} (attempt {attempt+1}/{max_retries}), "
                    f"retrying in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                continue
            raise UpstreamServiceError(
                message=f"LightRAG 删除文档失败: HTTP {resp.status_code}"
            )

        try:
            body = resp.json()
        except Exception:
            body = {}
        last_status = body.get("status", "")

        if last_status == "deletion_started":
            logger.info(f"LightRAG delete_doc({doc_id}) started background deletion")
            return True

        if last_status == "busy":
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"LightRAG is busy with another task; delete_doc({doc_id}) "
                    f"(attempt {attempt+1}/{max_retries}), {delay:.1f}s before retry"
                )
                await asyncio.sleep(delay)
                continue
            raise UpstreamServiceError(
                message=f"LightRAG 删除文档失败: 服务持续繁忙，已重试 {max_retries} 次"
            )


        logger.warning(
            f"LightRAG delete_doc({doc_id}) returned unknown status={last_status}; treating it as successful"
        )
        return True

    raise UpstreamServiceError(
        message=f"LightRAG 删除文档失败: 服务繁忙，已重试 {max_retries} 次"
    )


def _jonex_query_headers(
    tenant_id: str = "",
    kb_id: str = "",
    trace_id: str = "",
    scene: str = "lightrag_query",
) -> dict:

    headers = {"X-Jonex-Scene": scene}
    if tenant_id:
        headers["X-Jonex-Tenant-Id"] = tenant_id
    if kb_id:
        headers["X-Jonex-Kb-Id"] = kb_id
    if trace_id:
        headers["X-Jonex-Trace-Id"] = trace_id
    workspace = lightrag_workspace(tenant_id, kb_id)
    if workspace:
        headers["LIGHTRAG-WORKSPACE"] = workspace
    return headers


def _workspace_headers(tenant_id: str = "", kb_id: str = "") -> dict:

    workspace = lightrag_workspace(tenant_id, kb_id)
    return {"LIGHTRAG-WORKSPACE": workspace} if workspace else {}


class LightRAGServerClient:


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
                    logger.info(f"LightRAG Server is ready: {self.base_url}")
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(2)
        raise UpstreamServiceError(
            message=f"LightRAG Server 启动超时（120s）：{self.base_url}",
        )

    @_retry_on_transient(max_retries=3, base_delay=1.0)
    async def upload_text(self, text: str, file_source: str, *, workspace: str = "") -> dict:
        try:
            resp = await self._client.post(
                "/documents/text",
                json={
                    "text": text,
                    "file_source": file_source,
                },
                headers={"LIGHTRAG-WORKSPACE": workspace} if workspace else None,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"LightRAG 入库失败: HTTP {e.response.status_code}",
                details={"body": e.response.text[:200]},
            )
        except httpx.TimeoutException:
            raise CapabilityTimeoutError(message="LightRAG 入库超时")

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

    @staticmethod
    def _parse_track_status(data: dict) -> tuple:

        documents = data.get("documents", [])
        if not documents:
            return ([], False, None)

        last_statuses = [
            {
                "id": doc.get("id"),
                "status": str(doc.get("status", "")).lower(),
                "error": doc.get("error") or doc.get("error_msg"),
            }
            for doc in documents
        ]

        failed_docs = [s for s in last_statuses if s["status"] == "failed"]
        if failed_docs:
            return ([], True, f"LightRAG 文档处理失败: {failed_docs}")

        ready_doc_ids = [s["id"] for s in last_statuses if s["id"] and s["status"] == "processed"]
        document_ids = [s["id"] for s in last_statuses if s["id"]]
        has_status = any(s["status"] for s in last_statuses)

        if ready_doc_ids and len(ready_doc_ids) == len(document_ids):
            return (ready_doc_ids, True, None)


        if document_ids and not has_status:
            return (document_ids, True, None)

        return ([], False, None)

    async def get_doc_ids_by_track(
        self, track_id: str, max_retries: int = 30, delay: float = 1.0, *, workspace: str = ""
    ) -> List[str]:

        try:
            max_retries = int(os.getenv("RAG_TRACK_STATUS_RETRIES", str(max_retries)))
        except ValueError:
            logger.warning("Invalid RAG_TRACK_STATUS_RETRIES; using the default polling attempt count")
        if max_retries <= 0:
            max_retries = 30

        try:
            delay = float(os.getenv("RAG_TRACK_STATUS_DELAY_SECONDS", str(delay)))
        except ValueError:
            logger.warning("Invalid RAG_TRACK_STATUS_DELAY_SECONDS; using the default polling interval")
        if delay < 0:
            delay = 1.0

        last_statuses: List[dict] = []

        for attempt in range(max_retries):
            try:
                resp = await self._client.get(
                    f"/documents/track_status/{track_id}",
                    headers={"LIGHTRAG-WORKSPACE": workspace} if workspace else None,
                )
                resp.raise_for_status()
                data = resp.json()
                ready_ids, all_done, failed_reason = self._parse_track_status(data)

                if failed_reason:
                    documents = data.get("documents", [])
                    failed_docs = [
                        {"id": doc.get("id"), "status": str(doc.get("status", "")).lower()}
                        for doc in documents
                        if str(doc.get("status", "")).lower() == "failed"
                    ]
                    raise UpstreamServiceError(
                        message="LightRAG 文档处理失败",
                        details={"track_id": track_id, "documents": failed_docs},
                    )

                if all_done:
                    return ready_ids


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

                if attempt == 0 or (attempt + 1) % 10 == 0:
                    logger.info(
                        f"track_id={track_id} waiting for LightRAG ingestion to complete "
                        f"({attempt + 1}/{max_retries}): {last_statuses}"
                    )
            except httpx.HTTPError as e:
                logger.debug(f"track_id={track_id} polling attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(delay)

        raise UpstreamServiceError(
            message="LightRAG 文档处理超时，未确认入库完成",
            details={"track_id": track_id, "last_statuses": last_statuses},
        )

    async def get_doc_ids_by_tracks(
        self,
        track_ids: List[str],
        *,
        workspace: str = "",
    ) -> tuple:

        if not track_ids:
            return ({}, {})

        batch_timeout_raw = os.getenv("RAG_TRACK_BATCH_TIMEOUT_SECONDS", "").strip()
        if batch_timeout_raw:
            try:
                batch_timeout = int(batch_timeout_raw)
            except ValueError:
                batch_timeout = 1800
        else:

            try:
                _retries = int(os.getenv("RAG_TRACK_STATUS_RETRIES", "30"))
            except ValueError:
                _retries = 30
            try:
                _delay = float(os.getenv("RAG_TRACK_STATUS_DELAY_SECONDS", "1"))
            except ValueError:
                _delay = 1.0
            batch_timeout = max(int(_retries * _delay), 60)
        if batch_timeout <= 0:
            batch_timeout = 1800

        try:
            poll_concurrency = int(os.getenv("RAG_TRACK_POLL_CONCURRENCY", "8"))
        except ValueError:
            poll_concurrency = 8
        if poll_concurrency <= 0:
            poll_concurrency = 8

        try:
            poll_delay = float(os.getenv("RAG_TRACK_STATUS_DELAY_SECONDS", "2"))
        except ValueError:
            poll_delay = 2.0
        if poll_delay < 0:
            poll_delay = 2.0

        ok_map: dict[str, list[str]] = {}
        fail_map: dict[str, str] = {}
        remaining: set[str] = set(track_ids)
        deadline = time.monotonic() + batch_timeout
        sem = asyncio.Semaphore(poll_concurrency)
        ws_headers = {"LIGHTRAG-WORKSPACE": workspace} if workspace else None

        async def _poll_one(tid: str):
            async with sem:
                try:
                    resp = await self._client.get(
                        f"/documents/track_status/{tid}",
                        headers=ws_headers,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    ready_ids, all_done, failed_reason = self._parse_track_status(data)
                    return (tid, ready_ids, all_done, failed_reason, None)
                except Exception as e:
                    return (tid, [], False, None, str(e))

        round_num = 0
        while remaining and time.monotonic() < deadline:
            round_num += 1
            tasks = [_poll_one(tid) for tid in remaining]
            results = await asyncio.gather(*tasks)

            for tid, ready_ids, all_done, failed_reason, error in results:
                if error:
                    logger.debug(
                        f"track_id={tid} batch polling request failed in round {round_num}: {error}"
                    )
                    continue

                if failed_reason:
                    fail_map[tid] = f"FAILED:{failed_reason}"
                    remaining.discard(tid)
                elif all_done:
                    ok_map[tid] = ready_ids
                    remaining.discard(tid)

            if remaining and (round_num == 1 or round_num % 10 == 0):
                logger.info(
                    f"Batch polling: {len(remaining)}/{len(track_ids)} tracks still awaiting ingestion completion "
                    f"(round {round_num})"
                )

            if remaining:
                await asyncio.sleep(poll_delay)

        for tid in remaining:
            fail_map[tid] = "TIMEOUT:轮询超时未确认入库完成"

        return (ok_map, fail_map)

    @_retry_on_transient(max_retries=3, base_delay=1.0)
    async def query(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        tenant_id: str = "",
        trace_id: str = "",
    ) -> dict:




        normalized_query = (query or "").strip()
        if len(normalized_query) < _LIGHTRAG_MIN_QUERY_LEN:
            raise InvalidParameterError(
                message=f"查询内容过短，至少需要 {_LIGHTRAG_MIN_QUERY_LEN} 个字符",
                details={"query_length": len(normalized_query)},
            )
        try:
            knowledge_base_id = _require_knowledge_base_id(knowledge_base_id)
            logger.debug(
                "LightRAG query includes knowledge base scope: knowledge_base_id=%s",
                knowledge_base_id,
            )
            resp = await self._client.post(
                "/query",
                json={
                    "query": query,
                    "mode": mode,
                    "top_k": top_k,
                    "include_references": True,
                    "include_chunk_content": True,
                },
                headers=_jonex_query_headers(
                    tenant_id=tenant_id,
                    kb_id=knowledge_base_id,
                    trace_id=trace_id,
                    scene="lightrag_query",
                ),
            )
            resp.raise_for_status()
            data = resp.json()
            refs = []
            for r in (data.get("references") or []):
                parsed = parse_file_source(r.get("file_path", ""))
                if not parsed:
                    continue



                content = r.get("content")
                raw_text = None
                if isinstance(content, list) and content:
                    raw_text = "\n\n".join(c for c in content if c)
                elif isinstance(content, str) and content:
                    raw_text = content
                if raw_text:
                    parsed["text"] = re.sub(r"\s*<!--yx:[0-9a-f]+-->\s*", "", raw_text).strip()
                refs.append(parsed)
            return {
                "answer": data.get("response", ""),
                "references": refs,
            }
        except httpx.HTTPStatusError as e:
            raise UpstreamServiceError(
                message=f"LightRAG 查询失败: HTTP {e.response.status_code}",
            )

    async def delete_doc(self, doc_id: str, *, workspace: str = "") -> bool:
        return await _delete_doc_with_retry(self, doc_id, workspace=workspace)

    async def stream_query(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str = "",
        tenant_id: str = "",
        trace_id: str = "",
    ) -> AsyncGenerator[str, None]:

        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=self.timeout,
        ) as client:
            async with client.stream(
                "POST",
                "/query/stream",
                json={"query": query, "mode": mode, "top_k": top_k},
                headers=_jonex_query_headers(
                    tenant_id=tenant_id,
                    kb_id=knowledge_base_id,
                    trace_id=trace_id,
                    scene="lightrag_query",
                ),
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield line

    async def close(self):
        if self._client:
            await self._client.aclose()







try:
    from raganything.parser import Parser as _RagParser
except ModuleNotFoundError:
    _RagParser = None

if _RagParser is not None:
    _VIDEO_EXTENSIONS = _RagParser.VIDEO_FORMATS
    _AUDIO_EXTENSIONS = _RagParser.AUDIO_FORMATS
else:
    _VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"}
    _AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma"}
_TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
_TEXT_FILE_ENCODINGS = ("utf-8", "utf-8-sig", "gb18030", "gbk", "latin-1")
_DEFAULT_TEXT_CHUNK_CHARS = 12000




_MPS_ENABLED: bool = os.getenv("MPS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


_MPS_SECRET_ID: str = os.getenv("MPS_SECRET_ID") or os.getenv("COS_SECRET_ID", "")
_MPS_SECRET_KEY: str = os.getenv("MPS_SECRET_KEY") or os.getenv("COS_SECRET_KEY", "")
_MPS_COS_BUCKET: str = os.getenv("MPS_COS_BUCKET") or os.getenv("COS_BUCKET", "")

_MPS_COS_REGION: str = (
    os.getenv("MPS_COS_REGION") or os.getenv("MPS_REGION") or os.getenv("COS_REGION", "")
)
_MPS_PROMPT_CATEGORY: str = os.getenv("MPS_PROMPT_CATEGORY", "mps_video_understanding")


def _mps_config_complete() -> bool:

    return all([_MPS_SECRET_ID, _MPS_SECRET_KEY, _MPS_COS_BUCKET, _MPS_COS_REGION])


def _build_mps_cos_url(storage_key: str) -> str:

    bucket = _MPS_COS_BUCKET or os.getenv("COS_BUCKET", "")
    region = _MPS_COS_REGION or os.getenv("COS_REGION", "")
    key = (storage_key or "").lstrip("/")
    if not bucket or not region or not key:
        return ""
    quoted = urllib.parse.quote(key, safe="/")
    return f"https://{bucket}.cos.{region}.myqcloud.com/{quoted}"


def _resolve_video_mps_url(task: dict) -> str:

    explicit = (task.get("mps_video_url") or "").strip()
    if explicit:
        return explicit
    if not (_MPS_ENABLED and _mps_config_complete()):
        return ""
    if (task.get("storage_backend") or "").strip().lower() != "cos":
        return ""
    return _build_mps_cos_url(task.get("storage_key") or "")

_whisper_model_cache: dict[str, object] = {}



_TRANSIENT_PARSE_ERROR_MARKERS = (
    "unexpected_eof_while_reading",
    "eof occurred in violation of protocol",
    "ssl",
    "failed to download mineru result",
    "connection reset",
    "connection aborted",
    "timed out",
    "temporary failure in name resolution",
    "max retries exceeded",
)


def _is_transient_parse_error(exc: BaseException) -> bool:

    import ssl
    import urllib.error


    cur: BaseException | None = exc
    seen = 0
    while cur is not None and seen < 10:
        if isinstance(cur, (ssl.SSLError, urllib.error.URLError, TimeoutError, ConnectionError)):
            return True
        msg = str(cur).lower()
        if any(marker in msg for marker in _TRANSIENT_PARSE_ERROR_MARKERS):
            return True
        cur = cur.__cause__ or cur.__context__
        seen += 1
    return False


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_plain_text_blocks(file_path: str) -> List[Dict[str, Any]]:

    try:
        max_chars = int(os.getenv("RAG_TEXT_CHUNK_CHARS", str(_DEFAULT_TEXT_CHUNK_CHARS)))
    except ValueError:
        max_chars = _DEFAULT_TEXT_CHUNK_CHARS
    if max_chars <= 0:
        logger.warning(
            f"RAG_TEXT_CHUNK_CHARS={max_chars} is invalid; using default value {_DEFAULT_TEXT_CHUNK_CHARS}"
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
            raise ValueError(f"读取文本文件失败: {file_path}: {exc}") from exc
    else:
        raise ValueError(
            f"文本文件编码无法识别: {file_path}: {last_decode_error}"
        ) from last_decode_error

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []


    paragraphs: list[dict[str, Any]] = []
    pos = 0
    for para in text.split("\n\n"):
        stripped = para.strip()
        para_len = len(para)
        if stripped:
            leading_ws = para_len - len(para.lstrip())
            paragraphs.append({
                "text": stripped,
                "char_start": pos + leading_ws,
                "char_end": pos + leading_ws + len(stripped),
            })
        pos += para_len + 2


    chunks: List[Dict[str, Any]] = []
    current_parts: List[str] = []
    current_len = 0
    current_start: int | None = None

    for p in paragraphs:
        if len(p["text"]) > max_chars:
            if current_parts:
                chunks.append({
                    "type": "text",
                    "text": "\n\n".join(current_parts),
                    "char_start": current_start,
                    "char_end": current_start + current_len if current_start is not None else None,
                })
                current_parts = []
                current_len = 0
                current_start = None
            for start in range(0, len(p["text"]), max_chars):
                end = min(start + max_chars, len(p["text"]))
                chunks.append({
                    "type": "text",
                    "text": p["text"][start:end],
                    "char_start": p["char_start"] + start,
                    "char_end": p["char_start"] + end,
                })
            continue

        next_len = current_len + len(p["text"]) + (2 if current_parts else 0)
        if current_parts and next_len > max_chars:
            chunks.append({
                "type": "text",
                "text": "\n\n".join(current_parts),
                "char_start": current_start,
                "char_end": (current_start + current_len) if current_start is not None else None,
            })
            current_parts = [p["text"]]
            current_len = len(p["text"])
            current_start = p["char_start"]
        else:
            if not current_parts:
                current_start = p["char_start"]
            current_parts.append(p["text"])
            current_len = next_len

    if current_parts:
        chunks.append({
            "type": "text",
            "text": "\n\n".join(current_parts),
            "char_start": current_start,
            "char_end": (current_start + current_len) if current_start is not None else None,
        })

    return chunks


def _get_whisper_model(model_name: str = "base"):

    if model_name not in _whisper_model_cache:
        import whisper
        logger.info(f"Loading Whisper model: {model_name}...")
        _whisper_model_cache[model_name] = whisper.load_model(model_name)
        logger.info(f"Whisper model {model_name} is ready")
    return _whisper_model_cache[model_name]


def _extract_audio(video_path: str, output_dir: str) -> Optional[str]:

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
        logger.warning(f"Audio extraction error: {e}")
        return None


def _build_asr_content_list(asr_result: dict, prefix: str, max_chars: int = 2000) -> list[dict]:

    segments = asr_result.get("segments", [])
    if not segments:
        transcript = (asr_result.get("text") or "").strip()
        if transcript:
            return [{"type": "text", "text": f"{prefix}\n\n{transcript}"}]
        return []

    chunks: list[dict] = []
    buf: list[str] = []
    buf_start: float | None = None
    buf_end: float | None = None
    buf_len = 0

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)
        seg_text = text

        next_len = buf_len + len(seg_text) + (2 if buf else 0)
        if buf and next_len > max_chars:
            chunks.append({
                "type": "text",
                "text": f"{prefix}\n\n" + "\n\n".join(buf),
                "time_start": buf_start,
                "time_end": buf_end,
            })
            buf = [seg_text]
            buf_len = len(seg_text)
            buf_start = seg_start
            buf_end = seg_end
        else:
            if not buf:
                buf_start = seg_start
            buf.append(seg_text)
            buf_len = next_len
            buf_end = seg_end

    if buf:
        chunks.append({
            "type": "text",
            "text": f"{prefix}\n\n" + "\n\n".join(buf),
            "time_start": buf_start,
            "time_end": buf_end,
        })

    return chunks


def _transcribe_audio(audio_path: str, model_name: str = "base") -> dict:

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





_mps_backend_cache: dict[str, object] = {}


def _get_mps_backend() -> object | None:

    if not _MPS_ENABLED:
        return None
    if not all([_MPS_SECRET_ID, _MPS_SECRET_KEY, _MPS_COS_BUCKET, _MPS_COS_REGION]):
        logger.warning("MPS configuration is incomplete; skipping intelligent video analysis")
        return None
    cache_key = f"{_MPS_SECRET_ID}:{_MPS_COS_BUCKET}"
    if cache_key not in _mps_backend_cache:
        try:
            from raganything.video_analysis.backends.mps import MPSVideoBackend

            cfg = types.SimpleNamespace(
                mps_secret_id=_MPS_SECRET_ID,
                mps_secret_key=_MPS_SECRET_KEY,
                mps_cos_bucket=_MPS_COS_BUCKET,
                mps_cos_region=_MPS_COS_REGION,
                mps_prompt_category=_MPS_PROMPT_CATEGORY,
            )
            _mps_backend_cache[cache_key] = MPSVideoBackend(cfg)
            logger.info("MPS video analysis backend is ready")
        except Exception as e:
            logger.error(f"MPS backend initialization failed: {e}")
            _mps_backend_cache[cache_key] = None
    return _mps_backend_cache.get(cache_key)


async def _run_mps_analysis(video_cos_url: str) -> list[dict]:

    backend = _get_mps_backend()
    if backend is None:
        return []

    result = await backend.analyze_video(video_path=video_cos_url)
    chunks: list[dict] = []
    file_name = Path(video_cos_url).name


    if result.summary:
        chunks.append({
            "type": "text",
            "text": (
                f"【视频文件】{file_name}\n"
                f"【视频摘要】{result.summary}\n"
            ),
        })


    scenes = result.scenes or []
    for i, scene in enumerate(scenes):
        logger.info(f"MPS analyzing scene: {i+1}/{len(scenes)}")
        logger.info(f"MPS analyzed scene: {scene}")
        desc = scene.get("description", "")
        start = scene.get("start_time", 0)
        end = scene.get("end_time", 0)

        def _fmt(sec: float) -> str:
            m, s = divmod(int(sec), 60)
            return f"{m:02d}:{s:02d}"

        scene_lines = [f"[视频片段 {i+1}/{len(scenes)}]"]
        scene_lines.append(f"时间: {_fmt(start)} - {_fmt(end)}")
        if scene.get("name"):
            scene_lines.append(f"名称: {scene['name']}")
        if scene.get("structure_type"):
            scene_lines.append(f"类型: {scene['structure_type']}")
        if desc:
            scene_lines.append(f"\n描述: {desc}")

        scene_chunk: dict[str, Any] = {
            "type": "text",
            "text": "\n".join(scene_lines),
        }



        if (start or 0) or (end or 0):
            scene_chunk["time_start"] = float(start or 0)
            scene_chunk["time_end"] = float(end or start or 0)
        logger.info(f"MPS analyzed scene_chunk: {scene_chunk}")
        chunks.append(scene_chunk)

    logger.info(
        f"MPS analysis completed: {len(scenes)} scenes, "
        f"{len(chunks)} text chunks generated"
    )
    return chunks


class LightRAGAdapter(BaseRAGCapability):



    _TASK_TTL = 7 * 86400
    _REDIS_TASK_PREFIX = "rag:task:"

    def __init__(self):
        super().__init__()
        self._initialized = False
        self._client: Optional[LightRAGServerClient] = None
        self._parser = None
        self._parser_name: str = "mineru"
        self._task_queue: Optional[asyncio.Queue] = None
        self._tasks: Dict[str, dict] = {}
        self._graph_reader: Optional[LightRAGGraphReader] = None
        self._ontology_extractor = None


    @classmethod
    def _task_redis_key(cls, task_id: str) -> str:
        return f"{cls._REDIS_TASK_PREFIX}{task_id}"

    async def _save_task(self, task_id: str, task_data: dict):

        client = get_redis_client()
        try:
            key = self._task_redis_key(task_id)
            await client.set(key, json.dumps(task_data, default=str), ex=self._TASK_TTL)
        finally:
            await client.aclose()

    async def _get_task(self, task_id: str) -> Optional[dict]:

        client = get_redis_client()
        try:
            data = await client.get(self._task_redis_key(task_id))
            return json.loads(data) if data else None
        finally:
            await client.aclose()

    async def _patch_task(self, task_id: str, **fields):

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
                    task["error"] = "atomic-rag 进程重启，任务上下文丢失，请重新提交"
                    await client.set(
                        key, json.dumps(task, default=str), keepttl=True
                    )
                    orphan_count += 1
            if orphan_count:
                logger.warning(
                    f"Startup cleanup: marking {orphan_count} orphan tasks as failed"
                )
            else:
                logger.info("Startup cleanup: no orphan tasks in a non-terminal state")
        except Exception as e:

            logger.exception(f"Failed to clean up orphan tasks during startup (non-fatal; startup will continue): {e}")
        finally:
            await client.aclose()


    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="rag.lightrag",
            capability_name="RAG-Anything + LightRAG Server",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="文档解析 + LightRAG Server HTTP 集成",
        )

    def _require_storage_scope(self, request: CapabilityRequest) -> dict:
        scope = dict(request.payload.get("scope") or {})
        tenant_id = require_tenant(scope.get("tenant_id") or request.tenant_id)
        scope["tenant_id"] = tenant_id
        scope.setdefault("scope_mode", "knowledge_base")

        scope["knowledge_base_id"] = _require_knowledge_base_id(
            scope.get("knowledge_base_id")
            or request.payload.get("knowledge_base_id")
        )
        return scope

    def _reader(self) -> LightRAGGraphReader:

        if self._graph_reader is None:
            self._graph_reader = LightRAGGraphReader()
        return self._graph_reader

    async def initialize(self):
        if self._initialized:
            return

        try:
            from raganything.parser import get_parser
        except ModuleNotFoundError as e:
            raise OperationNotSupportedError(
                message="RAG 文档解析依赖 raganything 未安装，无法初始化 LightRAG 解析器"
            ) from e

        parser_name = os.getenv("RAG_PARSER", "mineru").lower()
        self._parser_name = parser_name
        try:
            self._parser = get_parser(parser_name)
        except ValueError as e:
            raise OperationNotSupportedError(
                message=(
                    f"不支持的解析器: {parser_name}，可选: "
                    "mineru（本地 CLI）, mineru_online（mineru.net 云）, "
                    "mineru_selfhost（内网 mineru-api）, docling, paddleocr"
                )
            ) from e

        installed = self._parser.check_installation()
        if not installed:
            logger.warning(
                f"{parser_name} is not installed correctly, which may cause parsing failures"
            )

        self._client = LightRAGServerClient()
        await self._client.initialize()


        await self._cleanup_orphan_tasks()

        self._task_queue = asyncio.Queue(maxsize=100)
        worker_num = int(os.getenv("RAG_WORKER_NUM", "2"))
        for i in range(worker_num):
            asyncio.create_task(self._ingest_worker(i))

        self._graph_reader = LightRAGGraphReader()


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

                from jonex_core.capability.atomic.rag.ontology_extractor import (
                    OntologyExtractor,
                )

                self._ontology_extractor = OntologyExtractor(registry)
                logger.info("Ontology extractor initialized (ONTOLOGY_EXTRACT_ENABLED=true)")
            except Exception as e:
                logger.warning(
                    f"Ontology extractor initialization failed (non-fatal; startup will continue): {e}"
                )
                self._ontology_extractor = None

        self._initialized = True
        logger.info(f"LightRAG adapter initialized (HTTP mode + {parser_name} parser)")

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
        tenant_id = require_tenant(request.tenant_id)

        if action == "insert":
            result = await self.insert(
                file_path=request.payload.get("file_path") or None,
                tenant_id=tenant_id,
                output_dir=request.payload.get("output_dir"),
                knowledge_base_id=_require_knowledge_base_id(
                    request.payload.get("knowledge_base_id")
                ),
                document_id=request.payload.get("document_id"),
                ontology_schema=request.payload.get("ontology_schema"),
                storage_backend=request.payload.get("storage_backend", "local"),
                storage_key=request.payload.get("storage_key"),
                mps_video_url=request.payload.get("mps_video_url") or None,
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data=result
            )

        if action == "query":
            detailed = await self.query_detailed(
                query=request.payload["query"],
                tenant_id=tenant_id,
                mode=request.payload.get("mode", "hybrid"),
                top_k=request.payload.get("top_k", 5),
                knowledge_base_id=_require_knowledge_base_id(
                    request.payload.get("knowledge_base_id")
                ),

                trace_id=request.payload.get("trace_id") or request.request_id or "",
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data=detailed
            )

        if action == "delete":
            success = await self.delete(
                doc_id=request.payload["doc_id"],
                tenant_id=tenant_id,
                knowledge_base_id=_require_knowledge_base_id(
                    request.payload.get("knowledge_base_id")
                ),
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data={"success": success}
            )

        if action == "get_task_status":
            status = await self.get_task_status(
                task_id=request.payload["task_id"],
                tenant_id=tenant_id,
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data=status
            )

        if action == "retry_ontology_extract":
            result = await self.retry_ontology_extract(
                document_id=request.payload["document_id"],
                knowledge_base_id=_require_knowledge_base_id(
                    request.payload.get("knowledge_base_id")
                ),
                tenant_id=request.tenant_id,
                file_path=request.payload.get("file_path", ""),
            )
            return CapabilityResponse.ok(
                request_id=request.request_id, data=result
            )

        if action == "get_storage_summary":
            scope = self._require_storage_scope(request)
            data = await self._reader().get_summary(scope)
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_documents":
            scope = self._require_storage_scope(request)
            keyword = request.payload.get("keyword")
            data = await self._reader().get_documents(
                scope,
                page=request.payload.get("page", 1),
                page_size=request.payload.get("page_size", 20),
                keyword=keyword,
                status=request.payload.get("status"),
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_entities":
            scope = self._require_storage_scope(request)
            data = await self._reader().get_entities(
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
            scope = self._require_storage_scope(request)
            data = await self._reader().get_relationships(
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
            scope = self._require_storage_scope(request)
            data = await self._reader().get_graph_summary(scope)
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_storage_graph":
            scope = self._require_storage_scope(request)
            data = await self._reader().get_graph(
                scope,
                limit=request.payload.get("limit", 200),
                keyword=request.payload.get("keyword"),
                file_path=request.payload.get("file_path"),
                document_id=request.payload.get("document_id"),
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        if action == "get_document_parse_result":
            scope = self._require_storage_scope(request)
            document_id = request.payload.get("document_id")
            if document_id and document_id not in (scope.get("document_ids") or []):
                scope["document_ids"] = [document_id]
            data = await self._reader().get_document_parse_result(scope)
            return CapabilityResponse.ok(request_id=request.request_id, data=data)

        return CapabilityResponse.error(
            request_id=request.request_id,
            code=400,
            message=f"不支持的 action: {action}",
        )

    async def insert(
        self,
        file_path: Optional[str] = None,
        tenant_id: str = "default",
        knowledge_base_id: str = "",
        output_dir: Optional[str] = None,
        document_id: Optional[str] = None,
        ontology_schema: Optional[dict] = None,
        storage_backend: str = "local",
        storage_key: Optional[str] = None,
        mps_video_url: Optional[str] = None,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = _require_knowledge_base_id(knowledge_base_id)
        if not file_path and not mps_video_url:
            raise InvalidParameterError(
                message="file_path 和 mps_video_url 至少传一个",
            )

        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "file_path": file_path,
            "mps_video_url": mps_video_url,
            "output_dir": output_dir,
            "knowledge_base_id": knowledge_base_id,
            "document_id": document_id,
            "storage_backend": storage_backend,
            "storage_key": storage_key or file_path or mps_video_url or "unknown",
            "status": "pending",
            "progress": 0.0,
            "lightrag_doc_ids": [],
            "error": None,
            "ontology_schema": ontology_schema,
        }
        await self._save_task(task_id, task)
        await self._task_queue.put(task)
        source = mps_video_url or file_path or "unknown"
        logger.info(f"Document enqueued: task_id={task_id}, tenant={tenant_id}, source={source}")
        return {
            "task_id": task_id,
            "status": "pending",
            "file_path": file_path,
            "mps_video_url": mps_video_url,
            "tenant_id": tenant_id,
        }

    async def query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> str:
        require_tenant(tenant_id)
        knowledge_base_id = _require_knowledge_base_id(knowledge_base_id)
        result = await self._client.query(
            query=query,
            mode=mode,
            top_k=top_k,
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id,
            trace_id=trace_id,
        )
        return result["answer"] if isinstance(result, dict) else result

    async def query_detailed(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
        trace_id: str = "",
    ) -> dict:

        require_tenant(tenant_id)
        knowledge_base_id = _require_knowledge_base_id(knowledge_base_id)
        return await self._client.query(
            query=query,
            mode=mode,
            top_k=top_k,
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id,
            trace_id=trace_id,
        )

    async def delete(self, doc_id: str, tenant_id: str, *, knowledge_base_id: str = "") -> bool:
        require_tenant(tenant_id)
        knowledge_base_id = _require_knowledge_base_id(knowledge_base_id)
        return await self._client.delete_doc(
            doc_id=doc_id,
            workspace=lightrag_workspace(tenant_id, knowledge_base_id),
        )

    async def stream_query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str = "",
    ) -> AsyncGenerator[str, None]:

        tenant_id = require_tenant(tenant_id)
        async for line in self._client.stream_query(
            query=query, mode=mode, top_k=top_k,
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id,
        ):
            yield line

    async def get_task_status(self, task_id: str, tenant_id: str) -> dict:
        task = await self._get_task(task_id)
        if not task:
            logger.debug(
                f"Task does not exist or has expired: task_id={task_id}, tenant={tenant_id}"
            )
            return {
                "task_id": task_id,
                "status": "not_found",
                "progress": 0.0,
                "error": "task not found",
            }
        if task.get("tenant_id") != tenant_id:
            raise TenantIsolationError("不能查询其他租户的任务状态")
        return {
            "task_id": task_id,
            "status": task.get("status", "unknown"),
            "progress": task.get("progress", 0.0),
            "error": task.get("error"),
            "lightrag_doc_ids": task.get("lightrag_doc_ids", []),
            "ontology_status": task.get("ontology_status"),
            "ontology_error": task.get("ontology_error"),
            "ontology_data": task.get("ontology_data"),
            "stage_timings": task.get("stage_timings") or {},
        }

    async def retry_ontology_extract(
        self,
        document_id: str,
        knowledge_base_id: str,
        tenant_id: str = "default",
        file_path: str = "",
    ) -> dict:

        if not self._ontology_extractor:
            return {"status": "skipped", "reason": "本体抽取未启用（ONTOLOGY_EXTRACT_ENABLED=false）"}

        tenant_id = require_tenant(tenant_id)
        knowledge_base_id = _require_knowledge_base_id(knowledge_base_id)
        if not document_id:
            raise InvalidParameterError(message="document_id 不能为空")


        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "knowledge_base_id": knowledge_base_id,
            "document_id": document_id,
            "file_path": file_path,
            "output_dir": "",
            "force_ontology_only": True,
            "status": "pending",
            "progress": 0.0,
            "lightrag_doc_ids": [],
        }
        await self._save_task(task_id, task)
        self._task_queue.put_nowait(task)
        logger.info(
            f"Ontology extraction retry enqueued: task_id={task_id}, doc={document_id}, kb={knowledge_base_id}"
        )
        return {"status": "queued", "task_id": task_id}

    async def _parse_document_with_retry(
        self, task_id: str, parse_kwargs: dict,
    ) -> list:

        try:
            max_attempts = max(1, int(os.getenv("MINERU_PARSE_MAX_RETRIES", "3")))
        except ValueError:
            max_attempts = 3
        try:
            backoff_base = float(os.getenv("MINERU_PARSE_RETRY_BACKOFF", "3"))
        except ValueError:
            backoff_base = 3.0

        last_exc: BaseException | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                return await asyncio.to_thread(
                    self._parser.parse_document,
                    **parse_kwargs,
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt >= max_attempts or not _is_transient_parse_error(exc):
                    raise
                delay = backoff_base * (2 ** (attempt - 1))
                logger.warning(
                    f"task={task_id} transient parse download failure (attempt {attempt}/{max_attempts}), "
                    f"retrying in {delay:.0f}s: {exc}"
                )
                await asyncio.sleep(delay)

        assert last_exc is not None
        raise last_exc

    async def _ingest_worker(self, worker_id: int):
        logger.info(f"RAG ingest worker {worker_id} started")
        while True:
            task = await self._task_queue.get()
            task_id = task["task_id"]
            try:
                timer = StageTimer()
                task["status"] = "processing"
                task["progress"] = 0.1
                await self._patch_task(task_id, status="processing", progress=0.1)


                device = None
                try:
                    import torch
                    if torch.cuda.is_available():
                        device = "cuda"
                        logger.info(f"task={task_id} detected GPU ({torch.cuda.get_device_name(0)}); enabling GPU acceleration")
                except ImportError:
                    pass

                output_dir = task.get("output_dir") or "/tmp/rag_output"
                whisper_model = os.getenv("WHISPER_MODEL", "base")

                force_ontology_only = task.get("force_ontology_only", False)

                file_path = task.get("file_path")

                mps_url = _resolve_video_mps_url(task)

                use_mps = False


                parse_path = file_path
                _cos_tmp: str | None = None
                if file_path and task.get("storage_backend") == "cos":
                    _t_dl = time.perf_counter()
                    os.makedirs(output_dir, exist_ok=True)
                    from jonex_core.common.object_storage import get_object_storage
                    base_name = os.path.basename(file_path)
                    _cos_tmp = os.path.join(output_dir, f"_cos_{task_id}_{base_name}")
                    await get_object_storage().get_to_path(task["storage_key"], _cos_tmp)
                    parse_path = _cos_tmp
                    logger.info(f"task={task_id} downloaded from COS: {task['storage_key']} → {_cos_tmp}")
                    timer.record("download_ms", _t_dl)


                content_list: list[dict] = []


                if mps_url and not force_ontology_only:
                    if file_path:
                        _ext0 = os.path.splitext(parse_path)[1].lower()
                        use_mps = _ext0 in _VIDEO_EXTENSIONS
                    else:
                        use_mps = True
                if use_mps:
                    logger.info(
                        f"task={task_id} using MPS intelligent video analysis for video; skipping ffmpeg+whisper ASR"
                    )
                elif file_path and not force_ontology_only and (
                    os.path.splitext(parse_path)[1].lower() in _VIDEO_EXTENSIONS
                ):

                    logger.info(
                        "task=%s video is not using MPS; falling back to ffmpeg+whisper ASR | "
                        "MPS_ENABLED=%s config_complete=%s storage_backend=%s mps_url=%s",
                        task_id,
                        _MPS_ENABLED,
                        _mps_config_complete(),
                        task.get("storage_backend"),
                        mps_url or "(empty)",
                    )

                if file_path:
                    ext = os.path.splitext(parse_path)[1].lower()
                    is_video = ext in _VIDEO_EXTENSIONS
                    is_audio = ext in _AUDIO_EXTENSIONS
                    is_plain_text = ext in _TEXT_EXTENSIONS

                    _t_parse = time.perf_counter()
                    if force_ontology_only:

                        content_list = []
                        logger.info(f"task={task_id} ontology-extraction-only mode; skipping file parsing")
                    elif is_video:
                        content_list = await asyncio.to_thread(
                            self._parser.parse_video,
                            video_path=parse_path,
                            output_dir=output_dir,
                        )
                        logger.info(f"task={task_id} video metadata parsing completed")
                    elif is_audio:
                        content_list = await asyncio.to_thread(
                            self._parser.parse_audio,
                            audio_path=parse_path,
                            output_dir=output_dir,
                        )
                        logger.info(f"task={task_id} audio metadata parsing completed")
                    elif is_plain_text:
                        content_list = await asyncio.to_thread(
                            _read_plain_text_blocks,
                            parse_path,
                        )
                        logger.info(
                            f"task={task_id} fast text parsing completed; skipped MinerU and "
                            f"produced {len(content_list)} chunks"
                        )
                    else:
                        parse_method = os.getenv("PARSE_METHOD", "auto")
                        parse_kwargs = {
                            "file_path": parse_path,
                            "method": parse_method,
                            "output_dir": output_dir,
                            "device": device,
                        }




                        if getattr(self, "_parser_name", "mineru") == "mineru":
                            mineru_backend = os.getenv("MINERU_BACKEND", "").strip()




                            mineru_model_source = (
                                os.getenv("MINERU_MODEL_SOURCE", "").strip()
                                or os.getenv("MINERU_SOURCE", "").strip()
                            )
                            if mineru_backend:
                                parse_kwargs["backend"] = mineru_backend
                            if mineru_model_source:
                                os.environ["MINERU_MODEL_SOURCE"] = mineru_model_source

                                parse_kwargs["source"] = mineru_model_source

                        mineru_timeout = os.getenv("MINERU_TIMEOUT_SECONDS", "").strip()
                        if mineru_timeout:
                            try:
                                parse_kwargs["timeout"] = int(mineru_timeout)
                            except ValueError:
                                logger.warning(
                                    f"MINERU_TIMEOUT_SECONDS={mineru_timeout} is invalid; using the default MinerU timeout"
                                )
                        content_list = await self._parse_document_with_retry(
                            task_id, parse_kwargs,
                        )
                    logger.info(
                        f"task={task_id} parsing completed; produced {len(content_list)} blocks"
                    )
                if file_path and not force_ontology_only:
                    timer.record("parse_ms", _t_parse)
                task["progress"] = 0.3
                await self._patch_task(task_id, progress=0.3)


                _t_asr = time.perf_counter()
                if file_path:
                    ext = os.path.splitext(parse_path)[1].lower()
                    is_video = ext in _VIDEO_EXTENSIONS
                    is_audio = ext in _AUDIO_EXTENSIONS
                    if force_ontology_only:
                        lightrag_doc_ids = task.get("lightrag_doc_ids", [])
                    elif is_video and not use_mps:
                        audio_path = await asyncio.to_thread(
                            _extract_audio, parse_path, output_dir
                        )
                        if audio_path:
                            task["progress"] = 0.4
                            await self._patch_task(task_id, progress=0.4)
                            asr_result = await asyncio.to_thread(
                                _transcribe_audio, audio_path, whisper_model
                            )
                            prefix = f"[视频转写] 语言: {asr_result.get('language', 'unknown')}"
                            asr_chunks = _build_asr_content_list(asr_result, prefix)
                            if asr_chunks:
                                content_list.extend(asr_chunks)
                                logger.info(
                                    f"task={task_id} video ASR completed: lang={asr_result.get('language')}, "
                                    f"{len(asr_chunks)} chunks"
                                )
                            task["progress"] = 0.5
                            await self._patch_task(task_id, progress=0.5)
                        else:
                            logger.info(f"task={task_id} video has no audio track; submitting metadata only")

                    elif is_audio:
                        task["progress"] = 0.4
                        await self._patch_task(task_id, progress=0.4)
                        asr_result = await asyncio.to_thread(
                            _transcribe_audio, parse_path, whisper_model
                        )
                        prefix = f"[音频转写] 语言: {asr_result.get('language', 'unknown')}"
                        asr_chunks = _build_asr_content_list(asr_result, prefix)
                        if asr_chunks:
                            content_list.extend(asr_chunks)
                            logger.info(
                                f"task={task_id} audio ASR completed: lang={asr_result.get('language')}, "
                                f"{len(asr_chunks)} chunks"
                            )
                        task["progress"] = 0.5
                        await self._patch_task(task_id, progress=0.5)


                if use_mps:
                    task["progress"] = 0.55
                    await self._patch_task(task_id, progress=0.55)
                    try:
                        mps_chunks = await _run_mps_analysis(mps_url)
                    except Exception as e:
                        raise UpstreamServiceError(
                            message=f"MPS 视频分析失败: {e}",
                            details={"mps_url": mps_url},
                        ) from e
                    if not mps_chunks:
                        raise UpstreamServiceError(
                            message="MPS 视频分析未返回内容（检查 MPS 配置/配额或视频 COS 地址）",
                            details={"mps_url": mps_url},
                        )
                    content_list.extend(mps_chunks)
                    logger.info(
                        f"task={task_id} MPS analysis completed (ASR skipped): {len(mps_chunks)} chunks"
                    )
                    task["progress"] = 0.6
                    await self._patch_task(task_id, progress=0.6)


                if file_path and (is_video or is_audio) and not force_ontology_only:
                    timer.record("asr_ms", _t_asr)
                _t_lightrag = time.perf_counter()
                lightrag_doc_ids: List[str] = []
                text_chunk_count = 0
                uploaded_chunk_count = 0
                duplicated_chunk_count = 0
                upload_errors: List[str] = []
                require_doc_ids = _env_bool("RAG_REQUIRE_DOC_IDS", True)
                batch_enqueue_enabled = _env_bool("RAG_BATCH_ENQUEUE_ENABLED", True)




                pending: list[tuple[int, str]] = []

                for idx, chunk in enumerate(content_list):
                    if chunk.get("type") == "table":

                        table_text = ""
                        caption = chunk.get("table_caption", "") or ""
                        if caption:
                            table_text += f"{caption}\n"
                        body = chunk.get("table_body", []) or []
                        if body:

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







                    ns_raw = f"{task['tenant_id']}|{task['knowledge_base_id']}|{task.get('document_id', '')}"
                    ns_hash = hashlib.md5(ns_raw.encode()).hexdigest()[:8]
                    text_for_upload = text + f"\n<!--yx:{ns_hash}-->"


                    loc: dict[str, Any] = {}
                    if chunk.get("char_start") is not None:
                        loc["char_start"] = chunk["char_start"]
                        loc["char_end"] = chunk.get("char_end", chunk["char_start"] + len(text))
                    if chunk.get("page_no") is not None:
                        loc["page_no"] = chunk["page_no"]
                    elif chunk.get("page_idx") is not None:
                        loc["page_no"] = chunk["page_idx"]
                    if chunk.get("time_start") is not None:
                        loc["time_start"] = chunk["time_start"]
                        loc["time_end"] = chunk.get("time_end", chunk["time_start"])

                    file_source = build_file_source(task, idx, loc=loc)
                    upload_workspace = lightrag_workspace(
                        task["tenant_id"], task["knowledge_base_id"]
                    )
                    try:
                        result = await self._client.upload_text(
                            text=text_for_upload,
                            file_source=file_source,
                            workspace=upload_workspace,
                        )
                        result_status = str(result.get("status", "")).lower()
                        if result_status in {"failed", "failure", "error"}:
                            raise UpstreamServiceError(
                                message="LightRAG 拒绝入库请求",
                                details={"response": result},
                            )
                        elif result_status == "duplicated":
                            duplicated_chunk_count += 1

                        track_id = result.get("track_id")
                        doc_ids = self._client.extract_doc_ids(result)

                        if doc_ids:
                            lightrag_doc_ids.extend(doc_ids)
                            uploaded_chunk_count += 1
                        elif track_id:
                            if batch_enqueue_enabled:

                                pending.append((idx, track_id))
                            else:

                                try:
                                    doc_ids = await self._client.get_doc_ids_by_track(
                                        track_id, workspace=upload_workspace
                                    )
                                except UpstreamServiceError:
                                    if require_doc_ids:
                                        raise
                                    logger.warning(
                                        f"task={task_id} chunk {idx} track_id={track_id} "
                                        "doc_id was not confirmed; treating the HTTP upload as successful"
                                    )
                                    doc_ids = []
                                if require_doc_ids and not doc_ids:
                                    raise UpstreamServiceError(
                                        message="LightRAG 已接收文本，但未返回可确认的 doc_id",
                                        details={"track_id": track_id},
                                    )
                                lightrag_doc_ids.extend(doc_ids)
                                uploaded_chunk_count += 1
                        else:
                            if require_doc_ids:
                                raise UpstreamServiceError(
                                    message="LightRAG 入库响应缺少 doc_id/track_id，无法确认入库结果",
                                    details={"response": result},
                                )
                            logger.warning(
                                f"task={task_id} chunk {idx} missing doc_id/track_id; "
                                "treating the HTTP upload as successful"
                            )
                            uploaded_chunk_count += 1
                    except Exception as e:
                        detail = ""
                        if isinstance(e, UpstreamServiceError) and e.details:
                            detail = f" | {e.details}"
                        logger.warning(
                            f"task={task_id} chunk {idx} upload failed (recorded as failed): {e}{detail}"
                        )
                        task["error"] = f"chunk {idx} 失败: {e}"
                        await self._patch_task(task_id, error=task["error"])
                        upload_errors.append(f"chunk {idx}: {e}{detail}")


                if batch_enqueue_enabled and pending:
                    track_ids = [tid for _, tid in pending]
                    ok_map, fail_map = await self._client.get_doc_ids_by_tracks(
                        track_ids, workspace=upload_workspace
                    )
                    for _tid, doc_ids in ok_map.items():
                        lightrag_doc_ids.extend(doc_ids)
                    for _tid, reason in fail_map.items():
                        chunk_idx = next(idx for idx, t in pending if t == _tid)
                        is_hard_failure = not reason.startswith("TIMEOUT:")
                        if require_doc_ids or is_hard_failure:
                            err_msg = f"chunk {chunk_idx}(track={_tid}) 处理失败: {reason}"
                            upload_errors.append(err_msg)
                            logger.warning(f"task={task_id} {err_msg}")
                            task["error"] = err_msg
                            await self._patch_task(task_id, error=task["error"])
                        else:
                            logger.warning(
                                f"task={task_id} chunk {chunk_idx} track_id={_tid} "
                                "doc_id was not confirmed; treating the HTTP upload as successful"
                            )
                            uploaded_chunk_count += 1
                    uploaded_chunk_count += len(ok_map)

                task["lightrag_doc_ids"] = lightrag_doc_ids
                if not force_ontology_only:
                    timer.record("lightrag_upload_ms", _t_lightrag)

                if not force_ontology_only:
                    if text_chunk_count == 0:
                        raise ValueError("解析完成但未提取到可入库文本")
                    if uploaded_chunk_count == 0:
                        raise UpstreamServiceError(
                            message="LightRAG 入库失败：没有任何文本 chunk 上传成功",
                            details={"errors": upload_errors[:5]},
                        )
                    if upload_errors:
                        raise UpstreamServiceError(
                            message=(
                                f"LightRAG 入库部分失败："
                                f"{len(upload_errors)}/{text_chunk_count} 个文本 chunk 失败"
                            ),
                            details={"errors": upload_errors[:5]},
                        )


                all_duplicated = (
                    duplicated_chunk_count > 0
                    and duplicated_chunk_count == text_chunk_count
                )
                if all_duplicated:
                    await self._patch_task(
                        task_id,
                        ontology_status="completed",
                    )
                    logger.info(
                        f"task={task_id} all chunks are idempotent duplicates"
                        f"({duplicated_chunk_count}/{text_chunk_count}); skipping ontology extraction"
                    )


                _t_ont = time.perf_counter()
                _ontology_ran = bool(self._ontology_extractor) and not all_duplicated
                if self._ontology_extractor and not all_duplicated:
                    try:



                        _reader = self._reader()
                        _ont_scope = {
                            "tenant_id": task["tenant_id"],
                            "knowledge_base_id": task["knowledge_base_id"],
                        }
                        if task.get("document_id"):
                            _ont_scope["document_ids"] = [task["document_id"]]
                        elif task.get("file_path"):
                            _ont_scope["file_paths"] = [task["file_path"]]
                        all_entities = []
                        page = 1
                        while True:
                            batch = await _reader.get_entities(
                                scope=_ont_scope,
                                page=page,
                                page_size=500,
                                with_degree=False,
                            )
                            items = batch.get("items", [])
                            if not items:
                                break
                            all_entities.extend(items)
                            if len(all_entities) >= int(batch.get("total", 0) or 0):
                                break
                            page += 1


                        _ns_pattern = re.compile(r"<!--yx:[a-f0-9]{8}-->")
                        all_entities = [
                            e for e in all_entities
                            if not _ns_pattern.search(e.get("name", ""))
                        ]

                        if not all_entities:

                            await self._patch_task(
                                task_id,
                                ontology_status="failed",
                                ontology_error="LightRAG 存储中未找到候选实体，无法抽取本体",
                            )
                            logger.info(
                                f"task={task_id} no candidate entities; setting ontology status to pending"
                            )
                        else:
                            scope_info = {
                                "tenant_id": task["tenant_id"],
                                "knowledge_base_id": task["knowledge_base_id"],
                                "document_id": task.get("document_id", ""),


                                "trace_id": task.get("trace_id") or task_id,
                            }


                            compiled_schema = task.get("ontology_schema")
                            if not compiled_schema:
                                try:
                                    from jonex_core.capability.atomic.ontology.compiled_schema_client import (
                                        CompiledSchemaClient,
                                    )
                                    compiled_schema = await CompiledSchemaClient().get_schema(
                                        task["tenant_id"], task["knowledge_base_id"],
                                    )
                                except Exception as e:
                                    logger.warning(
                                        f"task={task_id} failed to fetch compiled schema; using fallback: {e}"
                                    )


                            all_relations = []
                            page = 1
                            while True:
                                rb = await _reader.get_relationships(
                                    scope=_ont_scope,
                                    page=page, page_size=500,
                                )
                                items = rb.get("items", [])
                                if not items:
                                    break
                                all_relations.extend(items)
                                if len(all_relations) >= int(rb.get("total", 0) or 0):
                                    break
                                page += 1

                            result = await self._ontology_extractor.extract(
                                content_list=content_list,
                                lightrag_entities=all_entities,
                                lightrag_relations=all_relations,
                                scope=scope_info,
                                compiled_schema=compiled_schema,
                            )
                            ontology_status = (
                                "completed"
                                if result.ok
                                else "failed"
                            )
                            ontology_data = {
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

                if _ontology_ran:
                    timer.record("ontology_extract_ms", _t_ont)
                timer.mark_total("worker_total_ms")
                _stage_timings = timer.as_dict()

                task["status"] = "completed"
                task["progress"] = 1.0
                await self._patch_task(
                    task_id,
                    status="completed",
                    progress=1.0,
                    lightrag_doc_ids=lightrag_doc_ids,
                    stage_timings=_stage_timings,
                )
                logger.info(
                    f"task={task_id} completed; submitted {uploaded_chunk_count} chunks and "
                    f"received {len(lightrag_doc_ids)} doc_ids"
                )
                logger.info(
                    "ingest_timing task=%s status=completed force_ontology_only=%s %s",
                    task_id,
                    force_ontology_only,
                    " ".join(f"{k}={v}" for k, v in _stage_timings.items()),
                    extra={
                        "event": "ingest_timing",
                        "task_id": task_id,
                        "tenant_id": task.get("tenant_id"),
                        "knowledge_base_id": task.get("knowledge_base_id"),
                        "document_id": task.get("document_id"),
                        "status": "completed",
                        "storage_backend": task.get("storage_backend"),
                        "force_ontology_only": force_ontology_only,
                        "text_chunk_count": text_chunk_count,
                        "lightrag_doc_count": len(lightrag_doc_ids),
                        **_stage_timings,
                    },
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
                timer.mark_total("worker_total_ms")
                _stage_timings = timer.as_dict()
                await self._patch_task(
                    task_id,
                    status="failed",
                    error=str(e),
                    stage_timings=_stage_timings,
                )
                logger.exception(f"task={task_id} failed: {e}")


                logger.info(
                    "ingest_timing task=%s status=failed %s error=%s",
                    task_id,
                    " ".join(f"{k}={v}" for k, v in _stage_timings.items()),
                    str(e)[:200],
                    extra={
                        "event": "ingest_timing",
                        "task_id": task_id,
                        "tenant_id": task.get("tenant_id"),
                        "knowledge_base_id": task.get("knowledge_base_id"),
                        "document_id": task.get("document_id"),
                        "status": "failed",
                        "storage_backend": task.get("storage_backend"),
                        "force_ontology_only": task.get("force_ontology_only", False),
                        "error": str(e)[:500],
                        **_stage_timings,
                    },
                )
                await self._send_webhook(
                    task_id=task_id,
                    tenant_id=task["tenant_id"],
                    status=task["status"],
                    doc_ids=task.get("lightrag_doc_ids", []),
                    error=task["error"],
                )
            finally:

                cos_tmp = locals().get("_cos_tmp")
                if cos_tmp and os.path.exists(cos_tmp):
                    try:
                        os.remove(cos_tmp)
                        logger.debug(f"task={task_id} COS temporary file cleaned up: {cos_tmp}")
                    except OSError:
                        pass
                self._task_queue.task_done()

    def register_routes(self, app) -> None:

        from fastapi.responses import StreamingResponse

        @app.get("/query/stream")
        async def stream_query_endpoint(
            query: str = "",
            mode: str = "hybrid",
            top_k: int = 5,
            tenant_id: str = "",
            knowledge_base_id: str = "",
        ):
            async def _generate():
                async for line in self.stream_query(
                    query=query, tenant_id=tenant_id, mode=mode, top_k=top_k,
                    knowledge_base_id=knowledge_base_id,
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
