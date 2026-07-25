"""Document status management for LightRAG KV store."""

import logging
import time
from typing import Any, Dict, Optional

from raganything.base import DocStatus

logger = logging.getLogger(__name__)


def current_doc_status_timestamp() -> str:
    """Return a stable UTC timestamp for doc_status bookkeeping."""
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())


class DocStatusManager:
    """Manage doc_status records in LightRAG KV storage.

    Provides create-or-get and merge semantics on top of
    ``lightrag.doc_status`` so that callers can safely update
    status fields without losing existing data.
    """

    def __init__(self, lightrag: Any, config: Any) -> None:
        self._lightrag = lightrag
        self._config = config

    def _get_file_reference(self, file_path: str) -> str:
        """Return full path or basename depending on config."""
        if getattr(self._config, "use_full_path", False):
            return file_path
        return file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

    async def ensure_record(
        self,
        doc_id: str,
        file_path: str,
        *,
        scheme_name: Optional[str] = None,
        status: DocStatus = DocStatus.READY,
    ) -> Dict[str, Any]:
        """Return existing doc_status or create a minimal one."""
        if self._lightrag is None:
            return {"status": status, "file_path": file_path}
        current = await self._lightrag.doc_status.get_by_id(doc_id)
        if current:
            return current

        timestamp = current_doc_status_timestamp()
        payload: Dict[str, Any] = {
            "status": status,
            "content": "",
            "content_summary": "",
            "content_length": 0,
            "error_msg": "",
            "chunks_count": 0,
            "chunks_list": [],
            "created_at": timestamp,
            "updated_at": timestamp,
            "file_path": self._get_file_reference(file_path),
        }
        if scheme_name is not None:
            payload["scheme_name"] = scheme_name

        await self._lightrag.doc_status.upsert({doc_id: payload})
        await self._lightrag.doc_status.index_done_callback()
        return await self._lightrag.doc_status.get_by_id(doc_id) or payload

    async def upsert(
        self,
        doc_id: str,
        file_path: str,
        *,
        scheme_name: Optional[str] = None,
        **updates: Any,
    ) -> Dict[str, Any]:
        """Merge *updates* into the existing doc_status record."""
        if self._lightrag is None:
            return {"status": updates.get("status", DocStatus.READY), "file_path": file_path}
        current = await self.ensure_record(
            doc_id, file_path, scheme_name=scheme_name,
        )
        updated = {
            **current,
            **updates,
            "updated_at": current_doc_status_timestamp(),
        }
        await self._lightrag.doc_status.upsert({doc_id: updated})
        await self._lightrag.doc_status.index_done_callback()
        return updated
