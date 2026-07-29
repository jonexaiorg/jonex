"""
Gateway 共享依赖 — 避免 main.py 与 routes/ 之间循环导入。
"""
from fastapi import Depends, Header

from jonex_core.common.exceptions import MissingApiKeyError, get_exception_class, JonexException, CapabilityInvokeError
from jonex_core.common.i18n import translate


async def require_auth_header(authorization: str = Header(None)) -> str:
    """检查 Authorization: Bearer 头是否存在"""
    if not authorization:
        raise MissingApiKeyError(message=translate("err.auth.missing_auth_header", fallback="缺少 Authorization 请求头"))
    if not authorization.startswith("Bearer "):
        raise MissingApiKeyError(
            message=translate("err.auth.invalid_auth_format", fallback="Authorization 格式无效，请使用: Bearer <token>")
        )
    return authorization


def raise_from_capability_result(result: dict):
    """把下游能力信封错误重建为带真实 code/params 的异常，交全局 handler 翻译。

    下游若已用 code+params 抛出，Gateway 重建的异常带真实 code+params，
    经 handler -> error_response 命中模板翻译；若仍是历史显式原文，params 为空、原样返回不回归。
    """
    code = result.get("code", 2002)
    if isinstance(code, str):
        try:
            code = int(code)
        except (ValueError, TypeError):
            code = 2002
    exc_cls = get_exception_class(code)
    if not issubclass(exc_cls, JonexException):
        exc_cls = CapabilityInvokeError
    raise exc_cls(
        message=result.get("message"),
        details=result.get("details") or None,
        params=result.get("params") or None,
    )
