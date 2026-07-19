
from fastapi import Depends, Header

from jonex_core.common.exceptions import MissingApiKeyError


async def require_auth_header(authorization: str = Header(None)) -> str:

    if not authorization:
        raise MissingApiKeyError(message="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise MissingApiKeyError(
            message="Invalid Authorization format. Use: Bearer <token>"
        )
    return authorization
