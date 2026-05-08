#!/usr/bin/env python3
"""
Self-Healing Workflow System
Automatically detects failures, diagnoses issues, and attempts recovery
Implements circuit breaker pattern and intelligent retry strategies
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable
import hashlib


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class FailureRecord:
    """Record of a failure"""

    timestamp: datetime
    component: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for fault tolerance

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing if service recovered
    """

    name: str
    failure_threshold: int = 5
    timeout_seconds: int = 60
    success_threshold: int = 2

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    open_time: Optional[datetime] = None

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()

    def record_failure(self, error: Exception):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0

        if (
            self.state == CircuitState.CLOSED
            and self.failure_count >= self.failure_threshold
        ):
            self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()

    def can_attempt(self) -> bool:
        """Check if request can proceed"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if (
                self.open_time
                and (datetime.now() - self.open_time).seconds >= self.timeout_seconds
            ):
                self._transition_to_half_open()
                return True
            return False

        # HALF_OPEN state
        return True

    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.open_time = datetime.now()
        print(
            f"🔴 Circuit breaker '{self.name}' OPENED after {self.failure_count} failures"
        )

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        print(f"🟡 Circuit breaker '{self.name}' HALF-OPEN (testing recovery)")

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        print(f"🟢 Circuit breaker '{self.name}' CLOSED (recovered)")


class RetryStrategy:
    """
    Intelligent retry strategy with exponential backoff
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential: bool = True,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        if self.exponential:
            delay = min(self.base_delay * (2**attempt), self.max_delay)
        else:
            delay = self.base_delay

        if self.jitter:
            import random

            delay *= random.uniform(0.5, 1.5)

        return delay

    async def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    print(f"✅ Retry successful on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e

                if attempt < self.max_attempts - 1:
                    delay = self.get_delay(attempt)
                    print(
                        f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    print(f"❌ All {self.max_attempts} attempts failed")

        raise last_exception


class SelfHealingSystem:
    """
    Self-healing system that automatically recovers from failures

    Features:
    - Automatic failure detection
    - Intelligent diagnosis
    - Automated recovery attempts
    - Circuit breaker pattern
    - Retry with exponential backoff
    - Failure pattern analysis
    """

    def __init__(self):
        self.failures: List[FailureRecord] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.recovery_strategies: Dict[str, Callable] = {}

    def register_circuit_breaker(self, name: str, breaker: CircuitBreaker):
        """Register a circuit breaker"""
        self.circuit_breakers[name] = breaker

    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register a recovery strategy for an error type"""
        self.recovery_strategies[error_type] = strategy

    async def execute_with_protection(
        self, operation_name: str, func: Callable, *args, **kwargs
    ):
        """Execute operation with circuit breaker protection"""
        breaker = self.circuit_breakers.get(operation_name)

        if breaker and not breaker.can_attempt():
            raise Exception(f"Circuit breaker '{operation_name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            if breaker:
                breaker.record_success()
            return result
        except Exception as e:
            if breaker:
                breaker.record_failure(e)

            # Record failure
            failure = FailureRecord(
                timestamp=datetime.now(),
                component=operation_name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            self.failures.append(failure)

            # Attempt recovery
            await self.attempt_recovery(failure)

            raise

    async def attempt_recovery(self, failure: FailureRecord):
        """Attempt to recover from failure"""
        print(f"\n🔧 Attempting recovery for {failure.component}...")

        failure.recovery_attempted = True

        # Get recovery strategy
        strategy = self.recovery_strategies.get(failure.error_type)

        if strategy:
            try:
                await strategy(failure)
                failure.recovery_successful = True
                print(f"✅ Recovery successful for {failure.component}")
            except Exception as e:
                failure.recovery_successful = False
                print(f"❌ Recovery failed: {e}")
        else:
            print(f"⚠️  No recovery strategy for {failure.error_type}")
            failure.recovery_successful = False

    def analyze_failure_patterns(self) -> Dict[str, any]:
        """Analyze failure patterns to identify systemic issues"""
        if not self.failures:
            return {"status": "no_failures"}

        recent = [
            f
            for f in self.failures
            if datetime.now() - f.timestamp < timedelta(hours=24)
        ]

        # Group by component
        by_component = {}
        for f in recent:
            by_component.setdefault(f.component, []).append(f)

        # Group by error type
        by_error = {}
        for f in recent:
            by_error.setdefault(f.error_type, []).append(f)

        # Calculate recovery rate
        attempted = sum(1 for f in recent if f.recovery_attempted)
        successful = sum(1 for f in recent if f.recovery_successful)
        recovery_rate = (successful / attempted * 100) if attempted > 0 else 0

        return {
            "status": "analyzed",
            "total_failures_24h": len(recent),
            "failures_by_component": {k: len(v) for k, v in by_component.items()},
            "failures_by_error_type": {k: len(v) for k, v in by_error.items()},
            "recovery_rate_percent": recovery_rate,
            "top_failing_component": (
                max(by_component.items(), key=lambda x: len(x[1]))[0]
                if by_component
                else None
            ),
        }

    def get_health_score(self) -> float:
        """Calculate system health score (0-100)"""
        recent = [
            f
            for f in self.failures
            if datetime.now() - f.timestamp < timedelta(hours=1)
        ]

        if not recent:
            return 100.0

        # Deduct points for failures
        health = 100.0
        health -= len(recent) * 5  # 5 points per failure

        # Add points for successful recoveries
        recoveries = sum(1 for f in recent if f.recovery_successful)
        health += recoveries * 2

        # Check circuit breakers
        open_breakers = sum(
            1 for b in self.circuit_breakers.values() if b.state == CircuitState.OPEN
        )
        health -= open_breakers * 20  # 20 points per open circuit

        return max(0.0, min(100.0, health))


# Recovery strategies
async def recover_cache_miss(failure: FailureRecord):
    """Recovery strategy for cache misses"""
    print("  🔄 Warming cache...")
    await asyncio.sleep(0.5)  # Simulate cache warming
    print("  ✅ Cache warmed")


async def recover_api_rate_limit(failure: FailureRecord):
    """Recovery strategy for API rate limiting"""
    print("  ⏳ Waiting for rate limit reset...")
    await asyncio.sleep(2)  # Simulate waiting
    print("  ✅ Rate limit reset")


async def recover_network_timeout(failure: FailureRecord):
    """Recovery strategy for network timeouts"""
    print("  🔄 Attempting connection retry with increased timeout...")
    await asyncio.sleep(1)
    print("  ✅ Connection re-established")


async def demo_self_healing():
    """Demo the self-healing system"""
    print("🏥 SELF-HEALING WORKFLOW SYSTEM\n")
    print("=" * 70)

    # Initialize system
    system = SelfHealingSystem()

    # Register circuit breakers
    system.register_circuit_breaker(
        "github_api", CircuitBreaker("github_api", failure_threshold=3)
    )
    system.register_circuit_breaker(
        "cache_service", CircuitBreaker("cache_service", failure_threshold=5)
    )

    # Register recovery strategies
    system.register_recovery_strategy("CacheMissError", recover_cache_miss)
    system.register_recovery_strategy("RateLimitError", recover_api_rate_limit)
    system.register_recovery_strategy("TimeoutError", recover_network_timeout)

    # Demo: Simulate operations with failures
    print("\n📊 Simulating Operations:\n")

    async def flaky_operation(fail_count: int = 0):
        """Simulated flaky operation"""
        if fail_count > 0:
            raise Exception("RateLimitError: API rate limit exceeded")
        await asyncio.sleep(0.1)
        return "Success"

    # Test with retry strategy
    print("1️⃣  Testing retry strategy...")
    retry = RetryStrategy(max_attempts=3, base_delay=0.5)

    try:
        # This will fail twice then succeed
        attempt = 0

        async def failing_then_success():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise Exception("RateLimitError: API rate limit exceeded")
            return "Success"

        result = await retry.execute(failing_then_success)
        print(f"✅ Operation succeeded: {result}\n")
    except Exception as e:
        print(f"❌ Operation failed: {e}\n")

    # Test circuit breaker
    print("2️⃣  Testing circuit breaker...")

    async def failing_operation():
        raise Exception("TimeoutError: Connection timeout")

    breaker = system.circuit_breakers["github_api"]

    # Trigger circuit breaker
    for i in range(5):
        try:
            await system.execute_with_protection("github_api", failing_operation)
        except Exception as e:
            print(f"  Attempt {i+1}: {type(e).__name__}")

    print(f"\n  Circuit state: {breaker.state.value}")
    print(f"  Can attempt: {breaker.can_attempt()}\n")

    # Analyze failure patterns
    print("3️⃣  Analyzing failure patterns...")
    analysis = system.analyze_failure_patterns()

    if analysis["status"] == "analyzed":
        print(f"\n  Total failures (24h): {analysis['total_failures_24h']}")
        print(f"  Recovery rate: {analysis['recovery_rate_percent']:.1f}%")
        print(f"  Top failing: {analysis['top_failing_component']}")

    # Health score
    health = system.get_health_score()
    print(f"\n  System health: {health:.1f}/100")

    # Summary
    print("\n" + "=" * 70)
    print("💡 Self-Healing Features:")
    print("  • Circuit breaker pattern for fault isolation")
    print("  • Intelligent retry with exponential backoff")
    print("  • Automatic failure detection & diagnosis")
    print("  • Pluggable recovery strategies")
    print("  • Failure pattern analysis")
    print("  • Real-time health scoring")


if __name__ == "__main__":
    asyncio.run(demo_self_healing())
