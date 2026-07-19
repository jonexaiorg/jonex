


import hashlib
import json
from dataclasses import dataclass
from typing import Optional

from fastapi import Request


@dataclass
class MeteringContext:

    tenant_id: str = "unknown"
    user_id: Optional[str] = None
    scene: str = "unknown"
    kb_id: Optional[str] = None
    doc_id: Optional[str] = None
    trace_id: Optional[str] = None
    request_id: Optional[str] = None


def parse_ctx(request: Request) -> MeteringContext:

    return MeteringContext(
        tenant_id=request.headers.get("X-Jonex-Tenant-Id", "unknown"),
        user_id=request.headers.get("X-Jonex-User-Id"),
        scene=request.headers.get("X-Jonex-Scene", "unknown"),
        kb_id=request.headers.get("X-Jonex-Kb-Id"),
        doc_id=request.headers.get("X-Jonex-Doc-Id"),
        trace_id=(
            request.headers.get("X-Jonex-Trace-Id")
            or request.headers.get("X-Request-ID")
        ),
        request_id=request.headers.get("X-Jonex-Request-Id"),
    )


def derive_request_id(ctx: MeteringContext, body: dict) -> str:

    explicit = (ctx.request_id or "").strip()
    if explicit:
        return explicit[:64]

    try:
        canonical_body = json.dumps(body, sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        canonical_body = str(body)

    model = (body or {}).get("model", "") if isinstance(body, dict) else ""
    trace = ctx.trace_id or ""
    digest = hashlib.sha1(
        f"{trace}|{ctx.scene}|{model}|{canonical_body}".encode("utf-8")
    ).hexdigest()[:32]


    prefix = trace[:24] if trace else "auto"
    return f"{prefix}:{digest}"[:64]
