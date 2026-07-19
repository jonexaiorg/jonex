#!/usr/bin/python3



from __future__ import annotations

import asyncio
import os
from functools import lru_cache

from jonex_core.common import get_logger

logger = get_logger("object_storage.cos")


@lru_cache(maxsize=1)
def _client():

    from qcloud_cos import CosConfig, CosS3Client

    region = os.getenv("COS_REGION")
    secret_id = os.getenv("COS_SECRET_ID")
    secret_key = os.getenv("COS_SECRET_KEY")
    if not region or not secret_id or not secret_key:
        missing = [
            k
            for k, v in [("COS_REGION", region), ("COS_SECRET_ID", secret_id), ("COS_SECRET_KEY", secret_key)]
            if not v
        ]
        raise ValueError(
            f"COS 客户端初始化失败：缺少环境变量 {', '.join(missing)}。\n"
            "设置 OBJECT_STORAGE_BACKEND=cos 时必须配置 COS_REGION、COS_SECRET_ID、COS_SECRET_KEY。"
        )
    cfg = CosConfig(
        Region=region,
        SecretId=secret_id,
        SecretKey=secret_key,
        Token=None,
        Scheme="https",
    )
    return CosS3Client(cfg)


class CosObjectStorage:


    def __init__(self) -> None:
        bucket = os.getenv("COS_BUCKET")
        if not bucket:
            raise ValueError(
                "COS 存储初始化失败：缺少环境变量 COS_BUCKET。\n"
                "设置 OBJECT_STORAGE_BACKEND=cos 时必须配置 COS_BUCKET。"
            )
        self._bucket = bucket
        self._expires = int(os.getenv("COS_PRESIGN_EXPIRES", "900"))

    def check_connectivity(self) -> None:

        try:
            _client().head_bucket(Bucket=self._bucket)
            logger.info("COS connectivity check passed (Bucket: %s)", self._bucket)
        except Exception as e:
            raise RuntimeError(
                f"COS 连通性自检失败（Bucket: {self._bucket}）: {e}\n"
                "请检查 COS_REGION / COS_SECRET_ID / COS_SECRET_KEY / COS_BUCKET 环境变量配置。"
            ) from e

    async def put_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        kw = {"Bucket": self._bucket, "Key": key, "Body": data}
        if content_type:
            kw["ContentType"] = content_type
        await asyncio.to_thread(_client().put_object, **kw)
        return key

    async def put_from_path(self, src_path: str, key: str, *, content_type: str | None = None) -> str:

        extra = {"ContentType": content_type} if content_type else {}
        await asyncio.to_thread(
            _client().upload_file,
            Bucket=self._bucket, Key=key, LocalFilePath=src_path, **extra,
        )
        return key

    async def get_bytes(self, key: str) -> bytes:

        resp = await asyncio.to_thread(
            _client().get_object,
            Bucket=self._bucket, Key=key,
        )
        return resp["Body"].read()

    def fs_path(self, key: str) -> str | None:

        return None

    async def get_to_path(self, key: str, dst_path: str) -> str:
        await asyncio.to_thread(
            _client().download_file,
            Bucket=self._bucket, Key=key, DestFilePath=dst_path,
        )
        return dst_path

    async def presigned_url(self, key: str, tenant_id: str, *, expires: int | None = None) -> str:

        return _client().get_presigned_url(
            Method="GET",
            Bucket=self._bucket,
            Key=key,
            Expired=expires or self._expires,
            Params={"response-content-disposition": "inline"},
        )

    async def presigned_put_url(self, key: str, *, expires: int = 300) -> str:

        return _client().get_presigned_url(
            Method="PUT",
            Bucket=self._bucket,
            Key=key,
            Expired=expires,
        )

    async def head_object(self, key: str) -> bool:

        try:
            await asyncio.to_thread(
                _client().head_object,
                Bucket=self._bucket, Key=key,
            )
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        await asyncio.to_thread(
            _client().delete_object,
            Bucket=self._bucket, Key=key,
        )
        return True


__all__ = ["CosObjectStorage"]
