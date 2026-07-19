#!/usr/bin/python3



from __future__ import annotations

import os
import re
from typing import Any





_WORKSPACE_SAFE_RE = re.compile(r"[^A-Za-z0-9_]")


def _safe_ws_segment(value: str) -> str:
    return _WORKSPACE_SAFE_RE.sub("_", (value or "").strip())


def lightrag_workspace(tenant_id: str, knowledge_base_id: str) -> str:

    t = _safe_ws_segment(tenant_id)
    k = _safe_ws_segment(knowledge_base_id)
    return f"{t}__{k}" if k else t


def build_file_source(
    task: dict[str, Any],
    idx: int,
    *,
    loc: dict[str, Any] | None = None,
) -> str:

    parts: list[str] = [
        f"kb={task.get('knowledge_base_id', '')}",
        f"doc={task.get('document_id') or ''}",
        f"tenant={task.get('tenant_id', '')}",
        f"file={task.get('file_path', '')}",
        f"chunk={idx}",
    ]
    loc = loc or {}
    if loc.get("char_start") is not None:
        parts.append(f"cstart={loc['char_start']}")
        parts.append(f"cend={loc['char_end']}")
    if loc.get("page_no") is not None:
        parts.append(f"page={loc['page_no']}")
    if loc.get("time_start") is not None:
        parts.append(f"tstart={loc['time_start']:.3f}")
        parts.append(f"tend={loc['time_end']:.3f}")
    parts.append(f"trace={task.get('trace_id') or task.get('task_id', '')}")
    return "|".join(parts)


def parse_file_source(raw: str) -> dict[str, Any]:

    if not raw:
        return {}
    if "|" not in raw or "=" not in raw:
        return {"file_path": raw, "storage_key": raw}

    kv: dict[str, str] = {}
    for seg in raw.split("|"):
        if "=" in seg:
            k, _, v = seg.partition("=")
            kv[k.strip()] = v.strip()

    def _num(v: str | None, cast: type) -> int | float | None:
        if v is None:
            return None
        try:
            return cast(v)
        except (TypeError, ValueError):
            return None

    file_seg = kv.get("file")
    return {
        "kb_id": kv.get("kb"),
        "doc_id": kv.get("doc") or None,
        "storage_key": file_seg,
        "file_path": file_seg,
        "chunk_index": _num(kv.get("chunk"), int),
        "char_start": _num(kv.get("cstart"), int),
        "char_end": _num(kv.get("cend"), int),
        "page_no": _num(kv.get("page"), int),
        "time_start": _num(kv.get("tstart"), float),
        "time_end": _num(kv.get("tend"), float),
    }




_MEDIA_BY_EXT: dict[str, set[str]] = {
    "text": {".txt", ".md", ".markdown"},
    "pdf": {".pdf"},
    "audio": {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma"},
    "video": {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"},
    "image": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"},
}


def classify_media(mime_type: str | None, file_name: str | None) -> str:

    mt = (mime_type or "").lower()
    if mt.startswith("audio/"):
        return "audio"
    if mt.startswith("video/"):
        return "video"
    if mt.startswith("image/"):
        return "image"
    if mt == "application/pdf":
        return "pdf"
    if mt.startswith("text/"):
        return "text"
    ext = os.path.splitext(file_name or "")[1].lower()
    for media, exts in _MEDIA_BY_EXT.items():
        if ext in exts:
            return media
    return "other"


def to_location(r: dict[str, Any]) -> dict[str, Any]:

    text = r.get("text")
    if r.get("time_start") is not None:
        return {
            "type": "timestamp",
            "time_start": r["time_start"],
            "time_end": r.get("time_end"),
            "chunk_index": r.get("chunk_index"),
            "text": text,
        }
    if r.get("page_no") is not None:
        return {
            "type": "page",
            "page_no": r["page_no"],
            "chunk_index": r.get("chunk_index"),
            "text": text,
        }
    if r.get("char_start") is not None:
        return {
            "type": "char",
            "char_start": r["char_start"],
            "char_end": r.get("char_end"),
            "chunk_index": r.get("chunk_index"),
            "text": text,
        }
    return {"type": "chunk", "chunk_index": r.get("chunk_index"), "text": text}


__all__ = [
    "build_file_source",
    "classify_media",
    "parse_file_source",
    "to_location",
]
