#!/usr/bin/python3



from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("atomic.audio.asr")


class ASRCapability(AtomicCapability):


    def _build_metadata(self) -> CapabilityMetadata:

        return CapabilityMetadata(
            capability_id="audio.asr",
            capability_name="ASR 语音转文本",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="自动语音识别技术，将音频转换为文本",
            tags=["audio", "asr"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:

        if not request.payload:
            raise InvalidParameterError(message="ASR 请求 payload 不能为空")

        action = request.payload.get("action", "transcribe")

        if action == "transcribe":
            if "audio_url" not in request.payload and "audio_data" not in request.payload:
                raise InvalidParameterError(message="transcribe 模式必须提供 audio_url 或 audio_data")
        elif action == "transcribe_file":
            if "file_path" not in request.payload:
                raise InvalidParameterError(message="transcribe_file 模式必须提供 file_path")
        else:
            raise InvalidParameterError(message=f"不支持的 action: {action}")

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:

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
            logger.error(f"ASR invocation failed: {e}")
            raise CapabilityInvokeError(
                message=f"ASR 调用失败: {str(e)}",
                details={"action": action},
                cause=e,
            )

    async def transcribe(self, audio_url: str) -> str:

        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Transcribing audio: {audio_url}")
            return f"[Mock ASR] 这是音频 {audio_url} 的转写结果。音频内容：项目进展顺利，团队协作良好。"











        raise CapabilityInvokeError(message="ASR 服务未配置")

    async def transcribe_file(self, file_path: str) -> str:

        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Transcribing local audio file: {file_path}")
            return f"[Mock ASR] 这是本地文件 {file_path} 的转写结果。内容摘要：项目进度汇报，包含需求分析、技术选型、开发计划等。"


        raise CapabilityInvokeError(message="ASR 服务未配置")
