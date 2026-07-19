"""OpenAI-compatible ASR API backend."""

import os
import hashlib
import time
from urllib.parse import urlparse, urlunparse

from raganything.asr import (
    AsrBackend,
    AsrResult,
    ValidationIssue,
    register_asr_backend,
)


@register_asr_backend()
class OpenAICompatibleAsrBackend(AsrBackend):
    """通用 OpenAI 格式 ASR API。

    兼容所有实现 OpenAI /v1/audio/transcriptions 协议的服务。
    """

    binding = "openai_compatible"

    def __init__(self, config):
        super().__init__(config)
        self.model_name = config.asr_model or "whisper-1"
        self._client = None

    @property
    def identity(self) -> str:
        ep = self._canonical_url(
            self.config.asr_base_url or os.getenv("ASR_BASE_URL") or ""
        )
        ep_hash = hashlib.md5(ep.encode()).hexdigest()[:8]
        return f"openai_compatible:{self.model_name}:{ep_hash}"

    @staticmethod
    def _canonical_url(url: str) -> str:
        parsed = urlparse(url)
        return urlunparse(
            (
                parsed.scheme,
                parsed.hostname.lower() if parsed.hostname else "",
                parsed.path.rstrip("/"),
                "",
                "",
                "",
            )
        )

    @classmethod
    def validate_config(cls, config) -> list[ValidationIssue]:
        issues = []
        if not config.asr_api_key and not os.getenv("ASR_API_KEY"):
            issues.append(
                ValidationIssue(
                    level="error",
                    field="asr_api_key",
                    message="ASR_API_KEY must be set for openai_compatible backend",
                )
            )
        if not config.asr_base_url and not os.getenv("ASR_BASE_URL"):
            issues.append(
                ValidationIssue(
                    level="error",
                    field="asr_base_url",
                    message="ASR_BASE_URL must be set for openai_compatible backend",
                )
            )
        return issues

    def _warmup(self):
        from openai import OpenAI

        self._client = OpenAI(
            api_key=self.config.asr_api_key or os.getenv("ASR_API_KEY"),
            base_url=self.config.asr_base_url or os.getenv("ASR_BASE_URL"),
        )

    def _do_close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def transcribe(self, audio_path: str) -> AsrResult:
        self._acquire_op()
        try:
            self._ensure_warmup()
            self._safe_hook(self.before_transcribe, audio_path)
            t0 = time.monotonic()
            try:
                with open(audio_path, "rb") as f:
                    resp = self._client.audio.transcriptions.create(
                        model=self.model_name,
                        file=f,
                        response_format="verbose_json",
                    )
                segments = list(getattr(resp, "segments", []) or [])
                ret: AsrResult = {
                    "transcript": resp.text.strip(),
                    "segments": [
                        {
                            "start": s.start,
                            "end": s.end,
                            "text": s.text.strip(),
                            "confidence": None,
                        }
                        for s in segments
                    ],
                    "language": getattr(resp, "language", "unknown"),
                    "duration": segments[-1].end if segments else 0,
                    "metadata": {"provider": {"model": self.model_name}},
                }
                self._safe_hook(self.after_transcribe, audio_path, ret, time.monotonic() - t0)
                return ret
            except Exception as e:
                self._safe_hook(self.on_error, audio_path, e)
                raise
        finally:
            self._release_op()
