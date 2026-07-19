#!/usr/bin/python3


from jonex_core.common.exceptions import InvalidParameterError

from .api_adapter import ApiIngestionAdapter
from .storage_adapter import StorageIngestionAdapter

_ADAPTERS = {
    "api": ApiIngestionAdapter,
    "storage": StorageIngestionAdapter,
}


def get_ingestion_adapter(access_type: str):
    cls = _ADAPTERS.get(access_type)
    if cls is None:
        raise InvalidParameterError(message=f"不支持的拉取型接入类型: {access_type}")
    return cls()


__all__ = ["get_ingestion_adapter", "ApiIngestionAdapter", "StorageIngestionAdapter"]
