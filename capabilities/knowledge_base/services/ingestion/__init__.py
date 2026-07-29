#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""按 access_type 返回 ingestion 适配器。"""
from jonex_core.common.exceptions import InvalidParameterError
from jonex_core.common.i18n import translate

from .api_adapter import ApiIngestionAdapter
from .storage_adapter import StorageIngestionAdapter

_ADAPTERS = {
    "api": ApiIngestionAdapter,
    "storage": StorageIngestionAdapter,
}


def get_ingestion_adapter(access_type: str):
    cls = _ADAPTERS.get(access_type)
    if cls is None:
        raise InvalidParameterError(message=translate("err.ingest.unsupported_access_type", params={"access_type": access_type}, fallback=f"不支持的接入类型: {access_type}")  )  # 原消息)
    return cls()


__all__ = ["get_ingestion_adapter", "ApiIngestionAdapter", "StorageIngestionAdapter"]
