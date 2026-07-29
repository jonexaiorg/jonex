#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
TCADP 平台专用 API 路由

TCADP API 插件模式：
- TCADP 通过 OpenAPI YAML 导入插件定义
- TCADP 直接调用业务路由
- 本文件提供：认证依赖 + 能力列表 + Webhook 回调
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Header, Request, HTTPException, Depends
from pydantic import BaseModel

from jonex_core.common import get_logger
from jonex_core.integrations.tcadp.adapter import get_tcadp_adapter
from jonex_core.integrations.tcadp.auth import get_tcadp_auth

logger = get_logger("api_tcadp")

router = APIRouter(prefix="/tcadp", tags=["TCADP 集成"])


# ==================== 请求模型 ====================
class WebhookCallbackRequest(BaseModel):
    """TCADP Webhook 回调请求"""
    event_type: str
    data: Dict[str, Any]
    timestamp: int


# ==================== 认证依赖 ====================
async def verify_tcadp_signature(request: Request) -> bool:
    """
    FastAPI 依赖：验证 TCADP 请求签名

    用法：
    @router.post("/your-endpoint", dependencies=[Depends(verify_tcadp_signature)])
    """
    adapter = get_tcadp_adapter()

    method = request.method
    path = request.url.path

    # 获取请求头
    headers = {k.lower(): v for k, v in request.headers.items()}

    # 获取请求体
    body = await request.body()
    body_str = body.decode("utf-8")

    if not adapter.verify_request_signature(method, path, headers, body_str):
        logger.warning(f"TCADP 签名验证失败: {method} {path}")
        raise HTTPException(status_code=401, detail="TCADP 签名验证失败")

    return True


# ==================== API 接口 ====================
@router.get("/v1/capabilities", summary="获取 TCADP 可用能力列表")
async def list_tcadp_capabilities():
    """
    获取 TCADP 平台可用的所有能力列表

    Returns:
        能力列表及插件文件位置
    """
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
    """
    接收 TCADP 平台的 Webhook 回调通知

    Args:
        request: FastAPI 请求对象
        callback_data: 回调数据

    Returns:
        响应
    """
    logger.info(f"收到 TCADP Webhook 回调: event_type={callback_data.event_type}")

    try:
        # 验证 Webhook 签名
        auth = get_tcadp_auth()
        headers = {k.lower(): v for k, v in request.headers.items()}

        body = await request.body()
        body_str = body.decode("utf-8")

        if not auth.verify_webhook_signature(headers, body_str):
            logger.warning("Webhook 签名验证失败")
            raise HTTPException(status_code=401, detail="签名验证失败")

        # TODO: 根据不同的 event_type 执行不同的业务逻辑
        # 例如: interview_completed, interview_failed, etc.

        logger.info(f"Webhook 回调处理成功: {callback_data.event_type}")

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
        logger.exception(f"Webhook 回调处理异常: {e}")
        return {
            "code": 500,
            "message": f"处理失败: {str(e)}",
            "data": None,
        }
