#!/usr/bin/python3



from __future__ import annotations

import os
import shutil
from pathlib import Path

from jonex_core.common import get_logger

logger = get_logger("object_storage.local")


class LocalObjectStorage:


    def __init__(self) -> None:
        self._base_dir = Path(os.getenv("KB_INPUT_DIR", "/app/inputs"))
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:




        base = self._base_dir.resolve()
        raw = Path(key)
        if raw.is_absolute():
            full = raw.resolve()
        else:
            full = (self._base_dir / raw.as_posix().lstrip("/")).resolve()
        if full != base and not str(full).startswith(str(base) + os.sep):
            raise ValueError(f"路径穿越拒绝: {key}")
        return full

    async def put_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        dst = self._resolve(key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        logger.debug("local_storage: put %s (%d bytes)", key, len(data))
        return key

    async def get_bytes(self, key: str) -> bytes:
        path = self._resolve(key)
        return path.read_bytes()

    def fs_path(self, key: str) -> str:

        return str(self._resolve(key))

    async def get_to_path(self, key: str, dst_path: str) -> str:
        src = self._resolve(key)
        shutil.copy2(str(src), dst_path)
        return dst_path

    async def presigned_url(self, key: str, tenant_id: str, *, expires: int = 900) -> str:

        logger.debug("local_storage: presigned_url not supported (local backend)")
        return ""

    async def delete(self, key: str) -> bool:
        path = self._resolve(key)
        if path.exists():
            path.unlink()
            return True
        return False


__all__ = ["LocalObjectStorage"]
