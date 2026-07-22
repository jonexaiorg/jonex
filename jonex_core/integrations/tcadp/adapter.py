"""
Tencent TCADP platform integration adapter

TCADP API plugin mode:
1. TCADP imports plugin definitions via OpenAPI YAML
2. TCADP directly calls registered business routes of Jonex platform
3. Jonex platform verifies TCADP request signature, processes and returns result
4. Async scenario: Jonex notifies via Webhook callback TCADP
"""

import httpx
import logging
from typing import Dict, Any, Optional

from jonex_core.common import get_config, get_logger
from jonex_core.integrations.tcadp.auth import get_tcadp_auth

logger = get_logger("tcadp.adapter")


class TCADPAdapter:
    """TCADP platform adapter

    Functions:
    1. Verify request signature from TCADP platform (used by middleware)
    2. Send Webhook callback to TCADP after async processing completes
    """

    def __init__(self):
        self.config = get_config()
        self.auth = get_tcadp_auth()
        self.tcadp_api_url = self.config.TCADP_API_URL
        self.tcadp_webhook_url = self.config.TCADP_WEBHOOK_URL

    def verify_request_signature(self, method: str, path: str, headers: Dict[str, str], body: str) -> bool:
        """
        Verify TCADP request signature

        Args:
            method: HTTP method (GET/POST/PUT/DELETE)
            path: Request path (e.g.: /api/v1/knowledge-base/)
            headers: Request headers
            body: Request body string

        Returns:
            bool: Whether signature is valid
        """
        if not self.config.TCADP_API_KEY:
            logger.warning("TCADP_API_KEY not configured, skipping signature verification")
            return True

        return self.auth.verify_webhook_signature(headers, body)

    async def send_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Send event callback to TCADP platform (async capability scenario)

        Args:
            event_type: Event type
            payload: Event data

        Returns:
            bool: Whether sent successfully
        """
        if not self.tcadp_webhook_url:
            logger.warning("TCADP_WEBHOOK_URL not configured, skipping webhook send")
            return False

        import time

        body = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": int(time.time()),
        }

        try:
            if self.config.ENV == "dev":
                logger.info(f"[Mock] Development environment, skipping real webhook send: {self.tcadp_webhook_url}")
                logger.info(f"[Mock] event_type: {event_type}, payload: {payload}")
                return True

            async with httpx.AsyncClient(timeout=self.config.TCADP_TIMEOUT) as client:
                path = "/webhook/tcadp/callback"
                headers = self.auth.get_auth_headers("POST", path, body=body)

                response = await client.post(
                    self.tcadp_webhook_url,
                    json=body,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

                if result.get("code") == 0:
                    logger.info(f"Webhook sent successfully: {event_type}")
                    return True
                else:
                    logger.error(f"Webhook send failed: {result.get('message')}")
                    return False

        except Exception as e:
            logger.exception(f"Webhook send exception: {e}")
            return False

    async def call_tcadp_api(self, path: str, method: str = "POST", body: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Invoke TCADP platform API (generic method)

        Args:
            path: API path
            method: HTTP method
            body: Request body

        Returns:
            API response
        """
        if not self.tcadp_api_url:
            raise ValueError("Not configured TCADP_API_URL")

        api_url = f"{self.tcadp_api_url.rstrip('/')}{path}"
        body = body or {}

        try:
            async with httpx.AsyncClient(timeout=self.config.TCADP_TIMEOUT) as client:
                headers = self.auth.get_auth_headers(method, path, body=body)

                if method.upper() == "GET":
                    response = await client.get(api_url, headers=headers)
                else:
                    response = await client.post(api_url, json=body, headers=headers)

                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.exception(f"Invoke TCADP API failed: {method} {api_url}")
            raise


# Global singleton
_adapter_instance: Optional[TCADPAdapter] = None


def get_tcadp_adapter() -> TCADPAdapter:
    """Get TCADP adapter instance"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = TCADPAdapter()
    return _adapter_instance
