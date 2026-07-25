"""EventBus — lightweight publish/subscribe for pipeline side effects.

DocStatus, metrics, audit, and other side effects register as listeners
rather than occupying pipeline stages. This keeps the core pipeline
focused on document processing.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from raganything.base import DocStatus


@dataclass
class PipelineEvent:
    """An event emitted during document processing."""
    type: str
    doc_id: str
    file_path: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Synchronous publish/subscribe bus (subscribers are called in registration order)."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, listener: Callable) -> None:
        self._listeners[event_type].append(listener)

    async def publish(self, event: PipelineEvent) -> None:
        for listener in self._listeners.get(event.type, []):
            try:
                await listener(event)
            except Exception:
                pass  # listener failure must not break pipeline


class DocStatusListener:
    """Updates doc_status in response to pipeline events."""

    def __init__(self, doc_status_mgr):
        self._mgr = doc_status_mgr

    async def on_document_parsed(self, event: PipelineEvent):
        await self._mgr.upsert(event.doc_id, event.file_path,
                               status=DocStatus.HANDLING, error_msg="")

    async def on_text_inserted(self, event: PipelineEvent):
        await self._mgr.upsert(event.doc_id, event.file_path,
                               status=DocStatus.HANDLING, error_msg="")

    async def on_multimodal_complete(self, event: PipelineEvent):
        updates: Dict[str, Any] = {"status": DocStatus.PROCESSED}

        # Merge chunk_ids into doc_status chunks_list if provided
        chunk_ids = event.data.get("chunk_ids", [])
        if chunk_ids and self._mgr._lightrag is not None:
            try:
                current = await self._mgr._lightrag.doc_status.get_by_id(event.doc_id)
                existing_list = current.get("chunks_list", []) if current else []
                existing_count = current.get("chunks_count", 0) if current else 0
                updates["chunks_list"] = existing_list + chunk_ids
                updates["chunks_count"] = existing_count + len(chunk_ids)
            except Exception:
                pass  # best-effort; status update proceeds regardless

        await self._mgr.upsert(event.doc_id, event.file_path, **updates)

    async def on_document_failed(self, event: PipelineEvent):
        await self._mgr.upsert(event.doc_id, event.file_path,
                               status=DocStatus.FAILED,
                               error_msg=event.data.get("error", ""))

    def register(self, event_bus: EventBus) -> None:
        event_bus.subscribe("document_parsed", self.on_document_parsed)
        event_bus.subscribe("text_inserted", self.on_text_inserted)
        event_bus.subscribe("multimodal_complete", self.on_multimodal_complete)
        event_bus.subscribe("document_failed", self.on_document_failed)
