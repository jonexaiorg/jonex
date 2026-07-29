# -*- coding:utf-8 -*-
"""
计量上下文：从 X-Jonex-* 请求头解析调用方上下文。

两个 ID 的职责拆分（方案 A）：
- trace_id（链路追踪 ID）：一次用户业务请求一个，全链路透传不变，
  用于把该请求下的多次 LLM 调用归组统计。来源 X-Jonex-Trace-Id，
  兼容回落到 X-Request-ID。
- request_id（计量幂等键）：每次逻辑 LLM 调用一个、重试稳定，写入
  metering.llm_usage_log 的 UNIQUE 列去重。调用方可显式透传
  X-Jonex-Request-Id；缺失时由网关按 trace_id + 请求体哈希确定性派生
  （见 derive_request_id），保证重试稳定、不同调用不冲突。
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Optional

from fastapi import Request


@dataclass
class MeteringContext:
    """调用方计量上下文，由 X-Jonex-* 头携带"""
    tenant_id: str = "unknown"
    user_id: Optional[str] = None
    scene: str = "unknown"
    kb_id: Optional[str] = None
    doc_id: Optional[str] = None
    trace_id: Optional[str] = None
    request_id: Optional[str] = None


def parse_ctx(request: Request) -> MeteringContext:
    """FastAPI 依赖：从请求头解析 MeteringContext

    request_id 此处可能为 None（调用方未透传）；真正的幂等键在 router 拿到
    请求体后通过 derive_request_id 补齐，避免空字符串撞 UNIQUE 约束被丢弃。
    """
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
    """确定性派生计量幂等键。

    解析顺序：
    1) 调用方显式透传 X-Jonex-Request-Id → 直接采用（调用方自控幂等）；
    2) 否则按 trace_id + 规范化请求体哈希派生：
       - 同一逻辑调用的重试：trace_id 与 body 完全一致 → 哈希一致 → 同一 key → 去重；
       - 不同调用（不同 chunk/不同问题）：body 不同 → key 不同 → 如实记录。

    trace_id 缺失时退化为纯 body 哈希（按内容去重，作用域更宽但仍正确）。
    """
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

    # 前缀带上 trace 便于排查；总长度受 VARCHAR(64) 约束
    prefix = trace[:24] if trace else "auto"
    return f"{prefix}:{digest}"[:64]
