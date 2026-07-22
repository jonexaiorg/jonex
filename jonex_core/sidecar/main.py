#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Sidecar proxy main application

Unified entry, handles all capability invocations, providing:
- API Key authentication
- Invocation metering
- Rate limiting and circuit breaking
- Log tracing
- Capability service reverse proxy
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, Request, Header
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import select

from jonex_core.sidecar.proxy import get_capability_proxy
from jonex_core.common import (
    register_exception_handlers,
    MissingApiKeyError,
    InvalidApiKeyError,
    CapabilityInvokeError,
    TokenExpiredError,
    PermissionDeniedError,
)
from jonex_core.common.config import get_config
from jonex_core.common.database import get_db
from jonex_core.models.user import User
from jonex_core.models.login_ticket import LoginTicket
from jonex_core.security.user_auth import get_user_auth

logger = logging.getLogger(__name__)


class CapabilityInvokeRequest(BaseModel):
    """Capability invocation request"""
    capability_id: str
    payload: dict
    tenant_id: str
    user_id: Optional[str] = None
    context: Optional[dict] = None


class InvokeResult(BaseModel):
    """Invocation result"""
    request_id: str
    success: bool
    code: int
    message: str
    data: Optional[dict] = None
    latency_ms: float


class LoginRequest(BaseModel):
    """User login request"""
    username: str
    password: str


class UserInfo(BaseModel):
    """User information"""
    user_id: int
    username: str
    display_name: Optional[str] = None
    tenant_id: str
    role: str


class LoginResponse(BaseModel):
    """User login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class LoginTicketRequest(BaseModel):
    """Create one-time login ticket request"""
    appId: str
    redirectUri: str
    state: Optional[str] = None


class LoginTicketResponse(BaseModel):
    """Create one-time login ticket response"""
    ticket: str
    expires_in: int


class ExchangeTicketRequest(BaseModel):
    """Redeem one-time login ticket request"""
    appId: str
    ticket: str
    redirectUri: str
    state: Optional[str] = None


class SidecarApp:
    """Sidecar application class"""

    def __init__(self):
        self.app = FastAPI(
            title="Jonex Platform Sidecar",
            description="Jonex platform capability proxy - unified entry (internal service)",
            version="1.0.0"
        )
        self.proxy = get_capability_proxy()
        self._setup_routes()
        # Register unified exception handlers
        register_exception_handlers(self.app)

    def _setup_routes(self):
        """Set up routes"""

        api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

        async def verify_any_auth(
            api_key: Optional[str] = Depends(api_key_header),
            authorization: Optional[str] = Header(None),
        ) -> dict:
            """Either-or authentication: prioritize Authorization: Bearer <user_jwt>, then X-API-Key"""
            if authorization and authorization.startswith("Bearer "):
                token = authorization[7:]
                user_auth = get_user_auth()
                try:
                    payload = user_auth.decode_token(token)
                except TokenExpiredError:
                    raise
                return {
                    "auth_type": "user",
                    "tenant_id": payload["tenant_id"],
                    "user_id": int(payload["sub"]),
                }
            if api_key and api_key.startswith("jonex_"):
                tenant_id = api_key.replace("jonex_test_", "")
                return {"auth_type": "apikey", "tenant_id": tenant_id}
            raise MissingApiKeyError()

        # ==================== System endpoints ====================

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
                    "name": f"{name} Capability service",
                    "type": "business",
                    "version": "v1",
                    "endpoint": endpoint,
                }
                for name, endpoint in self.proxy.capability_endpoints.items()
                if endpoint
            ]
            return {"capabilities": capabilities}

        # ==================== Authentication endpoints ====================

        @self.app.post("/auth/login", response_model=LoginResponse)
        async def auth_login(login_req: LoginRequest, db=Depends(get_db)):
            result = await db.execute(
                select(User).where(
                    User.tenant_id == "default_tenant",
                    User.username == login_req.username,
                    User.status == 1,
                    User.is_deleted == 0,
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                raise InvalidApiKeyError(message="Invalid username or password")

            user_auth = get_user_auth()
            if not user_auth.verify_password(login_req.password, user.password_hash):
                raise InvalidApiKeyError(message="Invalid username or password")

            access_token = user_auth.create_access_token(user)
            refresh_token = user_auth.create_refresh_token(user)

            logger.info(f"User logged in successfully: {user.username} (id={user.id})")

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=user_auth.access_expire_hours * 3600,
                user=UserInfo(
                    user_id=user.id,
                    username=user.username,
                    display_name=user.display_name,
                    tenant_id=user.tenant_id,
                    role=user.role,
                ),
            )

        @self.app.get("/auth/me", response_model=UserInfo)
        async def auth_me(authorization: str = Header(...)):
            if not authorization.startswith("Bearer "):
                raise TokenExpiredError(message="Missing Bearer token")
            user_auth = get_user_auth()
            payload = user_auth.decode_token(authorization[7:])
            return UserInfo(
                user_id=int(payload["sub"]),
                username=payload["username"],
                display_name=None,
                tenant_id=payload["tenant_id"],
                role=payload["role"],
            )

        @self.app.post("/auth/refresh", response_model=LoginResponse)
        async def auth_refresh(authorization: str = Header(...), db=Depends(get_db)):
            if not authorization.startswith("Bearer "):
                raise TokenExpiredError(message="Missing Bearer token")
            user_auth = get_user_auth()
            payload = user_auth.decode_token(authorization[7:])
            if payload.get("type") != "refresh":
                raise TokenExpiredError(message="Please use refresh token to refresh")

            result = await db.execute(
                select(User).where(
                    User.id == int(payload["sub"]),
                    User.status == 1,
                    User.is_deleted == 0,
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                raise InvalidApiKeyError(message="User not found or disabled")

            access_token = user_auth.create_access_token(user)
            refresh_token = user_auth.create_refresh_token(user)

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=user_auth.access_expire_hours * 3600,
                user=UserInfo(
                    user_id=user.id,
                    username=user.username,
                    display_name=user.display_name,
                    tenant_id=user.tenant_id,
                    role=user.role,
                ),
            )

        # ==================== Ticket endpoints ====================

        @self.app.post("/auth/login-ticket", response_model=LoginTicketResponse)
        async def auth_login_ticket(
            req: LoginTicketRequest,
            authorization: str = Header(...),
            request: Request = None,
            db=Depends(get_db),
        ):
            """Create one-time login ticket - requires Bearer token"""
            if not authorization.startswith("Bearer "):
                raise TokenExpiredError(message="Missing Bearer token")
            user_auth = get_user_auth()
            payload = user_auth.decode_token(authorization[7:])

            # Verify user is still enabled
            result = await db.execute(
                select(User).where(
                    User.id == int(payload["sub"]),
                    User.status == 1,
                    User.is_deleted == 0,
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                raise InvalidApiKeyError(message="User not found or disabled")

            # Verify redirect whitelist
            config = get_config()
            try:
                allowed = json.loads(config.AUTH_ALLOWED_REDIRECT_URIS) if config.AUTH_ALLOWED_REDIRECT_URIS else {}
            except json.JSONDecodeError:
                logger.error(f"AUTH_ALLOWED_REDIRECT_URIS Parsing failed: {config.AUTH_ALLOWED_REDIRECT_URIS}")
                raise PermissionDeniedError(message="redirect whitelist configuration error")

            allowed_uris = allowed.get(req.appId, [])
            if not allowed_uris:
                raise PermissionDeniedError(message=f"No whitelist configuration found for appId={req.appId}")
            if not any(req.redirectUri.startswith(u) for u in allowed_uris):
                raise PermissionDeniedError(message=f"redirectUri is not in the whitelist: {req.redirectUri}")

            # Generate ticket, write to DB
            ticket_plain = user_auth.create_login_ticket_plaintext()
            ticket_hash = user_auth.hash_login_ticket(ticket_plain)
            expire_seconds = config.LOGIN_TICKET_EXPIRE_SECONDS
            expires_at = datetime.utcnow() + timedelta(seconds=expire_seconds)

            client_ip = request.client.host if request and request.client else None
            user_agent = request.headers.get("User-Agent", "")[:1024] if request else None

            ticket_record = LoginTicket(
                ticket_hash=ticket_hash,
                tenant_id=user.tenant_id,
                user_id=user.id,
                app_id=req.appId,
                redirect_uri=req.redirectUri,
                state=req.state,
                expires_at=expires_at,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            db.add(ticket_record)
            await db.commit()

            logger.info(
                f"Created login ticket: hash={ticket_hash[:8]}... user={user.username} "
                f"app={req.appId} redirect={req.redirectUri}"
            )

            return LoginTicketResponse(ticket=ticket_plain, expires_in=expire_seconds)

        @self.app.post("/auth/exchange-ticket", response_model=LoginResponse)
        async def auth_exchange_ticket(req: ExchangeTicketRequest, db=Depends(get_db)):
            """Redeem one-time ticket, returns access token - no Authorization required"""
            user_auth = get_user_auth()
            ticket_hash = user_auth.hash_login_ticket(req.ticket)

            result = await db.execute(
                select(LoginTicket).where(LoginTicket.ticket_hash == ticket_hash)
            )
            ticket_record = result.scalar_one_or_none()

            if not ticket_record:
                raise InvalidApiKeyError(message="Ticket not found or invalid format")

            now = datetime.utcnow()
            if ticket_record.expires_at < now:
                raise TokenExpiredError(message="ticket Expired or already used")
            if ticket_record.used_at is not None:
                raise TokenExpiredError(message="ticket Expired or already used")

            # Verify binding information
            if ticket_record.app_id != req.appId:
                raise PermissionDeniedError(message="appId Inconsistent with ticket binding")
            if ticket_record.redirect_uri != req.redirectUri:
                raise PermissionDeniedError(message="redirectUri Inconsistent with ticket binding")
            if ticket_record.state != req.state:
                raise PermissionDeniedError(message="state Inconsistent with ticket binding")

            # Mark as used within the transaction to prevent concurrent duplicate redemption
            ticket_record.used_at = now
            await db.flush()

            # Query user
            result = await db.execute(
                select(User).where(
                    User.id == ticket_record.user_id,
                    User.status == 1,
                    User.is_deleted == 0,
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                await db.rollback()
                raise InvalidApiKeyError(message="User not found or disabled")

            access_token = user_auth.create_access_token(user)
            refresh_token = user_auth.create_refresh_token(user)
            await db.commit()

            logger.info(
                f"Redeemed login ticket successfully: hash={ticket_hash[:8]}... user={user.username} "
                f"app={req.appId}"
            )

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=user_auth.access_expire_hours * 3600,
                user=UserInfo(
                    user_id=user.id,
                    username=user.username,
                    display_name=user.display_name,
                    tenant_id=user.tenant_id,
                    role=user.role,
                ),
            )

        # ==================== Capability invocation endpoint ====================

        @self.app.post("/invoke", response_model=InvokeResult)
        async def invoke_capability(
            request: Request,
            invoke_request: CapabilityInvokeRequest,
            auth: dict = Depends(verify_any_auth),
        ):
            start_time = time.time()
            tenant_id = invoke_request.tenant_id or auth.get("tenant_id", "default_tenant")
            user_id = invoke_request.user_id or str(auth.get("user_id", ""))

            try:
                logger.info(
                    f"[Sidecar] Forward capability invocation: {invoke_request.capability_id}, "
                    f"tenant: {tenant_id}, auth_type: {auth['auth_type']}"
                )

                result = await self.proxy.invoke_capability(
                    capability_id=invoke_request.capability_id,
                    payload=invoke_request.payload,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )

                latency = (time.time() - start_time) * 1000

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
                msg = str(e)
                # Convert common network errors to friendly hints
                cid = invoke_request.capability_id
                if "Name or service not known" in msg:
                    hint = f"Dependency service container not started or DNS unresolvable"
                elif "Connection refused" in msg:
                    hint = "Dependency service port not ready"
                else:
                    hint = msg
                logger.error(f"[Sidecar] Forwarding exception: {cid}, {hint}, latency={latency:.0f}ms")
                raise CapabilityInvokeError(
                    message=f"Capability invocation failed: {hint}",
                    cause=e,
                )

        @self.app.post("/invoke/stream")
        async def invoke_capability_stream(
            request: Request,
            invoke_request: CapabilityInvokeRequest,
            auth: dict = Depends(verify_any_auth),
        ):
            from fastapi.responses import StreamingResponse

            tenant_id = invoke_request.tenant_id or auth.get("tenant_id", "default_tenant")
            user_id = invoke_request.user_id or str(auth.get("user_id", ""))

            async def _generate():
                async for line in self.proxy.stream_invoke(
                    capability_id=invoke_request.capability_id,
                    payload=invoke_request.payload,
                    tenant_id=tenant_id,
                    user_id=user_id,
                ):
                    yield line + "\n"

            return StreamingResponse(_generate(), media_type="application/x-ndjson")

        @self.app.get("/invoke/stream/rag")
        async def invoke_rag_stream(
            query: str = "",
            mode: str = "hybrid",
            top_k: int = 5,
            auth: dict = Depends(verify_any_auth),
        ):
            from fastapi.responses import StreamingResponse

            tenant_id = auth.get("tenant_id", "default_tenant")

            async def _generate():
                async for line in self.proxy.stream_rag_query(
                    query=query, tenant_id=tenant_id, mode=mode, top_k=top_k,
                ):
                    yield line + "\n"

            return StreamingResponse(_generate(), media_type="application/x-ndjson")

    def register_capability(self, capability):
        """
        Register capability (deprecated: retained for backward compatibility, does nothing actually)

        Warning: Sidecar now uses reverse proxy mode and does not directly hold capability instances.
        Capabilities should be deployed as independent services and registered to service discovery.
        """
        logger.warning(
            f"[DEPRECATED] register_capability is deprecated: {capability.get_metadata().full_id} "
            f"Please use the independent capability service deployment mode"
        )

    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.app


# Global singleton
_sidecar_app: Optional[SidecarApp] = None


def get_sidecar_app() -> SidecarApp:
    """Get global Sidecar application instance"""
    global _sidecar_app
    if _sidecar_app is None:
        _sidecar_app = SidecarApp()
    return _sidecar_app
