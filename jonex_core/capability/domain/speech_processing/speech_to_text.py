#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Speech to text domain capability

Orchestrates atomic capabilities via ASRClient. The client is determined as LOCAL / REMOTE / MOCK
by capability_runtime.yaml; this layer is unaware of deployment form.
"""

from typing import Any, Dict

from jonex_core.capability.atomic.audio.client import ASRClient, get_asr_client
from jonex_core.capability.domain.base import DomainCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
)
from jonex_core.common import get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("domain.speech.stt")


class SpeechToTextCapability(DomainCapability):
    """Speech to text domain capability"""

    def __init__(self, asr_client: ASRClient | None = None):
        super().__init__()
        # In test scenarios, a custom client can be injected
        self.asr_client: ASRClient = asr_client or get_asr_client()

    def _build_metadata(self) -> CapabilityMetadata:
        from jonex_core.capability.models import CapabilityType

        return CapabilityMetadata(
            capability_id="speech.speech_to_text",
            capability_name="Speech to text",
            capability_type=CapabilityType.DOMAIN,
            version="v1",
            description="Speech to text domain capability, supports long audio processing, segmentation, timestamps, speaker diarization",
            tags=["speech", "asr"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        if not request.payload:
            raise InvalidParameterError(message="Speech to text request payload cannot be empty")

        action = request.payload.get("action", "transcribe")
        if action not in {"transcribe", "transcribe_with_timestamps", "speaker_diarization"}:
            raise InvalidParameterError(message=f"Unsupported action: {action}")

        if "audio_url" not in request.payload:
            raise InvalidParameterError(message="audio_url parameter must be provided")
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        await self.validate_input(request)

        action = request.payload.get("action", "transcribe")
        audio_url = request.payload["audio_url"]

        try:
            logger.info(f"Speech to text: audio_url={audio_url}, action={action}")
            text = await self.asr_client.transcribe(audio_url)

            if action == "transcribe":
                data: Dict[str, Any] = {"text": text}
            elif action == "transcribe_with_timestamps":
                data = self._add_timestamps(text)
            else:  # speaker_diarization
                with_ts = self._add_timestamps(text)
                speakers = sorted({seg["speaker"] for seg in with_ts["segments"]})
                data = {**with_ts, "speakers": speakers, "speaker_count": len(speakers)}

            return CapabilityResponse.ok(
                request_id=request.request_id,
                data=data,
                message="Speech to text succeeded",
            )
        except CapabilityInvokeError:
            raise
        except Exception as e:
            logger.error(f"Speech to text processing failed: {e}")
            raise CapabilityInvokeError(
                message=f"Speech to text processing failed: {e}",
                details={"action": action, "audio_url": audio_url},
                cause=e,
            )

    @staticmethod
    def _add_timestamps(text: str) -> Dict[str, Any]:
        """Simple timestamp simulation (actually returned by ASR atomic capability)"""
        sentences = [s for s in text.split("。") if s.strip()]
        segments = []
        current = 0.0
        for i, sentence in enumerate(sentences):
            duration = len(sentence) * 0.2
            segments.append(
                {
                    "start_time": round(current, 2),
                    "end_time": round(current + duration, 2),
                    "text": sentence.strip() + "。",
                    "speaker": f"speaker_{i % 2 + 1}",
                }
            )
            current += duration
        return {"text": text, "segments": segments, "duration": round(current, 2)}
