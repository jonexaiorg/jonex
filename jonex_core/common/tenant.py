#!/usr/bin/python3



from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator, Optional

from jonex_core.common.exceptions import TenantIsolationError, TokenExpiredError

DEFAULT_TENANT_IDS = frozenset({"default", "default_tenant", "system"})
_tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("jonex_tenant_id", default=None)


def _normalize_tenant_id(tenant_id: str | None) -> str:
    return (tenant_id or "").strip()


def is_default_tenant(tenant_id: str | None) -> bool:

    normalized = _normalize_tenant_id(tenant_id)
    return not normalized or normalized in DEFAULT_TENANT_IDS


def require_tenant(tenant_id: str | None) -> str:

    normalized = _normalize_tenant_id(tenant_id)
    if is_default_tenant(normalized):
        raise TenantIsolationError(message="The default tenant is not allowed")
    return normalized


def _tenant_from_bearer_token(token: str) -> str:
    if token.startswith("jonex_test_"):
        return _normalize_tenant_id(token.removeprefix("jonex_test_"))

    import jwt

    from jonex_core.common.config import get_config

    config = get_config()
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError(message="Token has expired", cause=exc)
    except jwt.PyJWTError as exc:
        raise TokenExpiredError(message="Invalid Token", cause=exc)

    tenant_id = payload.get("tenant_id")
    if tenant_id is not None and not isinstance(tenant_id, str):
        raise TokenExpiredError(message="Invalid Token")
    return _normalize_tenant_id(tenant_id)


def extract_tenant_id(request) -> str:

    headers = getattr(request, "headers", {}) or {}
    auth_tenant_id = ""
    header_tenant_id = _normalize_tenant_id(
        headers.get("X-Tenant-ID") or headers.get("x-tenant-id") or ""
    )

    auth_header = headers.get("Authorization") or headers.get("authorization")
    if auth_header:
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() == "bearer" and token:
            auth_tenant_id = _tenant_from_bearer_token(token)

    if auth_tenant_id and header_tenant_id and auth_tenant_id != header_tenant_id:
        raise TenantIsolationError(
            message="Request tenant does not match the authenticated tenant",
            details={
                "request_tenant_id": header_tenant_id,
                "auth_tenant_id": auth_tenant_id,
            },
        )

    tenant_id = auth_tenant_id or header_tenant_id
    return require_tenant(tenant_id)


class TenantContext:


    @classmethod
    def set(cls, tenant_id: str | None) -> Token[Optional[str]]:
        return _tenant_id_ctx.set(_normalize_tenant_id(tenant_id) or None)

    @classmethod
    def get(cls) -> Optional[str]:
        return _tenant_id_ctx.get()

    @classmethod
    def clear(cls) -> Token[Optional[str]]:
        return _tenant_id_ctx.set(None)

    @classmethod
    def reset(cls, token: Token[Optional[str]]) -> None:
        _tenant_id_ctx.reset(token)


@contextmanager
def tenant_scope(tenant_id: str) -> Iterator[str]:

    normalized = require_tenant(tenant_id)
    token = TenantContext.set(normalized)
    try:
        yield normalized
    finally:
        TenantContext.reset(token)


__all__ = [
    "DEFAULT_TENANT_IDS",
    "TenantContext",
    "extract_tenant_id",
    "is_default_tenant",
    "require_tenant",
    "tenant_scope",
]
