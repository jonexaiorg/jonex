#!/usr/bin/python3


from __future__ import annotations

import base64
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from jonex_core.common.crypto import decrypt_secret

from .base import RemoteFile

logger = logging.getLogger(__name__)


class ApiIngestionAdapter:


    def _headers(self, cfg: dict[str, Any]) -> dict:
        auth = cfg.get("auth") or {}
        atype = (auth.get("type") or "none").lower()
        headers: dict[str, str] = {}
        token_ref = auth.get("token_ref", "")
        if atype == "bearer":
            headers["Authorization"] = f"Bearer {decrypt_secret(token_ref)}"
        elif atype == "api_key":
            headers[auth.get("header_name") or "X-API-Key"] = decrypt_secret(token_ref)
        elif atype == "basic":
            raw = decrypt_secret(token_ref)
            headers["Authorization"] = "Basic " + base64.b64encode(raw.encode()).decode()
        return headers

    async def test_connection(self, cfg: dict[str, Any]) -> dict:
        try:
            files = await self.list_remote_files(cfg)
            return {"ok": True, "message": "连接成功", "sample_count": len(files)}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    async def list_remote_files(
        self, cfg: dict[str, Any], since: Optional[datetime] = None,
    ) -> list[RemoteFile]:
        endpoint = cfg["endpoint"]
        method = (cfg.get("method") or "GET").upper()
        list_path = cfg.get("list_path", "$.data.items")
        name_field = cfg.get("file_name_field", "name")
        url_field = cfg.get("file_url_field", "url")
        id_field = cfg.get("file_id_field", url_field)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.request(method, endpoint, headers=self._headers(cfg))
            resp.raise_for_status()
            body = resp.json()
        from jsonpath_ng import parse as jsonpath_parse

        matches = jsonpath_parse(list_path).find(body)
        items = matches[0].value if matches else []
        out: list[RemoteFile] = []
        for it in items or []:
            if not isinstance(it, dict):
                continue
            uri = it.get(url_field)
            if not uri:
                continue
            out.append(
                RemoteFile(
                    external_id=str(it.get(id_field) or uri),
                    name=str(it.get(name_field) or str(uri).rsplit("/", 1)[-1]),
                    uri=str(uri),
                )
            )
        return out

    async def fetch_bytes(self, cfg: dict[str, Any], rf: RemoteFile) -> tuple[bytes, str]:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(rf.uri, headers=self._headers(cfg))
            resp.raise_for_status()
            mime = resp.headers.get("content-type", "application/octet-stream").split(";")[0].strip()
            return resp.content, mime


__all__ = ["ApiIngestionAdapter"]
