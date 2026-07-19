"""Built-in ASR backends — imported to trigger @register_asr_backend."""

from raganything.asr.backends.whisper import WhisperAsrBackend  # noqa: F401
from raganything.asr.backends.openai_compatible import OpenAICompatibleAsrBackend  # noqa: F401
# LegacyFunctionBackend is intentionally NOT imported here — it's not registered.
