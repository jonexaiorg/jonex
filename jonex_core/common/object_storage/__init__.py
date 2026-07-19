#!/usr/bin/python3



from __future__ import annotations

import os
import re
from functools import lru_cache

from jonex_core.common import get_logger

logger = get_logger("object_storage")


def build_object_key(
    tenant_id: str,
    knowledge_base_id: str,
    doc_id: str,
    file_name: str | None,
) -> str:

    prefix = os.getenv("COS_KEY_PREFIX", "jonex").strip("/")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", file_name or "unnamed")
    return f"{prefix}/kb/{tenant_id}/{knowledge_base_id}/{doc_id}/{doc_id}_{safe}"



@lru_cache(maxsize=1)
def get_object_storage():

    backend = os.getenv("OBJECT_STORAGE_BACKEND", "local").strip().lower()

    if backend == "cos":
        from jonex_core.common.object_storage.cos_storage import CosObjectStorage

        instance = CosObjectStorage()
        instance.check_connectivity()
        logger.info("Object storage backend: COS (Tencent Cloud)")
    else:
        from jonex_core.common.object_storage.local_storage import LocalObjectStorage

        instance = LocalObjectStorage()
        logger.info("Object storage backend: local (development fallback)")

    return instance


@lru_cache(maxsize=4)
def get_object_storage_for(backend: str | None):

    name = (backend or "local").strip().lower()
    if name == "cos":
        from jonex_core.common.object_storage.cos_storage import CosObjectStorage

        return CosObjectStorage()
    from jonex_core.common.object_storage.local_storage import LocalObjectStorage

    return LocalObjectStorage()


__all__ = ["get_object_storage", "get_object_storage_for", "build_object_key"]
