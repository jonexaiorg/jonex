"""Legacy function adapter for ASR backend system."""

from typing import Any, Callable, Mapping

from raganything.asr import AsrBackend, AsrResult, AsrTranscriptionError


class LegacyFunctionBackend(AsrBackend):
    """包装手动传入的 asr_model_func，适配 backend 接口。

    不注册到全局注册表，由 RAGAnything 在检测到手动 asr_model_func 时直接构造。
    必须将旧格式输出 normalize 到 AsrResult。
    """

    binding = "__legacy__"

    def __init__(self, config, func: Callable):
        super().__init__(config)
        self._func = func
        self.model_name = getattr(func, "asr_model", "unknown")

    @property
    def identity(self) -> str:
        ident = getattr(self._func, "asr_identity", None)
        return ident or f"legacy:{self.model_name}"

    def transcribe(self, audio_path: str) -> AsrResult:
        self._acquire_op()
        try:
            self._ensure_warmup()
            raw = self._func(audio_path)
            return self._normalize(raw)
        finally:
            self._release_op()

    def _normalize(self, raw: Any) -> AsrResult:
        """将任意旧格式输出标准化为 AsrResult。防御性处理非 dict 输入。"""
        if not isinstance(raw, Mapping):
            raise AsrTranscriptionError(
                f"Legacy asr_model_func returned {type(raw).__name__} "
                f"(expected dict-like): {str(raw)[:200]}"
            )
        segments = raw.get("segments", []) or []
        return {
            "transcript": (raw.get("transcript") or "").strip(),
            "segments": [
                {
                    "start": s.get("start", 0.0),
                    "end": s.get("end", 0.0),
                    "text": (s.get("text") or "").strip(),
                    "confidence": s.get("confidence"),
                    "speaker_label": s.get("speaker_label"),
                }
                for s in segments
            ],
            "language": raw.get("language", "unknown"),
            "duration": raw.get("duration", segments[-1]["end"] if segments else 0),
            "metadata": {"provider": {"raw_keys": list(raw.keys())}},
        }
