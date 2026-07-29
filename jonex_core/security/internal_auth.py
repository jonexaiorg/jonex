#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
服务间内部认证

使用 JWT Token 确保只有授权的内部服务可以调用能力服务
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Header

from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import InternalAuthError
from jonex_core.common.i18n import translate

logger = get_logger("security")

# 时钟偏差容忍（秒）。
# 内部 token 在多台机器间流转（尤其本地调试连线上服务时），若签发方时钟略快于
# 校验方，iat/nbf 会落在校验方的"未来"，被 PyJWT 判为无效。
# 签发时将 iat/nbf 回拨该值、校验时给 jwt.decode 加同等 leeway，吸收时钟偏差。
CLOCK_SKEW_LEEWAY_SECONDS = 120


class InternalAuth:
    """内部服务认证"""

    def __init__(self):
        self.config = get_config()
        self.secret = self.config.JWT_SECRET
        self.algorithm = self.config.JWT_ALGORITHM

    def generate_token(self, service_name: str) -> str:
        """
        生成服务间调用的 JWT Token

        Args:
            service_name: 调用方服务名

        Returns:
            JWT Token 字符串
        """
        now = datetime.now(timezone.utc)
        # iat/nbf 回拨 leeway，容忍签发方时钟快于校验方导致的"未来签发"被拒
        issued = now - timedelta(seconds=CLOCK_SKEW_LEEWAY_SECONDS)
        payload = {
            "service": service_name,
            "type": "internal",
            "exp": now + timedelta(minutes=5),
            "iat": issued,
            "nbf": issued,
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> bool:
        """
        验证内部服务调用 Token

        Args:
            token: JWT Token

        Returns:
            是否验证通过
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                leeway=CLOCK_SKEW_LEEWAY_SECONDS,
            )
            return payload.get("type") == "internal"
        except jwt.PyJWTError:
            return False

    def get_service_name(self, token: str) -> Optional[str]:
        """
        从 Token 中解析服务名

        Args:
            token: JWT Token

        Returns:
            服务名，如果验证失败则返回 None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                leeway=CLOCK_SKEW_LEEWAY_SECONDS,
            )
            if payload.get("type") == "internal":
                return payload.get("service")
            return None
        except jwt.PyJWTError:
            return None


# 全局单例
_auth_instance: Optional[InternalAuth] = None


def get_internal_auth() -> InternalAuth:
    """
    获取内部认证实例（单例）

    Returns:
        InternalAuth 实例
    """
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = InternalAuth()
    return _auth_instance


async def verify_internal_service(
    authorization: Optional[str] = Header(None),
    x_internal_service: Optional[str] = Header(None),
) -> str:
    """
    FastAPI 依赖注入：验证内部服务调用

    使用方式:
        @app.post("/invoke")
        async def invoke(service_name: str = Depends(verify_internal_service)):
            ...

    Args:
        authorization: Authorization 请求头
        x_internal_service: X-Internal-Service 请求头（备选方式）

    Returns:
        调用方服务名

    Raises:
        InternalAuthError: 认证失败时抛出 403
    """
    auth = get_internal_auth()

    # 支持两种方式：Authorization Header 或 X-Internal-Service Header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif x_internal_service:
        token = x_internal_service

    if not token:
        logger.warning("内部服务认证失败：缺少 Token")
        raise InternalAuthError(message=translate("err.internal_auth.missing_token", fallback="内部服务认证失败：缺少 Token"))

    service_name = auth.get_service_name(token)
    if not service_name:
        logger.warning("内部服务认证失败：无效的 Token")
        raise InternalAuthError(message=translate("err.internal_auth.invalid_token", fallback="内部服务认证失败：无效的 Token"))

    logger.debug(f"内部服务认证通过: {service_name}")
    return service_name
