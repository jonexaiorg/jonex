#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
租户上下文与入口提取规范。

业务资源必须使用显式租户，禁止落入 default/default_tenant/system。
"""

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator, Optional

from jonex_core.common.exceptions import TenantIsolationError, TokenExpiredError
from jonex_core.common.i18n import translate

DEFAULT_TENANT_IDS = frozenset({"default", "default_tenant", "system"})
_tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("jonex_tenant_id", default=None)


def _normalize_tenant_id(tenant_id: str | None) -> str:
    return (tenant_id or "").strip()


def is_default_tenant(tenant_id: str | None) -> bool:
    """判断是否为空租户或平台默认租户。"""
    normalized = _normalize_tenant_id(tenant_id)
    return not normalized or normalized in DEFAULT_TENANT_IDS


def require_tenant(tenant_id: str | None) -> str:
    """返回合法业务租户；为空或默认租户时直接阻断。"""
    normalized = _normalize_tenant_id(tenant_id)
    if is_default_tenant(normalized):
        raise TenantIsolationError(message=translate("err.tenant.default_forbidden", fallback="禁止使用默认租户"))
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
        raise TokenExpiredError(cause=exc)  # Token 签名已过期
    except jwt.PyJWTError as exc:
        raise TokenExpiredError(cause=exc)  # Token 格式无效或签名校验失败

    tenant_id = payload.get("tenant_id")
    if tenant_id is not None and not isinstance(tenant_id, str):
        raise TokenExpiredError()  # Token payload 中 tenant_id 类型不合法
    return _normalize_tenant_id(tenant_id)


def extract_tenant_id(request) -> str:
    """
    从请求中提取租户。

    优先级：
    1. Authorization: Bearer {JWT} 中的 tenant_id
    2. Authorization: Bearer jonex_test_{tenant_id}
    3. X-Tenant-ID

    当 JWT/测试 Token 与 X-Tenant-ID 同时存在时，二者必须一致。
    """
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
            message=translate("err.tenant.mismatch", fallback="请求租户与认证租户不一致"),
            details={
                "request_tenant_id": header_tenant_id,
                "auth_tenant_id": auth_tenant_id,
            },
        )

    tenant_id = auth_tenant_id or header_tenant_id
    return require_tenant(tenant_id)


class TenantContext:
    """基于 contextvars 的异步安全租户上下文。"""

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
    """在当前执行上下文中绑定合法业务租户。"""
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
