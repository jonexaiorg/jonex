"""Pipeline processing mode."""
from enum import Enum


class PipelineMode(str, Enum):
    """Determines how multimodal content is handled.

    STANDALONE — Pipeline handles multimodal processing directly.
    LIGHTRAG_INTEGRATED — Pipeline calls LightRAG's insert_text_content_with_multimodal_content.
    """
    STANDALONE = "standalone"
    LIGHTRAG_INTEGRATED = "lightrag"
