#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
TCADP platform authentication signature module

Implements TCADP API signature and verification functions:
1. Request signature generation (HMAC-SHA256)
2. Response signature generation
3. Webhook callback signature verification
"""

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
    """TCADP authentication signature class"""

    def __init__(self, api_key: Optional[str] = None, webhook_secret: Optional[str] = None):
        """
        Initialize authentication client

        Args:
            api_key: TCADP API key (read from configuration by default)
            webhook_secret: TCADP Webhook signature secret (read from configuration by default)
        """
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
        """
        Generate API request signature

        Signature algorithm:
            1. Concatenate request method + request path + timestamp + ordered query parameters + JSON body
            2. Use HMAC-SHA256 signature, key is API KEY
            3. Convert result to hexadecimal string

        Args:
            method: HTTP request method (GET/POST/PUT/DELETE)
            path: Request path (e.g.: /api/v1/capabilities/register)
            params: Query parameters
            body: Request body
            timestamp: Timestamp (seconds, default uses current time)

        Returns:
            str: Signature string
        """
        if not self.api_key:
            logger.warning("TCADP_API_KEY not configured, using empty signature")
            return ""

        if timestamp is None:
            timestamp = int(time.time())

        # Build signature content
        signature_parts = [
            method.upper(),
            path,
            str(timestamp),
        ]

        # Add query parameters (concatenated after sorting by key)
        if params:
            sorted_params = sorted(params.items(), key=lambda x: x[0])
            query_string = urlencode(sorted_params)
            signature_parts.append(query_string)

        # Add request body (JSON string)
        if body:
            body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
            signature_parts.append(body_json)

        # Concatenate all parts
        signature_string = "\n".join(signature_parts)

        # HMAC-SHA256 signature
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
        """
        Get authentication request headers

        Args:
            method: HTTP request method
            path: Request path
            params: Query parameters
            body: Request body

        Returns:
            Dict[str, str]: Request headers dict, includes X-API-Key, X-Timestamp, X-Signature
        """
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
        """
        Verify Webhook callback signature

        Args:
            headers: Webhook headers
            body: Webhook body (raw string)

        Returns:
            bool: Whether signature is valid
        """
        if not self.webhook_secret:
            logger.warning("TCADP_WEBHOOK_SECRET not configured, skipping Webhook signature verification")
            return True

        # Get signature and timestamp from request headers
        signature = headers.get("X-Webhook-Signature", "")
        timestamp = headers.get("X-Webhook-Timestamp", "")

        if not signature or not timestamp:
            logger.warning("Webhook request missing signature or timestamp")
            return False

        # Check if timestamp is within 5 minutes (prevent replay attacks)
        try:
            ts = int(timestamp)
            now = int(time.time())
            if abs(now - ts) > 5 * 60:
                logger.warning(f"Webhook timestamp expired: {ts} vs {now}")
                return False
        except ValueError:
            logger.warning(f"Invalid timestamp: {timestamp}")
            return False

        # Calculate expected signature
        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            f"{timestamp}.{body}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Safe signature comparison (prevent timing attacks)
        is_valid = hmac.compare_digest(signature, expected_signature)

        if not is_valid:
            logger.warning(f"Webhook Signature verification failed: {signature[:16]}... vs {expected_signature[:16]}...")

        return is_valid


# Global singleton
_auth_instance: Optional[TCADPAuth] = None


def get_tcadp_auth() -> TCADPAuth:
    """Get TCADP authentication client instance"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = TCADPAuth()
    return _auth_instance
