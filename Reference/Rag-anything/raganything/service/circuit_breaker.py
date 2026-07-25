"""Simple circuit breaker for external service protection."""

import time


class CircuitBreaker:
    """Circuit breaker with closed → open → half_open state transitions.

    After ``fail_threshold`` consecutive failures, the breaker opens.
    It stays open for ``cooldown_seconds``, then transitions to half_open
    allowing one probe request through. Success resets to closed.
    """

    def __init__(self, fail_threshold: int = 5, cooldown_seconds: float = 30.0):
        self._fail_threshold = fail_threshold
        self._cooldown = cooldown_seconds
        self._fail_count = 0
        self._opened_at: float = 0.0
        self._state = "closed"

    @property
    def state(self) -> str:
        return self._state

    def allow(self) -> bool:
        if self._state == "open":
            if time.monotonic() - self._opened_at >= self._cooldown:
                self._state = "half_open"
                return True
            return False
        return True

    def record_success(self):
        self._fail_count = 0
        self._state = "closed"

    def record_failure(self):
        self._fail_count += 1
        if self._fail_count >= self._fail_threshold:
            self._state = "open"
            self._opened_at = time.monotonic()
