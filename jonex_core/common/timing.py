#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""分阶段耗时埋点工具。

用于文档摄入链路（解析 → 推 LightRAG → 本体抽取 → 入图库）的性能分析，
采集各阶段耗时（毫秒），输出可聚合的结构化数据。设计见
`docs/ingestion-timing-metrics-design.md`。

约定（见设计文档 §3.2）：
- 耗时单位统一毫秒（int），用单调钟 ``time.perf_counter()`` 计时；
- ``StageTimer`` 受环境变量 ``INGEST_TIMING_ENABLED`` 控制，默认开启，
  关闭时退化为 no-op（不收集、不抛异常）；
- ``stage()`` 是上下文管理器，**不改变原有控制流与异常传播**，阶段内
  抛错时 ``finally`` 仍记录已耗时间，便于定位「失败前卡在哪个阶段」；
- 不支持嵌套 ``stage()``（同名 key 后者覆盖前者，不累加）；
- ``mark_total()`` 多次调用取最后一次；
- ``as_dict()`` 返回内部字典的副本。
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Dict, Iterator, Optional


def timing_enabled() -> bool:
    """摄入耗时埋点总开关。默认开启；显式设为 0/false/no 时关闭。"""
    return os.getenv("INGEST_TIMING_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }


class StageTimer:
    """分阶段耗时收集器（毫秒）。

    计时不抛异常；关闭开关时退化为 no-op。约定构造点须紧贴处理起点，
    使 ``mark_total()`` 反映真实处理时间，不混入空闲等待。
    """

    def __init__(self, enabled: Optional[bool] = None) -> None:
        self.enabled = timing_enabled() if enabled is None else enabled
        self._t0 = time.perf_counter()
        self.timings: Dict[str, int] = {}

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        """计时一个阶段。阶段内异常照常传播，耗时在 ``finally`` 记录。"""
        if not self.enabled:
            yield
            return
        start = time.perf_counter()
        try:
            yield
        finally:
            self.timings[name] = int((time.perf_counter() - start) * 1000)

    def mark_total(self, name: str = "worker_total_ms") -> None:
        """记录从构造到当前的总耗时（多次调用取最后一次）。"""
        if self.enabled:
            self.timings[name] = int((time.perf_counter() - self._t0) * 1000)

    def record(self, name: str, start: float) -> None:
        """记录一个阶段耗时：``start`` 为该阶段开始时的 ``time.perf_counter()``。

        用于深层嵌套代码中避免 ``with`` 块大段重新缩进的场景（如 ingest worker）：
        在阶段前取 ``t = time.perf_counter()``，阶段正常结束后调 ``record(name, t)``。
        注意：若阶段内抛异常未走到 ``record``，该 key 不会被记录（此时可由
        ``worker_total_ms`` + 已记录的前序阶段定位失败位置）。
        """
        if self.enabled:
            self.timings[name] = int((time.perf_counter() - start) * 1000)

    def as_dict(self) -> Dict[str, int]:
        """返回已采集耗时的副本。"""
        return dict(self.timings)


__all__ = ["StageTimer", "timing_enabled"]
