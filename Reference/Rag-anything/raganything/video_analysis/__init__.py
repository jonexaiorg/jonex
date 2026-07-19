"""
Video Analysis Backend System — Pluggable Video Understanding Providers.

Provides a config-driven provider subsystem for video analysis with
a pluggable backend registry, allowing runtime selection between
local processing (ASR + keyframes + VLM) and cloud-based analysis
(e.g. Tencent Cloud MPS VideoComprehension).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional, Type


# ── Data Types ──────────────────────────────────────────────────────────


@dataclass
class VideoAnalysisResult:
    """Structured result from a video analysis backend.

    All backends normalise their output into this format so that
    :class:`~raganything.video_processor.VideoModalProcessor` can
    consume them uniformly.
    """

    summary: str
    """Text summary / description of the video content."""

    scenes: Optional[List[Dict[str, Any]]] = None
    """Optional list of scene/shot breakdowns."""

    tags: Optional[List[Dict[str, Any]]] = None
    """Optional list of generated tags / labels."""

    raw_json: str = ""
    """Raw JSON string returned by the provider (empty for local)."""

    analysis_method: str = "local"
    """Identifier of the backend that produced this result."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Provider-specific metadata (model name, processing time, etc.)."""


# ── Validation ──────────────────────────────────────────────────────────


class ValidationIssue:
    """A single issue found during backend configuration validation."""

    def __init__(self, level: str, field: str, message: str):
        self.level = level  # "error" | "warning"
        self.field = field
        self.message = message

    def __repr__(self) -> str:
        return f"[{self.level}] {self.field}: {self.message}"


# ── Backend Registry ────────────────────────────────────────────────────


_VIDEO_ANALYSIS_BACKENDS: Dict[str, Type["VideoAnalysisBackend"]] = {}
"""Registry mapping backend binding names to their classes."""


def register_video_analysis_backend(override: bool = False):
    """Decorator that registers a :class:`VideoAnalysisBackend` subclass.

    Example usage::

        @register_video_analysis_backend()
        class MPSVideoBackend(VideoAnalysisBackend):
            binding = "mps"
            ...

    Args:
        override: When ``False`` (default), raises :class:`ValueError`
            if a backend with the same binding is already registered.
            Pass ``True`` to silently replace an existing registration.

    Returns:
        A decorator that registers the class and returns it unchanged.

    Raises:
        ValueError: If the class's ``binding`` attribute is empty, or if
            ``override=False`` and the binding is already registered.
    """

    def decorator(cls: Type["VideoAnalysisBackend"]) -> Type["VideoAnalysisBackend"]:
        binding = cls.binding
        if not binding:
            raise ValueError(
                f"VideoAnalysisBackend class {cls.__name__} must have a "
                f"non-empty 'binding' attribute"
            )
        if not override and binding in _VIDEO_ANALYSIS_BACKENDS:
            raise ValueError(
                f"Video analysis backend '{binding}' is already registered. "
                f"Use register_video_analysis_backend(override=True) to replace it."
            )
        _VIDEO_ANALYSIS_BACKENDS[binding] = cls
        return cls

    return decorator


def get_video_analysis_backend(binding: str) -> Type["VideoAnalysisBackend"]:
    """Look up a registered video analysis backend class by binding name.

    Args:
        binding: The binding name (e.g. ``"local"``, ``"mps"``).

    Returns:
        The registered backend class.

    Raises:
        ValueError: If no backend is registered under *binding*.
    """
    try:
        return _VIDEO_ANALYSIS_BACKENDS[binding]
    except KeyError:
        raise ValueError(
            f"Video analysis backend '{binding}' is not registered. "
            f"Available backends: {list(_VIDEO_ANALYSIS_BACKENDS.keys())}"
        ) from None


# ── Base Backend Class ──────────────────────────────────────────────────


class VideoAnalysisBackend(ABC):
    """Abstract base class for all video analysis backends.

    Subclasses must set :attr:`binding` and implement :meth:`analyze_video`.
    """

    binding: ClassVar[str] = ""
    """Unique binding name. Every subclass **must** override."""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    async def analyze_video(
        self,
        video_path: str,
        prompt: Optional[str] = None,
    ) -> VideoAnalysisResult:
        """Analyse a video file and return structured results.

        Args:
            video_path: Absolute path (or COS URL) of the video file.
            prompt: Optional provider-specific analysis prompt / instruction.

        Returns:
            A :class:`VideoAnalysisResult` with the analysis output.
        """
        ...

    @classmethod
    def validate_config(cls, config) -> List[ValidationIssue]:
        """Validate *config* against this backend's requirements.

        Returns:
            A list of issues.  An empty list means the config is valid.
        """
        return []

    def close(self) -> None:
        """Release any resources held by this backend.

        Idempotent — safe to call multiple times.
        """
