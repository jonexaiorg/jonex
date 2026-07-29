#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""对象存储工厂。

按 OBJECT_STORAGE_BACKEND 环境变量返回对应的存储后端：
- "cos" → CosObjectStorage
- "local" → LocalObjectStorage（默认，开发回退）
"""

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
    """统一的知识库文档对象存储 key 方案（local / cos / 其他对象存储通用）。

    形如：``{COS_KEY_PREFIX}/kb/{tenant}/{kb}/{doc}/{doc}_{safe_name}``

    - local 后端：物理文件落在 ``KB_INPUT_DIR/{key}``；
    - 对象存储后端（cos 等）：作为对象 Key 上传。

    key 与后端无关，是文档在平台对象存储中的规范标识。
    """
    prefix = os.getenv("COS_KEY_PREFIX", "jonex").strip("/")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", file_name or "unnamed")
    return f"{prefix}/kb/{tenant_id}/{knowledge_base_id}/{doc_id}/{doc_id}_{safe}"



@lru_cache(maxsize=1)
def get_object_storage():
    """获取对象存储实例（单例，lru_cache 保证进程内复用）。

    按环境变量 OBJECT_STORAGE_BACKEND 返回；用于**新上传**等以平台当前后端为准的场景。
    读取既有文档原文请改用 get_object_storage_for(doc.storage_backend)，按文档自身后端选择。

    启动时做一次连通性自检（仅 COS 后端），凭证错误尽早暴露。
    """
    backend = os.getenv("OBJECT_STORAGE_BACKEND", "local").strip().lower()

    if backend == "cos":
        from jonex_core.common.object_storage.cos_storage import CosObjectStorage

        instance = CosObjectStorage()
        instance.check_connectivity()  # 启动自检，凭证错误尽早暴露
        logger.info("对象存储后端: COS (腾讯云)")
    else:
        from jonex_core.common.object_storage.local_storage import LocalObjectStorage

        instance = LocalObjectStorage()
        logger.info("对象存储后端: local (开发回退)")

    return instance


@lru_cache(maxsize=4)
def get_object_storage_for(backend: str | None):
    """按**指定后端**返回对象存储实例（按 doc.storage_backend 选择，与全局 env 无关）。

    用于读取既有文档：混合数据（部分 local、部分 cos）时必须按每条文档自己的
    后端取对象，否则会出现「local 文档去 COS 读」之类的错配。
    """
    name = (backend or "local").strip().lower()
    if name == "cos":
        from jonex_core.common.object_storage.cos_storage import CosObjectStorage

        return CosObjectStorage()
    from jonex_core.common.object_storage.local_storage import LocalObjectStorage

    return LocalObjectStorage()


__all__ = ["get_object_storage", "get_object_storage_for", "build_object_key"]
