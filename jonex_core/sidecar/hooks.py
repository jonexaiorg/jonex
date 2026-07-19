

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from jonex_core.common.config import get_config
from jonex_core.security.internal_auth import get_internal_auth

logger = logging.getLogger(__name__)


class RateLimiter:


    def __init__(self):
        self.config = get_config()

    async def check(self, tenant_id: str, api_path: str, user_id: Optional[str] = None) -> bool:

        if not self.config.RATE_LIMIT_ENABLED:
            return True
        return True


class MeteringCollector:


    def __init__(self):
        self.config = get_config()

    async def record(
        self,
        tenant_id: str,
        api_path: str,
        latency_ms: float,
        status_code: int,
        user_id: Optional[str] = None,
    ):

        if not self.config.METERING_ENABLED:
            return
        logger.debug(
            f"[Metering] tenant={tenant_id} api={api_path} "
            f"latency={latency_ms:.0f}ms status={status_code}"
        )


class CircuitBreaker:


    def __init__(self):
        self.config = get_config()
        self._failure_counts: dict[str, int] = {}
        self._state: dict[str, str] = {}

    async def before_call(self, service_name: str) -> bool:

        if not self._enabled:
            return True
        state = self._state.get(service_name, "closed")
        if state == "open":
            logger.warning(f"[CircuitBreaker] Circuit is open; rejecting call: {service_name}")
            return False
        return True

    async def on_success(self, service_name: str):

        if not self._enabled:
            return
        self._failure_counts[service_name] = 0
        self._state[service_name] = "closed"

    async def on_failure(self, service_name: str):

        if not self._enabled:
            return
        count = self._failure_counts.get(service_name, 0) + 1
        self._failure_counts[service_name] = count
        if count >= self.config.CIRCUIT_BREAKER_THRESHOLD:
            self._state[service_name] = "open"
            logger.warning(
                f"[CircuitBreaker] Circuit breaker triggered: {service_name} "
                f"({count} consecutive failures)"
            )

    @property
    def _enabled(self) -> bool:
        return getattr(self.config, "CIRCUIT_BREAKER_ENABLED", False)


class AuditForwarder:



    _AUDIT_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


    _EXCLUDED_PREFIXES = ("auth/", "health")

    def __init__(self):
        self.config = get_config()
        self._buffer: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._bg_task: Optional[asyncio.Task] = None
        self._running = False

        self._key_action_keywords = [
            kw.strip().lower()
            for kw in getattr(self.config, "AUDIT_KEY_ACTION_KEYWORDS", "").split(",")
            if kw.strip()
        ]

    def _is_key_action(self, action: Optional[str]) -> bool:

        if not action:
            return False
        tokens = re.split(r"[_\-.\s]+", action.lower())
        return any(
            tok == kw or tok.startswith(kw)
            for tok in tokens
            for kw in self._key_action_keywords
        )

    def _is_collectable(
        self,
        method: str,
        path: str,
        invoke_action: Optional[str] = None,
        is_invoke: bool = False,
    ) -> bool:

        if not self.config.AUDIT_LOG_ENABLED:
            return False
        normalized = path.lstrip("/")
        for prefix in self._EXCLUDED_PREFIXES:
            if normalized.startswith(prefix):
                return False

        if is_invoke:
            return self._is_key_action(invoke_action)

        if method not in self._AUDIT_METHODS:
            return False
        return True

    async def collect(
        self,
        tenant_id: str,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        trace_id: str = "",
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip: Optional[str] = None,
        service_name: str = "sidecar",
        request_params: Optional[Dict] = None,
        response_body: Optional[Dict] = None,
        invoke_action: Optional[str] = None,
        is_invoke: bool = False,
    ):

        if not self._is_collectable(method, path, invoke_action, is_invoke):
            return


        audit_action = invoke_action if is_invoke and invoke_action else f"http.{method.lower()}"

        entry = {
            "tenant_id": tenant_id,
            "log_type": "OPERATION",
            "action": audit_action,
            "outcome": "SUCCESS" if status_code < 400 else "FAILED",
            "service_name": service_name,
            "user_id": int(user_id) if user_id and user_id.isdigit() else None,
            "username": username,
            "ip": ip,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": int(latency_ms),
            "trace_id": trace_id,
            "request_params": request_params,
            "response_body": response_body,
        }

        async with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) >= self.config.AUDIT_FLUSH_BATCH_SIZE:
                asyncio.ensure_future(self._flush())

    async def _flush(self):

        async with self._lock:
            batch = list(self._buffer)
            self._buffer.clear()
        if not batch:
            return

        try:
            internal_auth = get_internal_auth()
            token = internal_auth.generate_token("sidecar")
            platform_url = self.config.PLATFORM_URL
            url = f"{platform_url}/api/v1/platform/audit-logs:ingest"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json={"entries": batch},
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code >= 400:
                    logger.warning(
                        "[AuditForwarder] ingest returned %s: %s",
                        resp.status_code, resp.text,
                    )
        except Exception:
            logger.exception("[AuditForwarder] Failed to forward audit logs")

    async def start_periodic_flush(self):

        if self._running:
            return
        self._running = True
        interval = self.config.AUDIT_FLUSH_INTERVAL_MS / 1000.0

        async def _loop():
            while self._running:
                await asyncio.sleep(interval)
                await self._flush()
        self._bg_task = asyncio.create_task(_loop())

    async def stop(self):

        self._running = False
        if self._bg_task:
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass
        await self._flush()



_audit_forwarder: Optional["AuditForwarder"] = None
_rate_limiter: Optional[RateLimiter] = None
_metering: Optional[MeteringCollector] = None
_circuit_breaker: Optional[CircuitBreaker] = None


def get_audit_forwarder() -> "AuditForwarder":
    global _audit_forwarder
    if _audit_forwarder is None:
        _audit_forwarder = AuditForwarder()
    return _audit_forwarder


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_metering() -> MeteringCollector:
    global _metering
    if _metering is None:
        _metering = MeteringCollector()
    return _metering


def get_circuit_breaker() -> CircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker