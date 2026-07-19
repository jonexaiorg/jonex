#!/usr/bin/python3


from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from functools import lru_cache

from jonex_core.common import get_config, get_logger

logger = get_logger("crypto")


@lru_cache(maxsize=1)
def _fernet():
    from cryptography.fernet import Fernet

    key = os.getenv("DATA_SOURCE_SECRET_KEY", "").strip()
    if not key:

        secret = get_config().JWT_SECRET.encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest()).decode()
        logger.warning("DATA_SOURCE_SECRET_KEY is not configured; derived it from JWT_SECRET (configure it explicitly in production)")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_secret(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    return _fernet().decrypt(ciphertext.encode()).decode()


def generate_ingest_key(tenant_id: str = "", kb_id: str = "", ds_id: str = "") -> str:

    payload = f"{tenant_id}|{kb_id}|{ds_id}|{secrets.token_hex(16)}"
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    sig = _sign_payload(encoded)
    return f"yxk_{encoded}.{sig}"


def hash_ingest_key(plaintext: str) -> str:

    return _sign_payload(plaintext)


def verify_ingest_key(plaintext: str, stored_hash: str) -> bool:
    if not plaintext or not stored_hash:
        return False

    return hmac.compare_digest(_sign_payload(plaintext), stored_hash)


def decode_ingest_key(plaintext: str) -> dict | None:

    try:

        body = plaintext
        if body.startswith("yxk_"):
            body = body[4:]

        if "." in body:
            body = body.rsplit(".", 1)[0]

        padded = body + "=" * (4 - len(body) % 4)
        payload = base64.urlsafe_b64decode(padded).decode()
        parts = payload.split("|")
        if len(parts) >= 3:
            return {"tenant_id": parts[0], "kb_id": parts[1], "ds_id": parts[2]}
    except Exception:
        pass
    return None


def _sign_payload(data: str) -> str:
    secret = get_config().JWT_SECRET.encode()
    return hmac.new(secret, data.encode(), hashlib.sha256).hexdigest()




_VIEW_TOKEN_SCOPE = "kb_raw_view"


def generate_view_token(tenant_id: str, doc_id: str, ttl: int = 300) -> str:

    import time

    import jwt

    payload = {
        "scope": _VIEW_TOKEN_SCOPE,
        "tid": tenant_id,
        "doc": doc_id,
        "exp": int(time.time()) + int(ttl),
    }
    cfg = get_config()
    return jwt.encode(payload, cfg.JWT_SECRET, algorithm=cfg.JWT_ALGORITHM)


def verify_view_token(token: str) -> dict | None:

    if not token:
        return None
    import jwt

    cfg = get_config()
    try:
        payload = jwt.decode(token, cfg.JWT_SECRET, algorithms=[cfg.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("scope") != _VIEW_TOKEN_SCOPE:
        return None
    tid = payload.get("tid")
    doc = payload.get("doc")
    if not tid or not doc:
        return None
    return {"tenant_id": tid, "doc_id": doc}


__all__ = [
    "encrypt_secret",
    "decrypt_secret",
    "generate_ingest_key",
    "hash_ingest_key",
    "verify_ingest_key",
    "decode_ingest_key",
    "generate_view_token",
    "verify_view_token",
]
