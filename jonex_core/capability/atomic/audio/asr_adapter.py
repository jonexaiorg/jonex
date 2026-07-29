#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""ASR 语音转文本适配器

对接语音识别服务，提供音频转文本能力。
"""

from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError
from jonex_core.common.i18n import translate

logger = get_logger("atomic.audio.asr")


class ASRCapability(AtomicCapability):
    """ASR 语音转文本能力适配器"""

    def _build_metadata(self) -> CapabilityMetadata:
        """构建能力元数据"""
        return CapabilityMetadata(
            capability_id="audio.asr",
            capability_name="ASR 语音转文本",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="自动语音识别技术，将音频转换为文本",
            tags=["audio", "asr"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        """验证输入参数"""
        if not request.payload:
            raise InvalidParameterError(message=translate("err.asr.payload_required", fallback="ASR 请求 payload 不能为空"))

        action = request.payload.get("action", "transcribe")

        if action == "transcribe":
            if "audio_url" not in request.payload and "audio_data" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "transcribe", "param": "audio_url 或 audio_data"}, fallback="transcribe 模式必须提供 audio_url 或 audio_data"))
        elif action == "transcribe_file":
            if "file_path" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "transcribe_file", "param": "file_path"}, fallback="transcribe_file 模式必须提供 file_path"))
        else:
            raise InvalidParameterError(message=translate("err.capability.unsupported_action", params={"action": action}, fallback=f"不支持的 action: {action}"))

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """执行 ASR 能力调用"""
        await self.validate_input(request)

        action = request.payload.get("action", "transcribe")

        try:
            if action == "transcribe":
                audio_url = request.payload.get("audio_url") or request.payload.get("audio_data")
                result = await self.transcribe(audio_url)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"text": result},
                    message="语音转文本成功",
                )
            elif action == "transcribe_file":
                file_path = request.payload["file_path"]
                result = await self.transcribe_file(file_path)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"text": result},
                    message="语音文件转文本成功",
                )
        except Exception as e:
            logger.error(f"ASR 调用失败: {e}")
            raise CapabilityInvokeError(
                message=translate("err.asr.invoke_failed", fallback="ASR 调用失败"),
                details={"action": action},
                cause=e,
            )

    async def transcribe(self, audio_url: str) -> str:
        """
        语音转文本（通过 URL）

        注意：当前为 mock 实现，实际部署时需要接入真实 ASR 服务。
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] 正在转写音频: {audio_url}")
            return f"[Mock ASR] 这是音频 {audio_url} 的转写结果。访谈内容：受访者表示本次项目进展顺利，团队协作良好。"

        # TODO: 接入真实的 ASR 服务（阿里云语音服务、百度语音等）
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         config.ASR_API_URL,
        #         json={"audio_url": audio_url},
        #         headers={"Authorization": f"Bearer {config.ASR_API_KEY}"},
        #     )
        #     return response.json()["result"]

        raise CapabilityInvokeError(message=translate("err.capability.service_not_configured", params={"service_name": "ASR"}, fallback="ASR 服务未配置"))

    async def transcribe_file(self, file_path: str) -> str:
        """
        语音转文本（通过本地文件）

        注意：当前为 mock 实现，实际部署时需要接入真实 ASR 服务。
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] 正在转写本地音频文件: {file_path}")
            return f"[Mock ASR] 这是本地文件 {file_path} 的转写结果。内容摘要：项目进度汇报，包含需求分析、技术选型、开发计划等。"

        # TODO: 接入真实的 ASR 服务
        raise CapabilityInvokeError(message=translate("err.capability.service_not_configured", params={"service_name": "ASR"}, fallback="ASR 服务未配置"))
