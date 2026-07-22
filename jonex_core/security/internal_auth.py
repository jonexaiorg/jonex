#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Inter-service internal authentication

Uses JWT tokens to ensure only authorized internal services can invoke capability services
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Header

from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import InternalAuthError

logger = get_logger("security")


class InternalAuth:
    """Internal service authentication"""

    def __init__(self):
        self.config = get_config()
        self.secret = self.config.JWT_SECRET
        self.algorithm = self.config.JWT_ALGORITHM

    def generate_token(self, service_name: str) -> str:
        """
        Generate JWT token for inter-service invocation

        Args:
            service_name: Caller service name

        Returns:
            JWT Token string
        """
        payload = {
            "service": service_name,
            "type": "internal",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> bool:
        """
        Verify internal service invocation token

        Args:
            token: JWT Token

        Returns:
            Whether verification passed
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload.get("type") == "internal"
        except jwt.PyJWTError:
            return False

    def get_service_name(self, token: str) -> Optional[str]:
        """
        Parse service name from token

        Args:
            token: JWT Token

        Returns:
            Service name, returns None if verification fails
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") == "internal":
                return payload.get("service")
            return None
        except jwt.PyJWTError:
            return None


# Global singleton
_auth_instance: Optional[InternalAuth] = None


def get_internal_auth() -> InternalAuth:
    """
    Get internal authentication instance (singleton)

    Returns:
        InternalAuth instance
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
    FastAPI dependency injection: verify internal service invocation

    Usage:
        @app.post("/invoke")
        async def invoke(service_name: str = Depends(verify_internal_service)):
            ...

    Args:
        authorization: Authorization request header
        x_internal_service: X-Internal-Service header (alternative method)

    Returns:
        Caller service name

    Raises:
        InternalAuthError: Raised when authentication fails 403
    """
    auth = get_internal_auth()

    # Supports two methods: Authorization header or X-Internal-Service header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif x_internal_service:
        token = x_internal_service

    if not token:
        logger.warning("Internal service authentication failed: Missing Token")
        raise InternalAuthError(message="Internal service authentication failed: Missing Token")

    service_name = auth.get_service_name(token)
    if not service_name:
        logger.warning("Internal service authentication failed: Invalid Token")
        raise InternalAuthError(message="Internal service authentication failed: Invalid Token")

    logger.debug(f"Internal service authentication passed: {service_name}")
    return service_name
