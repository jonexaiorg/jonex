#!/usr/bin/python3


from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Dict, Iterator, Optional


def timing_enabled() -> bool:

    return os.getenv("INGEST_TIMING_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }


class StageTimer:


    def __init__(self, enabled: Optional[bool] = None) -> None:
        self.enabled = timing_enabled() if enabled is None else enabled
        self._t0 = time.perf_counter()
        self.timings: Dict[str, int] = {}

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:

        if not self.enabled:
            yield
            return
        start = time.perf_counter()
        try:
            yield
        finally:
            self.timings[name] = int((time.perf_counter() - start) * 1000)

    def mark_total(self, name: str = "worker_total_ms") -> None:

        if self.enabled:
            self.timings[name] = int((time.perf_counter() - self._t0) * 1000)

    def record(self, name: str, start: float) -> None:

        if self.enabled:
            self.timings[name] = int((time.perf_counter() - start) * 1000)

    def as_dict(self) -> Dict[str, int]:

        return dict(self.timings)


__all__ = ["StageTimer", "timing_enabled"]
