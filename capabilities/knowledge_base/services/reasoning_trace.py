
import time
from typing import Any, Optional


class ReasoningCollector:


    def __init__(self, enabled: bool):
        self.enabled = enabled
        self._steps: list[dict] = []
        self._t0 = time.perf_counter()

    def step(
        self,
        stage: str,
        title: str,
        *,
        status: str = "done",
        summary: Optional[str] = None,
        detail: Optional[dict[str, Any]] = None,
        t_start: Optional[float] = None,
    ) -> None:
        if not self.enabled:
            return
        now = time.perf_counter()
        self._steps.append({
            "stage": stage,
            "title": title,
            "status": status,
            "summary": summary,
            "detail": detail,
            "duration_ms": int((now - t_start) * 1000) if t_start is not None else None,
        })

    def build(self, final_source: str) -> Optional[dict]:
        if not self.enabled:
            return None
        return {
            "steps": self._steps,
            "final_source": final_source,
            "total_ms": int((time.perf_counter() - self._t0) * 1000),
        }


__all__ = ["ReasoningCollector"]
