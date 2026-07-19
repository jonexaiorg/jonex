#!/usr/bin/python3



from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Header

from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import InternalAuthError

logger = get_logger("security")


class InternalAuth:


    def __init__(self):
        self.config = get_config()
        self.secret = self.config.JWT_SECRET
        self.algorithm = self.config.JWT_ALGORITHM

    def generate_token(self, service_name: str) -> str:

        payload = {
            "service": service_name,
            "type": "internal",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> bool:

        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload.get("type") == "internal"
        except jwt.PyJWTError:
            return False

    def get_service_name(self, token: str) -> Optional[str]:

        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") == "internal":
                return payload.get("service")
            return None
        except jwt.PyJWTError:
            return None



_auth_instance: Optional[InternalAuth] = None


def get_internal_auth() -> InternalAuth:

    global _auth_instance
    if _auth_instance is None:
        _auth_instance = InternalAuth()
    return _auth_instance


async def verify_internal_service(
    authorization: Optional[str] = Header(None),
    x_internal_service: Optional[str] = Header(None),
) -> str:

    auth = get_internal_auth()


    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif x_internal_service:
        token = x_internal_service

    if not token:
        logger.warning("Internal service authentication failed: missing Token")
        raise InternalAuthError(message="Internal service authentication failed: missing Token")

    service_name = auth.get_service_name(token)
    if not service_name:
        logger.warning("Internal service authentication failed: invalid Token")
        raise InternalAuthError(message="Internal service authentication failed: invalid Token")

    logger.debug(f"Internal service authentication succeeded: {service_name}")
    return service_name
