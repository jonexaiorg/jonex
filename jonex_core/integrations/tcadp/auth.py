#!/usr/bin/python3



import hmac
import hashlib
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import InvalidParameterError

logger = get_logger("tcadp.auth")


class TCADPAuth:


    def __init__(self, api_key: Optional[str] = None, webhook_secret: Optional[str] = None):

        config = get_config()
        self.api_key = api_key or config.TCADP_API_KEY or ""
        self.webhook_secret = webhook_secret or config.TCADP_WEBHOOK_SECRET or ""

    def generate_signature(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
    ) -> str:

        if not self.api_key:
            logger.warning("TCADP_API_KEY is not configured; using an empty signature")
            return ""

        if timestamp is None:
            timestamp = int(time.time())


        signature_parts = [
            method.upper(),
            path,
            str(timestamp),
        ]


        if params:
            sorted_params = sorted(params.items(), key=lambda x: x[0])
            query_string = urlencode(sorted_params)
            signature_parts.append(query_string)


        if body:
            body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
            signature_parts.append(body_json)


        signature_string = "\n".join(signature_parts)


        signature = hmac.new(
            self.api_key.encode("utf-8"),
            signature_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        logger.debug(f"Generated signature: timestamp={timestamp}, signature={signature[:16]}...")
        return signature

    def get_auth_headers(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:

        timestamp = int(time.time())
        signature = self.generate_signature(method, path, params, body, timestamp)

        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": str(timestamp),
            "X-Signature": signature,
            "Content-Type": "application/json",
        }

    def verify_webhook_signature(
        self,
        headers: Dict[str, str],
        body: str,
    ) -> bool:

        if not self.webhook_secret:
            logger.warning("TCADP_WEBHOOK_SECRET is not configured; skipping Webhook signature verification")
            return True


        signature = headers.get("X-Webhook-Signature", "")
        timestamp = headers.get("X-Webhook-Timestamp", "")

        if not signature or not timestamp:
            logger.warning("Webhook request is missing a signature or timestamp")
            return False


        try:
            ts = int(timestamp)
            now = int(time.time())
            if abs(now - ts) > 5 * 60:
                logger.warning(f"Webhook timestamp expired: {ts} vs {now}")
                return False
        except ValueError:
            logger.warning(f"Invalid timestamp: {timestamp}")
            return False


        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            f"{timestamp}.{body}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


        is_valid = hmac.compare_digest(signature, expected_signature)

        if not is_valid:
            logger.warning(f"Webhook signature verification failed: {signature[:16]}... vs {expected_signature[:16]}...")

        return is_valid



_auth_instance: Optional[TCADPAuth] = None


def get_tcadp_auth() -> TCADPAuth:

    global _auth_instance
    if _auth_instance is None:
        _auth_instance = TCADPAuth()
    return _auth_instance
