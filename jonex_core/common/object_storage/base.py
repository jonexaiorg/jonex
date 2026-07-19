#!/usr/bin/python3



from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class ObjectStorage(Protocol):


    async def put_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> str:

        ...

    async def get_bytes(self, key: str) -> bytes:

        ...

    async def get_to_path(self, key: str, dst_path: str) -> str:

        ...

    async def presigned_url(self, key: str, tenant_id: str, *, expires: int = 900) -> str:

        ...

    async def delete(self, key: str) -> bool:

        ...


__all__ = ["ObjectStorage"]
