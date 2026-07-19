#!/usr/bin/python3


from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from jonex_core.common.crypto import decrypt_secret

from .base import RemoteFile

logger = logging.getLogger(__name__)


class StorageIngestionAdapter:
    def _client(self, cfg: dict[str, Any]):
        import boto3
        from botocore.config import Config

        cred = decrypt_secret(cfg.get("credential_ref", ""))
        ak, _, sk = cred.partition(":")
        backend = (cfg.get("backend") or "").strip().lower()
        bucket = (cfg.get("bucket") or "").strip()
        endpoint = cfg.get("endpoint") or None


        style = "path" if backend == "minio" else "virtual"





        if style == "virtual" and endpoint and bucket:
            from urllib.parse import urlsplit, urlunsplit

            parts = urlsplit(endpoint)
            if parts.netloc.startswith(f"{bucket}."):
                endpoint = urlunsplit(
                    (parts.scheme, parts.netloc[len(bucket) + 1:], "", "", "")
                )

        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=ak or None,
            aws_secret_access_key=sk or None,
            region_name=cfg.get("region") or None,
            config=Config(s3={"addressing_style": style}),
        )

    async def test_connection(self, cfg: dict[str, Any]) -> dict:
        try:
            files = await self.list_remote_files(cfg)
            return {"ok": True, "message": "连接成功", "sample_count": len(files)}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    async def list_remote_files(
        self, cfg: dict[str, Any], since: Optional[datetime] = None,
    ) -> list[RemoteFile]:
        def _list() -> list[RemoteFile]:
            client = self._client(cfg)
            bucket = cfg["bucket"]
            prefix = cfg.get("prefix", "")
            allow = {e.lower().lstrip(".") for e in (cfg.get("include_ext") or [])}
            out: list[RemoteFile] = []
            token: Optional[str] = None
            while True:
                kw: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
                if token:
                    kw["ContinuationToken"] = token
                resp = client.list_objects_v2(**kw)
                for o in resp.get("Contents", []):
                    key = o["Key"]
                    if key.endswith("/"):
                        continue
                    ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
                    if allow and ext not in allow:
                        continue
                    lm = o.get("LastModified")
                    if since and lm and lm <= since:
                        continue
                    out.append(
                        RemoteFile(
                            external_id=key,
                            name=key.rsplit("/", 1)[-1],
                            size=o.get("Size"),
                            modified_at=lm,
                            uri=key,
                        )
                    )
                if not resp.get("IsTruncated"):
                    break
                token = resp.get("NextContinuationToken")
            return out

        return await asyncio.to_thread(_list)

    async def fetch_bytes(self, cfg: dict[str, Any], rf: RemoteFile) -> tuple[bytes, str]:
        def _get() -> tuple[bytes, str]:
            client = self._client(cfg)
            resp = client.get_object(Bucket=cfg["bucket"], Key=rf.uri)
            return resp["Body"].read(), resp.get("ContentType", "application/octet-stream")

        return await asyncio.to_thread(_get)


__all__ = ["StorageIngestionAdapter"]
