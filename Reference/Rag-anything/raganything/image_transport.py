"""ImageTransport: VLM image transport layer abstraction.

Makes local frame images accessible via public URL.
CosImageHost is the Tencent COS implementation.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# Global shared executor to avoid thread explosion across instances
_GLOBAL_EXECUTOR_MAX_WORKERS = 32
_IMAGE_TRANSPORT_EXECUTOR: Optional[ThreadPoolExecutor] = None
_IMAGE_TRANSPORT_EXECUTOR_LOCK = threading.Lock()

_MAX_FRAME_BYTES = 10 * 1024 * 1024   # TokenHub single image limit
_MAX_DELETE_BATCH = 1000              # COS DeleteObjects max per call
_UPLOAD_RETRY_COUNT = 2               # per-frame max retries

_SAFE_PATH_RE = re.compile(r'[^a-zA-Z0-9._-]')

_CONTENT_TYPE_MAP = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.png': 'image/png', '.webp': 'image/webp',
}


def _get_shared_executor() -> ThreadPoolExecutor:
    global _IMAGE_TRANSPORT_EXECUTOR
    with _IMAGE_TRANSPORT_EXECUTOR_LOCK:
        if _IMAGE_TRANSPORT_EXECUTOR is None:
            _IMAGE_TRANSPORT_EXECUTOR = ThreadPoolExecutor(
                max_workers=_GLOBAL_EXECUTOR_MAX_WORKERS)
        return _IMAGE_TRANSPORT_EXECUTOR


@dataclass
class PrepareResult:
    """Return value of ImageTransport.prepare_urls()."""
    frames: list[dict]
    transport_available: bool = False
    uploaded_count: int = 0
    failed_count: int = 0
    fatal_error: Optional[str] = None


@dataclass
class VLMSupport:
    """VLM protocol capability. Injected as vlm_func.vlm_support."""
    supports_url: bool
    supports_base64: bool


class CleanupPolicy(Enum):
    IMMEDIATE = "immediate"   # delete after VLM done (default)
    TTL = "ttl"               # rely on COS lifecycle rules (1-day auto-expire)
    NEVER = "never"           # keep for debugging/audit


class ImageTransport(ABC):
    """VLM image transport layer abstraction.

    Makes local frame images accessible via public URL.
    One instance per video processing session.
    """

    @abstractmethod
    async def prepare_urls(self, frames: list[dict], video_id: str) -> PrepareResult:
        """Upload frames and inject frame['upload'] = {'url': '...', 'key': '...'}.

        video_id is used as namespace in COS object keys (prevents cross-video collision).
        Never raises. Failed frames get frame['upload'] absent or url=None.
        """

    @abstractmethod
    async def cleanup(self, frames: list[dict]) -> None:
        """Delete uploaded objects by frame['upload']['key']. Never raises."""


class CosImageHost(ImageTransport):
    """Tencent COS implementation: upload → public URL → cleanup."""

    def __init__(self, bucket, appid, region, secret_id=None, secret_key=None,
                 key_prefix="rag_anything/video", max_concurrent=5,
                 client=None, executor=None):
        """client: pass existing CosS3Client (e.g. STS temp credentials).
        executor: inject existing ThreadPoolExecutor, else shared global pool.
        """
        self._validate_config(bucket, appid, region, key_prefix)
        self._bucket = bucket
        self._appid = appid
        self._region = region
        self._key_prefix = key_prefix.rstrip('/')
        self._max_concurrent = max_concurrent

        if client:
            self._client = client
        else:
            from qcloud_cos import CosConfig, CosS3Client
            cfg = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
            self._client = CosS3Client(cfg)

        if executor is not None:
            self._executor = executor
        else:
            self._executor = _get_shared_executor()

        actual_workers = getattr(self._executor, '_max_workers', max_concurrent)
        if self._max_concurrent > actual_workers:
            logger.warning(
                f"cos_max_concurrent ({self._max_concurrent}) exceeds executor "
                f"max_workers ({actual_workers}); uploads may queue unexpectedly")

        self._cleanup_policy = CleanupPolicy.IMMEDIATE
        self._closed = False

    # ── config validation ────────────────────────────────

    @staticmethod
    def _validate_config(bucket, appid, region, key_prefix):
        if not bucket or not appid or not region:
            raise ValueError(
                f"cos_bucket, cos_appid, cos_region must all be set, "
                f"got bucket={bucket!r}, appid={appid!r}, region={region!r}")
        if key_prefix and ('..' in key_prefix or key_prefix.startswith('/')
                           or '\\' in key_prefix):
            raise ValueError(
                f"cos_key_prefix invalid (no '..', '/', '\\'): {key_prefix!r}")

    # ── path safety ──────────────────────────────────────

    @staticmethod
    def _sanitize_path_component(component: str) -> str:
        """Whitelist: keep only alphanumeric, dot, underscore, hyphen."""
        cleaned = _SAFE_PATH_RE.sub('_', component)
        cleaned = cleaned.strip('_')
        return cleaned or 'unnamed'

    @staticmethod
    def _frame_name_from_path(frame_path: str) -> str:
        name = os.path.basename(frame_path)
        return CosImageHost._sanitize_path_component(name)

    # ── content type ─────────────────────────────────────

    @classmethod
    def _content_type_for(cls, frame_path: str) -> str:
        suffix = os.path.splitext(frame_path)[1].lower()
        return _CONTENT_TYPE_MAP.get(suffix, 'application/octet-stream')

    # ── URL construction ─────────────────────────────────

    def _make_access_url(self, cos_key: str) -> str:
        """Construct public-read URL.

        COS domain: {bucket}-{appid}.cos.{region}.myqcloud.com/{key}
        If bucket name already contains the appid suffix, don't double it.
        """
        if self._bucket.endswith(f"-{self._appid}"):
            bucket_part = self._bucket
        else:
            bucket_part = f"{self._bucket}-{self._appid}"
        return (
            f"https://{bucket_part}"
            f".cos.{self._region}.myqcloud.com/{cos_key}"
        )

    # ── prepare_urls ─────────────────────────────────────

    async def prepare_urls(self, frames: list[dict], video_id: str) -> PrepareResult:
        result = PrepareResult(frames=frames)

        if not frames:
            result.transport_available = True
            return result

        safe_video_id = self._sanitize_path_component(video_id)
        loop = asyncio.get_running_loop()
        semaphore = asyncio.Semaphore(self._max_concurrent)

        fatal_error_str: Optional[str] = None
        fatal_event = asyncio.Event()

        async def upload_one(frame: dict) -> str:
            """Return: 'ok' | 'skip' | 'failed' | 'fatal'."""
            if frame.get('upload') and frame['upload'].get('url'):
                return 'ok'

            frame_path = frame.get('frame_path', '')
            if not frame_path or not os.path.isfile(frame_path):
                return 'skip'
            try:
                if os.path.getsize(frame_path) > _MAX_FRAME_BYTES:
                    logger.warning(f"Frame exceeds 10MB: {frame_path}")
                    return 'skip'
            except OSError:
                return 'skip'

            safe_name = self._frame_name_from_path(frame_path)
            cos_key = f"{self._key_prefix}/{safe_video_id}/{safe_name}"
            content_type = self._content_type_for(frame_path)

            for attempt in range(_UPLOAD_RETRY_COUNT + 1):
                if fatal_event.is_set():
                    return 'skip'

                try:
                    async with semaphore:
                        if fatal_event.is_set():
                            return 'skip'
                        await loop.run_in_executor(
                            self._executor,
                            self._do_upload,
                            cos_key,
                            frame_path,
                            content_type,
                        )
                    frame['upload'] = {
                        'url': self._make_access_url(cos_key),
                        'key': cos_key,
                    }
                    return 'ok'
                except _UploadError as e:
                    if e.fatal:
                        nonlocal fatal_error_str
                        if fatal_error_str is None:
                            fatal_error_str = str(e)
                        fatal_event.set()
                        return 'fatal'
                    if attempt < _UPLOAD_RETRY_COUNT and e.retryable:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        logger.warning(f"Upload failed for {frame_path}: {e}")
                        return 'failed'
                except Exception as e:
                    logger.warning(f"Upload failed (non-retryable): {frame_path}: {e}")
                    return 'failed'

        try:
            tasks = [upload_one(f) for f in frames]
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)

            for outcome in outcomes:
                if outcome == 'ok':
                    result.uploaded_count += 1
                elif outcome == 'failed':
                    result.failed_count += 1
                elif outcome == 'fatal':
                    result.failed_count += 1
        except Exception as e:
            logger.error(f"Unexpected error in prepare_urls: {e}", exc_info=True)

        result.fatal_error = fatal_error_str
        result.transport_available = result.uploaded_count > 0
        return result

    def _do_upload(self, cos_key: str, frame_path: str, content_type: str):
        """Synchronous upload (runs in thread pool). Uses file stream, not read-all."""
        try:
            with open(frame_path, 'rb') as body:
                self._client.put_object(
                    Bucket=self._bucket,
                    Key=cos_key,
                    Body=body,
                    ContentType=content_type,
                )
        except Exception as e:
            retryable, fatal = _classify_error(e)
            raise _UploadError(str(e), retryable=retryable, fatal=fatal) from e

    # ── cleanup ──────────────────────────────────────────

    async def cleanup(self, frames: list[dict]) -> None:
        if self._cleanup_policy in (CleanupPolicy.TTL, CleanupPolicy.NEVER):
            return

        cos_keys = list(dict.fromkeys(
            f['upload']['key']
            for f in frames
            if f.get('upload') and f['upload'].get('key')
        ))
        if not cos_keys:
            return

        loop = asyncio.get_running_loop()

        for i in range(0, len(cos_keys), _MAX_DELETE_BATCH):
            batch = [{'Key': k} for k in cos_keys[i:i + _MAX_DELETE_BATCH]]
            try:
                response = await loop.run_in_executor(
                    self._executor, self._do_delete_objects, batch)
                for error in response.get('Error', []):
                    code = error.get('Code', '')
                    key = error.get('Key', '')
                    if code == 'NoSuchKey':
                        logger.debug(f"Cleanup: already deleted: {key}")
                    else:
                        logger.warning(
                            f"Cleanup: delete failed {key}: "
                            f"[{code}] {error.get('Message', '')}")
            except Exception as e:
                logger.warning(f"Cleanup batch failed (non-fatal): {e}")

    def _do_delete_objects(self, batch: list[dict]):
        return self._client.delete_objects(
            Bucket=self._bucket,
            Delete={'Object': batch, 'Quiet': False},
        )

    # ── lifecycle ────────────────────────────────────────

    def close(self):
        if self._closed:
            return
        self._closed = True

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# ── error classification (module-level) ─────────────────

class _UploadError(Exception):
    def __init__(self, message: str, retryable: bool = True, fatal: bool = False):
        super().__init__(message)
        self.retryable = retryable
        self.fatal = fatal


def _classify_error(exc: Exception) -> tuple[bool, bool]:
    """Return (retryable, fatal).

    fatal: transport infrastructure broken (auth/bucket/endpoint).
    retryable: transient error (network/server) worth retrying.
    """
    # Priority 1: SDK ErrorCode (distinguishes NoSuchBucket vs NoSuchKey)
    error_code = (
        getattr(exc, 'error_code', None)
        or getattr(exc, 'ErrorCode', None)
        or getattr(exc, 'code', '')
    )
    if error_code and isinstance(error_code, str):
        ec = error_code.lower()
        if ec in {'nosuchbucket', 'accessdenied', 'invalidaccesskeyid',
                  'signaturedoesnotmatch', 'invalidbucketname'}:
            return False, True
        if ec == 'nosuchkey':
            return False, False

    # Priority 2: HTTP status code
    code = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
    if code and isinstance(code, int):
        if code in (401, 403):
            return False, True
        if code >= 500:
            return True, False

    # Priority 3: SDK exception types
    try:
        from qcloud_cos.cos_exception import CosClientError, CosServiceError
        if isinstance(exc, CosServiceError):
            return code >= 500 if code else False, code == 403
        if isinstance(exc, CosClientError):
            err_str = str(exc).lower()
            if any(x in err_str for x in ('signature', 'credential',
                    'secretid', 'secrekey', 'authorization')):
                return False, True
            return True, False
    except ImportError:
        pass

    # Priority 4: string fallback
    err = str(exc).lower()
    fatal_keywords = {'access denied', 'forbidden', 'unauthorized',
                      'invalid bucket', 'no such bucket'}
    if any(x in err for x in fatal_keywords):
        return False, True
    non_retryable = {'not found', 'bad request', 'invalid'}
    if any(x in err for x in non_retryable):
        return False, False
    retryable = {'timeout', 'connection', 'reset', 'network',
                 'broken pipe', 'too many'}
    return any(x in err for x in retryable), False
