#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""ASR speech-to-text adapter

Integrates with speech recognition service, provides audio-to-text capability.
"""

from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("atomic.audio.asr")


class ASRCapability(AtomicCapability):
    """ASR speech-to-text capability adapter"""

    def _build_metadata(self) -> CapabilityMetadata:
        """Build capabilityMetadata"""
        return CapabilityMetadata(
            capability_id="audio.asr",
            capability_name="ASR Speech to text",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="Automatic speech recognition technology, converts audio to text",
            tags=["audio", "asr"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        """Validate input parameters"""
        if not request.payload:
            raise InvalidParameterError(message="ASR Request payload cannot be empty")

        action = request.payload.get("action", "transcribe")

        if action == "transcribe":
            if "audio_url" not in request.payload and "audio_data" not in request.payload:
                raise InvalidParameterError(message="transcribe mode must provide audio_url or audio_data")
        elif action == "transcribe_file":
            if "file_path" not in request.payload:
                raise InvalidParameterError(message="transcribe_file mode must provide file_path")
        else:
            raise InvalidParameterError(message=f"Unsupported action: {action}")

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """Execute ASR capability invocation"""
        await self.validate_input(request)

        action = request.payload.get("action", "transcribe")

        try:
            if action == "transcribe":
                audio_url = request.payload.get("audio_url") or request.payload.get("audio_data")
                result = await self.transcribe(audio_url)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"text": result},
                    message="Speech to text success",
                )
            elif action == "transcribe_file":
                file_path = request.payload["file_path"]
                result = await self.transcribe_file(file_path)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"text": result},
                    message="Audio file speech to text success",
                )
        except Exception as e:
            logger.error(f"ASR Invocation failed: {e}")
            raise CapabilityInvokeError(
                message=f"ASR Invocation failed: {str(e)}",
                details={"action": action},
                cause=e,
            )

    async def transcribe(self, audio_url: str) -> str:
        """
        Speech to text (via URL)

        Note: Currently a mock implementation. In actual deployment, integrate with a real ASR service.
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Transcribing audio: {audio_url}")
            return f"[Mock ASR] This is the transcription result of audio {audio_url}. Audio content: The speaker stated that this project is progressing smoothly with good team collaboration."

        # TODO: Connect to a real ASR service (Alibaba Cloud speech service, Baidu speech, etc.)
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         config.ASR_API_URL,
        #         json={"audio_url": audio_url},
        #         headers={"Authorization": f"Bearer {config.ASR_API_KEY}"},
        #     )
        #     return response.json()["result"]

        raise CapabilityInvokeError(message="ASR Service not configured")

    async def transcribe_file(self, file_path: str) -> str:
        """
        Speech to text (via local file)

        Note: Currently a mock implementation. In actual deployment, integrate with a real ASR service.
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Transcribing local audio file: {file_path}")
            return f"[Mock ASR] This is the transcription result of local file {file_path}. Content summary: project progress report, including requirements analysis, technology selection, development plan, etc."

        # TODO: Connect to a real ASR service
        raise CapabilityInvokeError(message="ASR Service not configured")
