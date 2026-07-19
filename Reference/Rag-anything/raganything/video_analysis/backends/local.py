"""
Local video analysis backend.

Encapsulates the existing local processing pipeline:
  extract audio → ASR transcribe → keyframes → VLM description
  → time alignment → MapReduce → entity extraction.

Delegates to ``VideoModalProcessor._analyze_via_local()`` to avoid
duplicating the ~130-line processing flow.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, Tuple

from raganything.video_analysis import (
    VideoAnalysisBackend,
    VideoAnalysisResult,
    register_video_analysis_backend,
)

if TYPE_CHECKING:
    from raganything.config import RAGAnythingConfig

logger = logging.getLogger(__name__)

# Callback signature: _analyze_via_local(modal_content, content_type, item_info, entity_name)
# Returns (summary, entity_info)
_LocalAnalyzeFunc = Callable[
    [Dict[str, Any], str, Optional[Dict[str, Any]], Optional[str]],
    Awaitable[Tuple[str, Dict[str, Any]]],
]


@register_video_analysis_backend()
class LocalVideoBackend(VideoAnalysisBackend):
    """Local video analysis backend.

    Relies on a callback (``local_analyze_func``) wired during
    initialisation — typically a bound method from
    :class:`~raganything.video_processor.VideoModalProcessor` that
    runs the full local pipeline and returns ``(summary, entity_info)``.
    """

    binding = "local"

    def __init__(
        self,
        config: "RAGAnythingConfig",
        *,
        local_analyze_func: Optional[_LocalAnalyzeFunc] = None,
    ):
        super().__init__(config)
        self._analyze_func = local_analyze_func

    # ── VideoAnalysisBackend ────────────────────────────────────────

    async def analyze_video(
        self,
        video_path: str,
        prompt: Optional[str] = None,
    ) -> VideoAnalysisResult:
        """Build a modal_content dict and delegate to the local pipeline."""
        if not self._analyze_func:
            raise RuntimeError(
                "LocalVideoBackend is not wired to a VideoModalProcessor. "
                "Pass 'local_analyze_func' during construction or ensure "
                "the processor calls _wire_local_backend()."
            )
        modal_content = {
            "video_path": video_path,
            "file_name": os.path.basename(video_path),
        }
        summary, entity_info = await self._analyze_func(
            modal_content, "video", None, None,
        )
        return VideoAnalysisResult(
            summary=summary,
            analysis_method="local",
            metadata=entity_info,
        )

    def close(self) -> None:
        self._analyze_func = None
