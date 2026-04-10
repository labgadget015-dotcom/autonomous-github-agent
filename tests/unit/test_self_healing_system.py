"""Unit tests for .github/scripts/self_healing_system.py"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from self_healing_system import (
    CircuitState, CircuitBreaker, FailureRecord,
    RetryStrategy, SelfHealingSystem
)


class TestCircuitStateEnum:
    def test_closed_value(self):
        assert CircuitState.CLOSED.value == "closed"

    def test_open_value(self):
        assert CircuitState.OPEN.value == "open"

    def test_half_open_value(self):
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    def _breaker(self, threshold=3, timeout=60):
        return CircuitBreaker(name="test", failure_threshold=threshold, timeout_seconds=timeout)

    def test_initial_state_is_closed(self):
        breaker = self._breaker()
        assert breaker.state == CircuitState.CLOSED

    def test_can_attempt_when_closed(self):
        breaker = self._breaker()
        assert breaker.can_attempt() is True

    def test_transitions_to_open_on_threshold(self):
        breaker = self._breaker(threshold=3)
        error = Exception("test error")
        for _ in range(3):
            breaker.record_failure(error)
        assert breaker.state == CircuitState.OPEN

    def test_cannot_attempt_when_open(self):
        breaker = self._breaker(threshold=1, timeout=9999)
        breaker.record_failure(Exception("error"))
        assert breaker.state == CircuitState.OPEN
        assert breaker.can_attempt() is False

    def test_record_success_resets_failures(self):
        breaker = self._breaker()
        breaker.failure_count = 2
        breaker.record_success()
        assert breaker.failure_count == 0

    def test_transitions_from_half_open_to_closed_on_success(self):
        breaker = CircuitBreaker(name="test", success_threshold=2)
        breaker.state = CircuitState.HALF_OPEN
        breaker.record_success()
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_transitions_to_open_on_failure(self):
        breaker = self._breaker()
        breaker.state = CircuitState.HALF_OPEN
        breaker.record_failure(Exception("fail"))
        assert breaker.state == CircuitState.OPEN

    def test_can_attempt_in_half_open(self):
        breaker = self._breaker()
        breaker.state = CircuitState.HALF_OPEN
        assert breaker.can_attempt() is True

    def test_increment_failure_count(self):
        breaker = self._breaker(threshold=10)
        breaker.record_failure(Exception("error"))
        assert breaker.failure_count == 1


class TestRetryStrategy:
    def test_creates_with_defaults(self):
        rs = RetryStrategy()
        assert rs.max_attempts == 3
        assert rs.base_delay == 1.0

    def test_get_delay_exponential(self):
        rs = RetryStrategy(base_delay=1.0, exponential=True, jitter=False)
        # attempt 0: 1.0, attempt 1: 2.0, attempt 2: 4.0
        assert rs.get_delay(0) == 1.0
        assert rs.get_delay(1) == 2.0
        assert rs.get_delay(2) == 4.0

    def test_get_delay_non_exponential(self):
        rs = RetryStrategy(base_delay=2.0, exponential=False, jitter=False)
        assert rs.get_delay(0) == 2.0
        assert rs.get_delay(3) == 2.0

    def test_get_delay_capped_at_max(self):
        rs = RetryStrategy(base_delay=1.0, max_delay=5.0, exponential=True, jitter=False)
        delay = rs.get_delay(10)  # Would be 1024 without cap
        assert delay <= 5.0

    def test_get_delay_with_jitter_in_range(self):
        rs = RetryStrategy(base_delay=10.0, exponential=False, jitter=True)
        for _ in range(20):
            delay = rs.get_delay(0)
            assert 5.0 <= delay <= 15.0

    @pytest.mark.asyncio
    async def test_execute_success_on_first_try(self):
        rs = RetryStrategy(max_attempts=3)
        calls = []

        async def success_func():
            calls.append(1)
            return "result"

        result = await rs.execute(success_func)
        assert result == "result"
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_execute_retries_on_failure(self):
        rs = RetryStrategy(max_attempts=3, base_delay=0.01, jitter=False)
        calls = []

        async def fail_then_succeed():
            calls.append(1)
            if len(calls) < 2:
                raise ValueError("not ready")
            return "ok"

        result = await rs.execute(fail_then_succeed)
        assert result == "ok"
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_execute_raises_after_all_retries(self):
        rs = RetryStrategy(max_attempts=2, base_delay=0.01, jitter=False)

        async def always_fails():
            raise RuntimeError("permanent failure")

        with pytest.raises(RuntimeError, match="permanent failure"):
            await rs.execute(always_fails)


class TestSelfHealingSystem:
    def test_creates_with_empty_structures(self):
        shs = SelfHealingSystem()
        assert shs.failures == []
        assert shs.circuit_breakers == {}
        assert shs.recovery_strategies == {}

    def test_register_circuit_breaker(self):
        shs = SelfHealingSystem()
        breaker = CircuitBreaker(name="my_service")
        shs.register_circuit_breaker("my_service", breaker)
        assert "my_service" in shs.circuit_breakers

    def test_register_recovery_strategy(self):
        shs = SelfHealingSystem()

        def my_recovery(failure):
            pass

        shs.register_recovery_strategy("ValueError", my_recovery)
        assert "ValueError" in shs.recovery_strategies

    @pytest.mark.asyncio
    async def test_execute_with_protection_success(self):
        shs = SelfHealingSystem()
        breaker = CircuitBreaker(name="svc")
        shs.register_circuit_breaker("svc", breaker)

        async def good_op():
            return "ok"

        result = await shs.execute_with_protection("svc", good_op)
        assert result == "ok"
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_execute_with_protection_records_failure(self):
        shs = SelfHealingSystem()

        async def failing_op():
            raise RuntimeError("crash")

        with pytest.raises(RuntimeError):
            await shs.execute_with_protection("svc", failing_op)

        assert len(shs.failures) == 1
        assert shs.failures[0].error_type == "RuntimeError"

    @pytest.mark.asyncio
    async def test_execute_raises_when_circuit_open(self):
        shs = SelfHealingSystem()
        breaker = CircuitBreaker(name="svc", failure_threshold=1, timeout_seconds=9999)
        shs.register_circuit_breaker("svc", breaker)

        # Open the circuit
        async def bad_op():
            raise RuntimeError("error")

        with pytest.raises(RuntimeError):
            await shs.execute_with_protection("svc", bad_op)

        # Now circuit is open, next attempt should be rejected
        async def good_op():
            return "ok"

        with pytest.raises(Exception, match="OPEN"):
            await shs.execute_with_protection("svc", good_op)


class TestFailureRecord:
    def test_creates_failure_record(self):
        fr = FailureRecord(
            timestamp=datetime.now(),
            component="my_service",
            error_type="ConnectionError",
            error_message="Could not connect",
        )
        assert fr.component == "my_service"
        assert fr.recovery_attempted is False
        assert fr.recovery_successful is None
