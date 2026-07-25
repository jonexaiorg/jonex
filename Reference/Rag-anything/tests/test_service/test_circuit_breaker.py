import time
import pytest
from raganything.service.circuit_breaker import CircuitBreaker


class TestCircuitBreaker:
    def test_initial_state_allows(self):
        cb = CircuitBreaker(fail_threshold=3, cooldown_seconds=30)
        assert cb.allow() is True

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(fail_threshold=2, cooldown_seconds=30)
        cb.record_failure()
        cb.record_failure()
        assert cb.allow() is False

    def test_resets_on_success(self):
        cb = CircuitBreaker(fail_threshold=3, cooldown_seconds=30)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.allow() is True

    def test_half_open_after_cooldown(self):
        cb = CircuitBreaker(fail_threshold=2, cooldown_seconds=0.1)
        cb.record_failure()
        cb.record_failure()
        assert cb.allow() is False
        time.sleep(0.2)
        assert cb.allow() is True  # half-open

    def test_state_transitions(self):
        cb = CircuitBreaker(fail_threshold=2, cooldown_seconds=30)
        assert cb.state == "closed"
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        cb.record_success()
        assert cb.state == "closed"
