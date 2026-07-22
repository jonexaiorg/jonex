#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
TCADP platform dedicated API routes

TCADP API plugin mode:
- TCADP imports plugin definitions via OpenAPI YAML
- TCADP directly invokes registered business routes
- This file provides: authentication dependency + capability list + Webhook callback
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Header, Request, HTTPException, Depends
from pydantic import BaseModel

from jonex_core.common import get_logger
from jonex_core.integrations.tcadp.adapter import get_tcadp_adapter
from jonex_core.integrations.tcadp.auth import get_tcadp_auth

logger = get_logger("api_tcadp")

router = APIRouter(prefix="/tcadp", tags=["TCADP Integration"])


# ==================== Request model ====================
class WebhookCallbackRequest(BaseModel):
    """TCADP Webhook callback request"""
    event_type: str
    data: Dict[str, Any]
    timestamp: int


# ==================== Authentication dependency ====================
async def verify_tcadp_signature(request: Request) -> bool:
    """
    FastAPI dependency: Verify TCADP request signature

    Usage:
    @router.post("/your-endpoint", dependencies=[Depends(verify_tcadp_signature)])
    """
    adapter = get_tcadp_adapter()

    method = request.method
    path = request.url.path

    # Get request headers
    headers = {k.lower(): v for k, v in request.headers.items()}

    # Get request body
    body = await request.body()
    body_str = body.decode("utf-8")

    if not adapter.verify_request_signature(method, path, headers, body_str):
        logger.warning(f"TCADP Signature verification failed: {method} {path}")
        raise HTTPException(status_code=401, detail="TCADP Signature verification failed")

    return True


# ==================== API Interface ====================
@router.get("/v1/capabilities", summary="List available TCADP capabilities")
async def list_tcadp_capabilities():
    """Get all business capabilities currently exposed to TCADP."""
    return {
        "code": 0,
        "message": "success",
        "data": {"capabilities": [], "total": 0},
    }


@router.post("/v1/webhook/callback", summary="Receive TCADP Webhook callback")
async def tcadp_webhook_callback(
    request: Request,
    callback_data: WebhookCallbackRequest,
):
    """
    Receive TCADP platform Webhook callback notification

    Args:
        request: FastAPI Request object
        callback_data: Callback data

    Returns:
        Response
    """
    logger.info(f"Received TCADP Webhook callback: event_type={callback_data.event_type}")

    try:
        # Verify Webhook signature
        auth = get_tcadp_auth()
        headers = {k.lower(): v for k, v in request.headers.items()}

        body = await request.body()
        body_str = body.decode("utf-8")

        if not auth.verify_webhook_signature(headers, body_str):
            logger.warning("Webhook Signature verification failed")
            raise HTTPException(status_code=401, detail="Signature verification failed")

        # TODO: Execute different business logic based on different event_type

        logger.info(f"Webhook callback processed successfully: {callback_data.event_type}")

        return {
            "code": 0,
            "message": "success",
            "data": {
                "event_type": callback_data.event_type,
                "received": True,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Webhook callback processing exception: {e}")
        return {
            "code": 500,
            "message": f"Processing failed: {str(e)}",
            "data": None,
        }
