#!/usr/bin/python3



import json
import logging
import secrets
import time
from typing import Any, Optional

import httpx
from fastapi import FastAPI, Depends, Request, Header
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from jonex_core.sidecar.proxy import get_capability_proxy
from jonex_core.sidecar.hooks import (
    get_rate_limiter,
    get_metering,
    get_circuit_breaker,
    get_audit_forwarder,
)
from jonex_core.common import (
    register_exception_handlers,
    MissingApiKeyError,
    CapabilityInvokeError,
    InvalidParameterError,
    TenantIsolationError,
    TokenExpiredError,
    require_tenant,
    setup_logging,
)
from jonex_core.common.config import get_config
from jonex_core.security.user_auth import get_user_auth

logger = logging.getLogger(__name__)


class CapabilityInvokeRequest(BaseModel):

    capability_id: str
    payload: dict
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip: Optional[str] = None
    context: Optional[dict] = None


class InvokeResult(BaseModel):

    request_id: str
    success: bool
    code: int
    message: str
    data: Optional[dict] = None
    latency_ms: float


class UserInfo(BaseModel):

    user_id: int
    username: str
    display_name: Optional[str] = None
    tenant_id: str
    role: str


TENANT_REQUIRED_AUTH_PATHS = {
    "auth/refresh",
    "auth/login-ticket",
}

TENANT_REQUIRED_PLATFORM_PREFIXES = (
    "platform/users",
    "platform/roles",
    "platform/audit-logs",
    "platform/task-schedules",
)


def _normalize_proxy_path(path: str) -> str:
    return path.strip("/")


async def _read_json_body(request: Request) -> dict[str, Any] | None:

    if request.method not in ("POST", "PUT", "PATCH"):
        return None

    raw = await request.body()
    if not raw:
        return None

    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidParameterError(message="Request body must contain valid JSON", cause=exc)

    if body is None:
        return None
    if not isinstance(body, dict):
        raise InvalidParameterError(message="Request body must be a JSON object")
    return body


def _tenant_from_authorization(auth_header: str | None) -> str | None:
    if not auth_header:
        return None

    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    if get_config().ENV.lower() in {"dev", "test"} and token.startswith("jonex_test_"):
        return require_tenant(token.removeprefix("jonex_test_"))

    user_auth = get_user_auth()
    payload = user_auth.decode_token(token)
    return require_tenant(payload.get("tenant_id"))


def _candidate_tenant(value: Any, source: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidParameterError(
            message="tenant_id must be a string",
            details={"source": source},
        )
    if not value.strip():
        return None
    return require_tenant(value)


def _assert_tenant_matches(
    candidate: Any,
    canonical: str | None,
    source: str,
) -> str | None:
    tenant_id = _candidate_tenant(candidate, source)
    if tenant_id is None:
        return canonical
    if canonical is not None and tenant_id != canonical:
        raise TenantIsolationError(
            message="Request tenant does not match the authenticated tenant",
            details={
                "source": source,
                "request_tenant_id": tenant_id,
                "auth_tenant_id": canonical,
            },
        )
    return tenant_id


def _platform_path_requires_tenant(path: str) -> bool:
    normalized = _normalize_proxy_path(path)
    if normalized in TENANT_REQUIRED_AUTH_PATHS:
        return True
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/")
        for prefix in TENANT_REQUIRED_PLATFORM_PREFIXES
    )


def _resolve_platform_tenant(
    request: Request,
    body: dict[str, Any] | None,
    auth: dict | None = None,
    require: bool = False,
) -> str | None:
    canonical = _candidate_tenant(auth.get("tenant_id"), "auth") if auth else None
    if auth is not None:
        canonical = _assert_tenant_matches(
            _tenant_from_authorization(request.headers.get("Authorization")),
            canonical,
            "authorization",
        )
    canonical = _assert_tenant_matches(
        request.headers.get("X-Tenant-ID"),
        canonical,
        "X-Tenant-ID",
    )

    if require and canonical is None:
        raise TenantIsolationError(message="This request requires an explicit tenant")
    return canonical


def _resolve_invoke_tenant(
    invoke_request: CapabilityInvokeRequest,
    auth: dict,
    x_tenant_id: str | None = None,
) -> str:
    canonical = _candidate_tenant(auth.get("tenant_id"), "auth")
    canonical = _assert_tenant_matches(x_tenant_id, canonical, "X-Tenant-ID")
    if canonical is None:
        raise TenantIsolationError(message="Capability calls require an explicit tenant")
    _assert_tenant_matches(invoke_request.tenant_id, canonical, "invoke.tenant_id")
    return canonical




_SYSTEM_INVOKE_ACTIONS = {"ingest_push"}


def _resolve_invoke_tenant_optional(
    invoke_request: CapabilityInvokeRequest,
    auth: dict,
    x_tenant_id: str | None = None,
) -> str | None:

    try:
        canonical = _candidate_tenant(auth.get("tenant_id"), "auth")
        canonical = _assert_tenant_matches(x_tenant_id, canonical, "X-Tenant-ID")
        return canonical
    except Exception:
        return None


async def _proxy_to_platform(request: Request, path: str, auth: dict | None = None):

    config = get_config()
    platform_url = config.PLATFORM_URL
    limiter = get_rate_limiter()
    metering = get_metering()

    auth_header = request.headers.get("Authorization", "")
    body = await _read_json_body(request)
    tenant_id = _resolve_platform_tenant(
        request,
        body,
        auth=auth,
        require=_platform_path_requires_tenant(path),
    )
    metering_tenant_id = tenant_id or "system"

    await limiter.check(metering_tenant_id, path)

    headers = {
        "X-Request-ID": getattr(request.state, "request_id", ""),
    }
    if auth_header:
        headers["Authorization"] = auth_header
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id

    target = f"{platform_url}/api/v1/{path}"

    start = time.time()
    status_code = 200

    client_ip = request.headers.get(
        "X-Forwarded-For",
        request.client.host if request.client else "",
    ).split(",")[0].strip()
    audit_user_id = str(auth.get("user_id")) if auth and auth.get("user_id") else ""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            kwargs = {"headers": headers, "params": request.query_params}
            if body is not None:
                kwargs["json"] = body
            resp = await client.request(request.method, target, **kwargs)
            status_code = resp.status_code
            resp.raise_for_status()
            result = resp.json()
            await metering.record(
                metering_tenant_id,
                path,
                (time.time() - start) * 1000,
                status_code,
            )
            await get_audit_forwarder().collect(
                tenant_id=metering_tenant_id,
                method=request.method,
                path=path,
                status_code=status_code,
                latency_ms=(time.time() - start) * 1000,
                trace_id=getattr(request.state, "request_id", ""),
                user_id=audit_user_id,
                ip=client_ip,
                service_name="sidecar",
            )
            return result
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            await metering.record(
                metering_tenant_id,
                path,
                (time.time() - start) * 1000,
                status_code,
            )
            await get_audit_forwarder().collect(
                tenant_id=metering_tenant_id,
                method=request.method,
                path=path,
                status_code=status_code,
                latency_ms=(time.time() - start) * 1000,
                trace_id=getattr(request.state, "request_id", ""),
                user_id=audit_user_id,
                ip=client_ip,
                service_name="sidecar",
            )
            try:
                detail = e.response.json()
            except Exception:
                detail = {"message": e.response.text}
            if isinstance(detail, dict) and "success" in detail and "message" in detail:
                return JSONResponse(content=detail, status_code=e.response.status_code)
            raise CapabilityInvokeError(
                message=detail.get("message", f"Platform service error: HTTP {e.response.status_code}"),
            )


class SidecarApp:


    def __init__(self):
        self.app = FastAPI(
            title="Jonex Platform Sidecar",
            description="Jonex平台能力代理 - 统一入口（内部服务）",
            version="1.0.0"
        )
        self.proxy = get_capability_proxy()
        self._setup_routes()
        self._setup_lifecycle()

        register_exception_handlers(self.app)

    def _setup_lifecycle(self):


        @self.app.on_event("startup")
        async def _start_audit_forwarder():
            try:
                setup_logging(enable_file=True)
                logger.info("[Sidecar] Local file logging enabled")
                await get_audit_forwarder().start_periodic_flush()
                logger.info("[Sidecar] AuditForwarder periodic flush started")
            except Exception:
                logger.exception("[Sidecar] Failed to start AuditForwarder")

        @self.app.on_event("shutdown")
        async def _stop_audit_forwarder():
            try:
                await get_audit_forwarder().stop()
                logger.info("[Sidecar] AuditForwarder stopped and flushed")
            except Exception:
                logger.exception("[Sidecar] Failed to stop AuditForwarder")

    def _setup_routes(self):


        api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

        async def verify_any_auth(
            api_key: Optional[str] = Depends(api_key_header),
            authorization: Optional[str] = Header(None),
            x_tenant_id: Optional[str] = Header(None),
        ) -> dict:

            if authorization and authorization.startswith("Bearer "):
                token = authorization[7:]
                if get_config().ENV.lower() in {"dev", "test"} and token.startswith("jonex_test_"):
                    return {
                        "auth_type": "test",
                        "tenant_id": require_tenant(token.removeprefix("jonex_test_")),
                    }
                payload = get_user_auth().decode_token(token)
                return {
                    "auth_type": "user",
                    "tenant_id": require_tenant(payload.get("tenant_id")),
                    "user_id": int(payload["sub"]),
                    "username": payload.get("username", ""),
                }
            configured_api_key = get_config().SIDECAR_API_KEY
            if (
                api_key
                and configured_api_key
                and secrets.compare_digest(api_key, configured_api_key)
            ):
                tenant_id = require_tenant(x_tenant_id) if x_tenant_id else None
                return {"auth_type": "apikey", "tenant_id": tenant_id}
            raise MissingApiKeyError()



        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "sidecar",
                "endpoints_configured": len(self.proxy.capability_endpoints),
            }

        @self.app.get("/capabilities")
        async def list_capabilities(auth: dict = Depends(verify_any_auth)):
            capabilities = [
                {
                    "capability_id": f"business.{name}.v1",
                    "name": f"{name} 能力服务",
                    "type": "business",
                    "version": "v1",
                    "endpoint": endpoint,
                }
                for name, endpoint in self.proxy.capability_endpoints.items()
                if endpoint
            ]
            return {"capabilities": capabilities}



        @self.app.post("/auth/login")
        async def auth_login(request: Request):
            return await _proxy_to_platform(request, "auth/login")

        @self.app.get("/auth/me")
        async def auth_me(request: Request):
            return await _proxy_to_platform(request, "auth/me")

        @self.app.post("/auth/refresh")
        async def auth_refresh(request: Request, auth: dict = Depends(verify_any_auth)):
            return await _proxy_to_platform(request, "auth/refresh", auth)

        @self.app.post("/auth/login-ticket")
        async def auth_login_ticket(request: Request, auth: dict = Depends(verify_any_auth)):
            return await _proxy_to_platform(request, "auth/login-ticket", auth)

        @self.app.post("/auth/exchange-ticket")
        async def auth_exchange_ticket(request: Request):
            return await _proxy_to_platform(request, "auth/exchange-ticket")

        @self.app.post("/auth/logout")
        async def auth_logout(request: Request):
            return await _proxy_to_platform(request, "auth/logout")



        @self.app.api_route("/platform/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def platform_proxy(
            request: Request,
            path: str,
            auth: dict = Depends(verify_any_auth),
        ):
            return await _proxy_to_platform(request, f"platform/{path}", auth)



        @self.app.post("/invoke", response_model=InvokeResult)
        async def invoke_capability(
            request: Request,
            invoke_request: CapabilityInvokeRequest,
            auth: dict = Depends(verify_any_auth),
            x_tenant_id: Optional[str] = Header(None),
        ):
            start_time = time.time()

            _action = (invoke_request.payload or {}).get("action")
            if _action in _SYSTEM_INVOKE_ACTIONS:
                tenant_id = invoke_request.tenant_id or _resolve_invoke_tenant_optional(invoke_request, auth, x_tenant_id)
                if not tenant_id:
                    raise CapabilityInvokeError(message="Invalid ingest key; unable to resolve tenant information. Regenerate the API Key")
            else:
                tenant_id = _resolve_invoke_tenant(invoke_request, auth, x_tenant_id)
            user_id = invoke_request.user_id or str(auth.get("user_id", ""))
            username = invoke_request.username or auth.get("username", "")

            client_ip = request.headers.get(
                "X-Forwarded-For",
                request.client.host if request.client else "",
            ).split(",")[0].strip()
            ip = invoke_request.ip or client_ip

            import uuid as _uuid
            trace_id = request.headers.get("X-Request-ID") or _uuid.uuid4().hex
            limiter = get_rate_limiter()
            breaker = get_circuit_breaker()
            metering = get_metering()


            service_name = invoke_request.capability_id.split(".")[1] if "." in invoke_request.capability_id else invoke_request.capability_id

            await limiter.check(tenant_id, invoke_request.capability_id, user_id)

            if not await breaker.before_call(service_name):
                raise CapabilityInvokeError(message=f"Circuit breaker is open for service {service_name}. Try again later")

            try:
                logger.info(
                    f"[Sidecar] Forwarding capability call: {invoke_request.capability_id}, "
                    f"tenant: {tenant_id}, auth_type: {auth['auth_type']}"
                )

                result = await self.proxy.invoke_capability(
                    capability_id=invoke_request.capability_id,
                    payload=invoke_request.payload,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    username=username,
                    ip=ip,
                    request_id=trace_id,
                )

                latency = (time.time() - start_time) * 1000
                await breaker.on_success(service_name)
                await metering.record(tenant_id, invoke_request.capability_id, latency, 200, user_id)

                await get_audit_forwarder().collect(
                    tenant_id=tenant_id,
                    method="POST",
                    path=f"invoke/{invoke_request.capability_id}",
                    status_code=200,
                    latency_ms=latency,
                    trace_id=trace_id,
                    user_id=user_id,
                    username=username,
                    ip=ip,
                    service_name="sidecar",
                    invoke_action=_action,
                    is_invoke=True,
                )

                logger.info(
                    f"[Sidecar] Forwarding completed: {invoke_request.capability_id}, "
                    f"success: {result.get('success', True)}, latency: {latency:.2f}ms"
                )

                return InvokeResult(
                    request_id=result.get("request_id", ""),
                    success=result.get("success", True),
                    code=result.get("code", 0),
                    message=result.get("message", "success"),
                    data=result.get("data"),
                    latency_ms=latency,
                )

            except Exception as e:
                latency = (time.time() - start_time) * 1000
                await breaker.on_failure(service_name)
                await metering.record(tenant_id, invoke_request.capability_id, latency, 500, user_id)
                await get_audit_forwarder().collect(
                    tenant_id=tenant_id,
                    method="POST",
                    path=f"invoke/{invoke_request.capability_id}",
                    status_code=500,
                    latency_ms=latency,
                    trace_id=trace_id,
                    user_id=user_id,
                    username=username,
                    ip=ip,
                    service_name="sidecar",
                    invoke_action=_action,
                    is_invoke=True,
                )
                msg = str(e)
                cid = invoke_request.capability_id
                if "Name or service not known" in msg:
                    hint = f"依赖的服务容器未启动或 DNS 无法解析"
                elif "Connection refused" in msg:
                    hint = "依赖的服务端口未就绪"
                else:
                    hint = msg
                logger.error(f"[Sidecar] Forwarding error: {cid}, {hint}, latency={latency:.0f}ms")
                raise CapabilityInvokeError(
                    message=f"Capability call failed: {hint}",
                    cause=e,
                )

        @self.app.post("/invoke/stream")
        async def invoke_capability_stream(
            request: Request,
            invoke_request: CapabilityInvokeRequest,
            auth: dict = Depends(verify_any_auth),
            x_tenant_id: Optional[str] = Header(None),
        ):
            from fastapi.responses import StreamingResponse

            tenant_id = _resolve_invoke_tenant(invoke_request, auth, x_tenant_id)
            user_id = invoke_request.user_id or str(auth.get("user_id", ""))
            import uuid as _uuid
            trace_id = request.headers.get("X-Request-ID") or _uuid.uuid4().hex

            async def _generate():
                async for line in self.proxy.stream_invoke(
                    capability_id=invoke_request.capability_id,
                    payload=invoke_request.payload,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    request_id=trace_id,
                ):
                    yield line + "\n"

            return StreamingResponse(_generate(), media_type="application/x-ndjson")

        @self.app.get("/invoke/stream/rag")
        async def invoke_rag_stream(
            query: str = "",
            mode: str = "hybrid",
            top_k: int = 5,
            knowledge_base_id: str = "",
            auth: dict = Depends(verify_any_auth),
            x_tenant_id: Optional[str] = Header(None),
        ):
            from fastapi.responses import StreamingResponse

            tenant_id = _assert_tenant_matches(
                x_tenant_id,
                _candidate_tenant(auth.get("tenant_id"), "auth"),
                "X-Tenant-ID",
            )
            if tenant_id is None:
                raise TenantIsolationError(message="Streaming RAG queries require an explicit tenant")

            async def _generate():
                async for line in self.proxy.stream_rag_query(
                    query=query, tenant_id=tenant_id, mode=mode, top_k=top_k,
                    knowledge_base_id=knowledge_base_id,
                ):
                    yield line + "\n"

            return StreamingResponse(_generate(), media_type="application/x-ndjson")

    def get_app(self) -> FastAPI:

        return self.app



_sidecar_app: Optional[SidecarApp] = None


def get_sidecar_app() -> SidecarApp:

    global _sidecar_app
    if _sidecar_app is None:
        _sidecar_app = SidecarApp()
    return _sidecar_app
