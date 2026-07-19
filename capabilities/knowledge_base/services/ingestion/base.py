#!/usr/bin/python3


from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass
class RemoteFile:
    external_id: str
    name: str
    size: Optional[int] = None
    modified_at: Optional[datetime] = None
    uri: Optional[str] = None


@runtime_checkable
class IngestionAdapter(Protocol):
    async def test_connection(self, cfg: dict[str, Any]) -> dict: ...
    async def list_remote_files(
        self, cfg: dict[str, Any], since: Optional[datetime] = None,
    ) -> list[RemoteFile]: ...
    async def fetch_bytes(self, cfg: dict[str, Any], rf: RemoteFile) -> tuple[bytes, str]: ...


__all__ = ["RemoteFile", "IngestionAdapter"]
