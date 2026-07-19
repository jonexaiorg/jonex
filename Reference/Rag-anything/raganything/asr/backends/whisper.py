"""Whisper local ASR backend."""

import time

from raganything.asr import AsrBackend, AsrResult, register_asr_backend


@register_asr_backend()
class WhisperAsrBackend(AsrBackend):
    """Local openai-whisper ASR. Supports all whisper model sizes."""

    binding = "whisper"

    def __init__(self, config):
        super().__init__(config)
        self.model_name = config.asr_model or "large-v3"
        self._model = None

    @property
    def identity(self) -> str:
        return f"whisper:{self.model_name}"

    def _warmup(self):
        import whisper

        self._model = whisper.load_model(self.model_name)

    def _do_close(self):
        self._model = None

    def transcribe(self, audio_path: str) -> AsrResult:
        self._acquire_op()
        try:
            self._ensure_warmup()
            self._safe_hook(self.before_transcribe, audio_path)
            t0 = time.monotonic()
            try:
                result = self._model.transcribe(audio_path)
                segments = result.get("segments", [])
                ret: AsrResult = {
                    "transcript": result["text"].strip(),
                    "segments": [
                        {
                            "start": s["start"],
                            "end": s["end"],
                            "text": s["text"].strip(),
                            "confidence": None,
                        }
                        for s in segments
                    ],
                    "language": result.get("language", "unknown"),
                    "duration": segments[-1]["end"] if segments else 0,
                    "metadata": {"provider": {"model": self.model_name}},
                }
                self._safe_hook(self.after_transcribe, audio_path, ret, time.monotonic() - t0)
                return ret
            except Exception as e:
                self._safe_hook(self.on_error, audio_path, e)
                raise
        finally:
            self._release_op()
