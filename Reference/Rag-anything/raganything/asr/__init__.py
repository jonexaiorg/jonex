"""
ASR Backend System — Multi-Platform Provider Architecture.

Provides a pluggable provider subsystem for audio transcription with
config-driven backend selection, thread-safe lazy initialization,
and complete backward compatibility.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    TypedDict,
)


# ── Type Definitions ──────────────────────────────────────────────────────────


class AsrSegment(TypedDict, total=False):
    """A single segment of an ASR transcription result.

    All fields are optional (``total=False``) so that partial results
    can be represented without missing-data placeholders.
    """

    start: float
    """Start time of the segment in seconds."""
    end: float
    """End time of the segment in seconds."""
    text: str
    """Transcribed text for this segment."""
    confidence: Optional[float]
    """Confidence score (0.0–1.0). ``None`` when unavailable."""
    speaker_label: Optional[str]
    """Speaker label, present only when diarization is enabled."""


class AsrResult(TypedDict):
    """Complete ASR transcription result for a single audio file."""

    transcript: str
    """Full concatenated transcription text."""
    segments: List[AsrSegment]
    """Ordered list of transcription segments."""
    language: str
    """Detected language code (e.g. ``"en"``, ``"zh"``)."""
    duration: float
    """Total audio duration in seconds."""
    metadata: Dict[str, Any]
    """Provider-specific metadata (e.g. model name, processing time)."""


# ── Enums ─────────────────────────────────────────────────────────────────────


class AsrCapability(str, Enum):
    """Capabilities that an ASR backend may advertise."""

    ASYNC = "async"
    """Native asynchronous transcription without thread-pool wrapping."""
    STREAMING = "streaming"
    """Streaming / partial-results transcription."""
    DIARIZATION = "diarization"
    """Speaker diarization (who-spoke-when)."""
    WORD_TIMESTAMPS = "word_timestamps"
    """Per-word timestamp alignment."""


# ── Exception Hierarchy ───────────────────────────────────────────────────────


class AsrBackendError(Exception):
    """Base exception for all ASR backend errors."""


class AsrAuthError(AsrBackendError):
    """Authentication or credential error from the ASR provider."""


class AsrRateLimitError(AsrBackendError):
    """Rate limit exceeded on the ASR provider."""


class AsrTranscriptionError(AsrBackendError):
    """Transcription failed due to an ASR provider error."""


class AsrTimeoutError(AsrBackendError, TimeoutError):
    """Transcription request timed out."""


# ── Validation ────────────────────────────────────────────────────────────────


class ValidationIssue(TypedDict):
    """A single issue found during backend configuration validation."""

    level: Literal["error", "warning"]
    """Severity: ``"error"`` prevents use; ``"warning"`` is advisory."""
    field: str
    """Name of the configuration field with the issue."""
    message: str
    """Human-readable description of the issue."""


# ── Backend Registry ──────────────────────────────────────────────────────────


_ASR_BACKENDS: Dict[str, Type["AsrBackend"]] = {}
"""Registry mapping backend binding names to their classes."""


def register_asr_backend(override: bool = False):
    """Decorator that registers an :class:`AsrBackend` subclass by its ``binding``.

    Example usage::

        @register_asr_backend()
        class WhisperBackend(AsrBackend):
            binding = "whisper"
            ...

    Args:
        override:
            When ``False`` (default), raises :class:`ValueError` if a backend
            with the same binding is already registered.  Pass ``True`` to
            silently replace an existing registration.

    Returns:
        A decorator that registers the class and returns it unchanged.

    Raises:
        ValueError:
            If the class's ``binding`` attribute is empty, or if
            ``override=False`` and the binding is already registered.
    """

    def decorator(cls: Type["AsrBackend"]) -> Type["AsrBackend"]:
        binding = cls.binding
        if not binding:
            raise ValueError(
                f"ASR backend class {cls.__name__} must have a non-empty "
                f"'binding' attribute"
            )
        if not override and binding in _ASR_BACKENDS:
            raise ValueError(
                f"ASR backend '{binding}' is already registered. "
                f"Use register_asr_backend(override=True) to replace it."
            )
        _ASR_BACKENDS[binding] = cls
        return cls

    return decorator


def get_asr_backend(binding: str) -> Type["AsrBackend"]:
    """Look up a registered ASR backend class by its binding name.

    Args:
        binding: The binding name of the backend (e.g. ``"whisper"``).

    Returns:
        The registered backend class.

    Raises:
        ValueError: If no backend is registered under *binding*.
    """
    try:
        return _ASR_BACKENDS[binding]
    except KeyError:
        raise ValueError(
            f"ASR backend '{binding}' is not registered. "
            f"Available backends: {list(_ASR_BACKENDS.keys())}"
        ) from None


# ── Base Backend Class ────────────────────────────────────────────────────────


class AsrBackend(ABC):
    """ASR 后端基类。所有 provider 实现此接口。

    生命周期: CREATED -> (warmup) -> READY -> CLOSED
    初始化是轻量的，warmup 在首次 transcribe 时 lazy 执行。

    线程模型:
    - _warmup_lock: 保护 warmup 互斥
    - _guard_cv (Condition) + _active_ops + _closed: 保护 in-flight 与 close 同步
    """

    binding: str = ""
    """Unique binding name for this backend. Every subclass **must** override."""

    def __init__(self, config: "RAGAnythingConfig"):
        self.config = config
        self._warmup_done = False
        self._warmup_lock = threading.Lock()
        self._guard_cv = threading.Condition()
        self._active_ops = 0
        self._closed = False

    # -- in-flight protection -------------------------------------------------

    def _acquire_op(self) -> None:
        """Mark the start of an in-flight operation.

        Raises:
            RuntimeError: If the backend has already been closed.
        """
        with self._guard_cv:
            if self._closed:
                raise RuntimeError(
                    f"ASR backend '{self.binding}' has been closed"
                )
            self._active_ops += 1

    def _release_op(self) -> None:
        """Mark the end of an in-flight operation.

        When the count drops to zero, all threads waiting in :meth:`close`
        are notified.
        """
        with self._guard_cv:
            self._active_ops -= 1
            if self._active_ops == 0:
                self._guard_cv.notify_all()

    # -- warmup (lazy, thread-safe, with rollback) ----------------------------

    def _ensure_warmup(self) -> None:
        """Run lazy warmup if it has not already completed.

        Thread-safe through a double-checked locking pattern:
        1. Fast-path check of ``_warmup_done`` (lock-free).
        2. Guard check under ``_guard_cv`` for closed state.
        3. Full warmup under the exclusive ``_warmup_lock``.

        On warmup failure the backend is closed and ``_warmup_done`` is
        reset so that a future call will attempt warmup again.
        """
        if self._warmup_done:
            return
        with self._guard_cv:
            if self._closed:
                raise RuntimeError(
                    f"ASR backend '{self.binding}' has been closed"
                )
        with self._warmup_lock:
            if self._warmup_done:
                return
            try:
                self._warmup()
                self._warmup_done = True
            except Exception:
                self._do_close()
                self._warmup_done = False
                raise

    def _warmup(self) -> None:
        """Subclass hook: perform deferred initialisation.

        Called once on the first ``transcribe`` or ``atranscribe`` call.
        Implementations should load models, open connections, authenticate,
        or perform any one-time setup here.
        """

    # -- identity -------------------------------------------------------------

    @property
    @abstractmethod
    def identity(self) -> str:
        """A stable identifier for this backend instance.

        Used for cache-key derivation.  Should include the backend binding
        and any configuration that affects transcription output (e.g.
        model name, language hint).
        """

    @property
    def capabilities(self) -> set[AsrCapability]:
        """Capabilities supported by this backend.

        Override in subclasses to advertise support.
        """
        return set()

    # -- config validation ----------------------------------------------------

    @classmethod
    def validate_config(cls, config: "RAGAnythingConfig") -> list[ValidationIssue]:
        """Validate *config* against this backend's requirements.

        Args:
            config: A :class:`~raganything.config.RAGAnythingConfig` instance.

        Returns:
            A list of issues.  An empty list means the config is valid.
        """
        return []

    # -- transcription --------------------------------------------------------

    def transcribe(self, audio_path: str) -> AsrResult:
        """Transcribe an audio file synchronously.

        Subclasses may override this or :meth:`atranscribe` (or both).

        Args:
            audio_path: Path to a local audio file.

        Returns:
            An :class:`AsrResult` dict with the full transcription.

        Raises:
            NotImplementedError: If the backend only supports async
                transcription.
        """
        raise NotImplementedError

    async def atranscribe(self, audio_path: str) -> AsrResult:
        """Transcribe an audio file asynchronously.

        Subclasses that natively support async should override this.

        Args:
            audio_path: Path to a local audio file.

        Returns:
            An :class:`AsrResult` dict with the full transcription.

        Raises:
            NotImplementedError: If the backend does not natively support
                async transcription.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support native async transcription"
        )

    # -- observability hooks --------------------------------------------------

    @staticmethod
    def _safe_hook(fn: Callable, *args: Any) -> None:
        """Invoke *fn* with *args*, swallowing any exception."""
        try:
            fn(*args)
        except Exception:
            pass

    def before_transcribe(self, audio_path: str) -> None:
        """Hook invoked immediately before a transcription starts.

        Exceptions are swallowed — they do **not** abort the operation.

        Args:
            audio_path: Path to the audio file about to be transcribed.
        """

    def after_transcribe(
        self, audio_path: str, result: AsrResult, elapsed: float
    ) -> None:
        """Hook invoked after a successful transcription.

        Exceptions are swallowed — they do **not** propagate.

        Args:
            audio_path: Path to the audio file that was transcribed.
            result: The transcription result.
            elapsed: Wall-clock time in seconds for the transcription.
        """

    def on_error(self, audio_path: str, exc: Exception) -> None:
        """Hook invoked when a transcription fails.

        Exceptions are swallowed — they do **not** propagate.

        Args:
            audio_path: Path to the audio file that caused the error.
            exc: The exception that was raised.
        """

    # -- lifecycle ------------------------------------------------------------

    def close(self) -> None:
        """Release all resources held by this backend.

        This method is **idempotent** — calling it multiple times is safe.
        If there are in-flight transcription operations it blocks until
        they complete.

        After ``close()``, the instance **must not** be used for further
        transcriptions.
        """
        with self._guard_cv:
            if self._closed:
                return
            self._closed = True
            while self._active_ops > 0:
                self._guard_cv.wait()
        self._warmup_done = False
        self._do_close()

    def _do_close(self) -> None:
        """Subclass hook: release provider-specific resources.

        **Must be idempotent** — calling multiple times must not raise.
        """

    # -- compatibility shim ---------------------------------------------------

    def create_func(self) -> Callable:
        """Build a callable compatible with the legacy ``asr_model_func`` API.

        The returned wrapper exposes an ``asr_identity`` attribute set to
        :attr:`identity`, which the processor uses for cache-key derivation.

        Example::

            backend = MyBackend(config)
            rag = RAGAnything(asr_model_func=backend.create_func(), ...)
        """
        backend = self

        def wrapper(audio_path: str) -> dict:
            return backend.transcribe(audio_path)

        wrapper.asr_identity = self.identity
        return wrapper
