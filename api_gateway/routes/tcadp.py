#!/usr/bin/python3



from typing import Optional, Dict, Any
from fastapi import APIRouter, Header, Request, HTTPException, Depends
from pydantic import BaseModel

from jonex_core.common import get_logger
from jonex_core.integrations.tcadp.adapter import get_tcadp_adapter
from jonex_core.integrations.tcadp.auth import get_tcadp_auth

logger = get_logger("api_tcadp")

router = APIRouter(prefix="/tcadp", tags=["TCADP 集成"])



class WebhookCallbackRequest(BaseModel):

    event_type: str
    data: Dict[str, Any]
    timestamp: int



async def verify_tcadp_signature(request: Request) -> bool:

    adapter = get_tcadp_adapter()

    method = request.method
    path = request.url.path


    headers = {k.lower(): v for k, v in request.headers.items()}


    body = await request.body()
    body_str = body.decode("utf-8")

    if not adapter.verify_request_signature(method, path, headers, body_str):
        logger.warning(f"TCADP signature verification failed: {method} {path}")
        raise HTTPException(status_code=401, detail="TCADP signature verification failed")

    return True



@router.get("/v1/capabilities", summary="获取 TCADP 可用能力列表")
async def list_tcadp_capabilities():

    return {
        "code": 0,
        "message": "success",
        "data": {
            "capabilities": [],
            "total": 0,
        },
    }


@router.post("/v1/webhook/callback", summary="接收 TCADP Webhook 回调")
async def tcadp_webhook_callback(
    request: Request,
    callback_data: WebhookCallbackRequest,
):

    logger.info(f"Received TCADP Webhook callback: event_type={callback_data.event_type}")

    try:

        auth = get_tcadp_auth()
        headers = {k.lower(): v for k, v in request.headers.items()}

        body = await request.body()
        body_str = body.decode("utf-8")

        if not auth.verify_webhook_signature(headers, body_str):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Signature verification failed")




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
        logger.exception(f"Webhook callback processing failed: {e}")
        return {
            "code": 500,
            "message": f"Processing failed: {str(e)}",
            "data": None,
        }
