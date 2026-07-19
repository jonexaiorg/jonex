
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, Header

from jonex_core.common.config import get_config
from jonex_core.common.exceptions import TokenExpiredError, PermissionDeniedError

logger = logging.getLogger(__name__)


class UserAuth:


    def __init__(self):
        config = get_config()
        self.secret = config.JWT_SECRET
        self.algorithm = config.JWT_ALGORITHM
        self.access_expire_hours = config.USER_JWT_EXPIRE_HOURS
        self.refresh_expire_days = config.USER_JWT_REFRESH_DAYS
        self.bcrypt_rounds = config.BCRYPT_ROUNDS

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=self.bcrypt_rounds)).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def _create_token(self, user, expires_delta: timedelta, token_type: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "tenant_id": user.tenant_id,
            "username": user.username,
            "role": user.role,
            "type": token_type,
            "exp": now + expires_delta,
            "iat": now,
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_access_token(self, user) -> str:
        return self._create_token(user, timedelta(hours=self.access_expire_hours), "user")

    def create_refresh_token(self, user) -> str:
        return self._create_token(user, timedelta(days=self.refresh_expire_days), "refresh")

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") not in ("user", "refresh"):
                raise TokenExpiredError(message="Invalid Token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError(message="Token has expired")
        except jwt.PyJWTError as e:
            logger.warning(f"JWT signature verification failed: {e}")
            raise TokenExpiredError(message="Invalid Token")


    def create_login_ticket_plaintext(self) -> str:

        return secrets.token_urlsafe(32)

    def hash_login_ticket(self, ticket: str) -> str:

        return hmac.new(
            self.secret.encode(),
            ticket.encode(),
            hashlib.sha256,
        ).hexdigest()


_user_auth_instance: Optional[UserAuth] = None


def get_user_auth() -> UserAuth:
    global _user_auth_instance
    if _user_auth_instance is None:
        _user_auth_instance = UserAuth()
    return _user_auth_instance


async def get_current_user(authorization: str = Header(...)) -> dict:

    if not authorization.startswith("Bearer "):
        raise TokenExpiredError(message="Missing Bearer token")
    token = authorization[7:]
    auth = get_user_auth()
    payload = auth.decode_token(token)
    return {
        "user_id": int(payload["sub"]),
        "tenant_id": payload["tenant_id"],
        "username": payload["username"],
        "role": payload["role"],
    }


def require_role(*roles: str):


    async def _check_role(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise PermissionDeniedError(
                message=f"Required role: {', '.join(roles)}; current role: {current_user['role']}"
            )
        return current_user

    return _check_role
