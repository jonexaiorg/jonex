"""
Gateway shared dependencies - avoid circular imports between main.py and routes/.
"""
from fastapi import Depends, Header

from jonex_core.common.exceptions import MissingApiKeyError


async def require_auth_header(authorization: str = Header(None)) -> str:
    """Check whether the Authorization: Bearer header exists"""
    if not authorization:
        raise MissingApiKeyError(message="Missing Authorization Request headers")
    if not authorization.startswith("Bearer "):
        raise MissingApiKeyError(
            message="Invalid Authorization format, please use: Bearer <token>"
        )
    return authorization
