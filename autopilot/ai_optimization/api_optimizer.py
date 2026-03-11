"""API Optimization Agent

This module provides intelligent API request optimization to minimize
rate limiting and maximize throughput using adaptive strategies.
"""

import logging
import random
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class APIOptimizationAgent:
    """Intelligent agent for optimizing API request strategies."""

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95):
        """Initialize the API optimization agent.

        Args:
            learning_rate: Learning rate for Q-learning
            discount_factor: Discount factor for future rewards
        """
        # Q-learning parameters
        self.q_table: Any = defaultdict(lambda: defaultdict(float))
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = 0.1  # Exploration rate

        # Strategy options
        self.strategies = ["batch", "sequential", "parallel", "adaptive"]

        # Performance history
        self.history: deque[Any] = deque(maxlen=1000)
        self.rate_limit_violations = 0
        self.total_requests = 0

        # Rate limit tracking
        self.rate_limits = {
            "remaining": 5000,
            "limit": 5000,
            "reset_time": time.time() + 3600,
        }

    def get_state(
        self, rate_limit_remaining: int, data_staleness: float, priority: str
    ) -> tuple:
        """Get current state for decision making.

        Args:
            rate_limit_remaining: Number of API calls remaining
            data_staleness: How stale is the data (0-1)
            priority: Priority level (low/medium/high/critical)

        Returns:
            State tuple
        """
        # Discretize continuous values for state space
        limit_bucket = self._discretize(rate_limit_remaining, [0, 100, 500, 1000, 5000])
        staleness_bucket = self._discretize(data_staleness, [0.0, 0.3, 0.6, 1.0])

        return (limit_bucket, staleness_bucket, priority)

    def _discretize(self, value: float, buckets: list[float]) -> int:
        """Discretize continuous value into buckets.

        Args:
            value: Value to discretize
            buckets: Bucket boundaries

        Returns:
            Bucket index
        """
        for i, boundary in enumerate(buckets):
            if value <= boundary:
                return i
        return len(buckets) - 1

    def choose_strategy(self, state: tuple, force_exploit: bool = False) -> str:
        """Choose API request strategy for current state.

        Args:
            state: Current state tuple
            force_exploit: If True, always exploit (no exploration)

        Returns:
            Strategy name
        """
        # Initialize Q-values for new state
        if state not in self.q_table:
            for strategy in self.strategies:
                self.q_table[state][strategy] = 0.0

        # Epsilon-greedy strategy selection (random used for ML exploration, not security)
        if not force_exploit and random.random() < self.epsilon:  # noqa: S311
            # Explore: random strategy
            strategy = random.choice(self.strategies)  # noqa: S311
            logger.debug(f"Exploring strategy: {strategy}")
        else:
            # Exploit: best known strategy
            strategy = max(self.q_table[state], key=lambda s: self.q_table[state][s])
            logger.debug(f"Exploiting best strategy: {strategy}")

        return strategy

    def update_q_value(
        self, state: tuple, action: str, reward: float, next_state: tuple
    ):
        """Update Q-value based on experience.

        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state reached
        """
        # Initialize next state if needed
        if next_state not in self.q_table:
            for strategy in self.strategies:
                self.q_table[next_state][strategy] = 0.0

        # Q-learning update
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[state][action] = new_q

        logger.debug(f"Updated Q({state}, {action}): {current_q:.3f} -> {new_q:.3f}")

    def calculate_reward(
        self,
        execution_time: float,
        rate_limit_used: int,
        success: bool,
        violated_limit: bool,
    ) -> float:
        """Calculate reward for action taken.

        Args:
            execution_time: Time taken to execute
            rate_limit_used: Number of API calls used
            success: Whether operation succeeded
            violated_limit: Whether rate limit was violated

        Returns:
            Reward value
        """
        reward = 0.0

        # Success bonus
        if success:
            reward += 10.0
        else:
            reward -= 20.0

        # Rate limit efficiency
        if rate_limit_used < 5:
            reward += 5.0
        elif rate_limit_used < 10:
            reward += 2.0
        else:
            reward -= rate_limit_used * 0.5

        # Rate limit violation penalty
        if violated_limit:
            reward -= 50.0
            self.rate_limit_violations += 1

        # Speed bonus (lower is better)
        if execution_time < 1.0:
            reward += 3.0
        elif execution_time > 5.0:
            reward -= 2.0

        return reward

    def execute_with_strategy(
        self, strategy: str, api_calls: list[Callable[..., Any]], timeout: float = 30.0
    ) -> dict[str, Any]:
        """Execute API calls using specified strategy.

        Args:
            strategy: Strategy to use
            api_calls: List of API call functions
            timeout: Maximum execution time

        Returns:
            Dictionary with results and metrics
        """
        start_time = time.time()
        results = []
        api_calls_made = 0

        try:
            if strategy == "batch":
                # Batch strategy: group calls together
                results = self._execute_batch(api_calls, timeout)
                api_calls_made = 1  # Batched into one call

            elif strategy == "sequential":
                # Sequential strategy: one at a time with delays
                for call in api_calls:
                    if time.time() - start_time > timeout:
                        break
                    results.append(call())
                    api_calls_made += 1
                    time.sleep(0.1)  # Small delay between calls

            elif strategy == "parallel":
                # Parallel strategy: execute all at once
                for call in api_calls:
                    results.append(call())
                    api_calls_made += 1

            elif strategy == "adaptive":
                # Adaptive strategy: based on current rate limits
                results = self._execute_adaptive(api_calls, timeout)
                api_calls_made = len(results)

            success = True

        except Exception as e:
            logger.error(f"Strategy {strategy} failed: {e}")
            success = False

        execution_time = time.time() - start_time
        self.total_requests += api_calls_made

        # Update rate limits (simulated)
        self.rate_limits["remaining"] -= api_calls_made
        violated = self.rate_limits["remaining"] < 0

        return {
            "results": results,
            "execution_time": execution_time,
            "api_calls_made": api_calls_made,
            "success": success,
            "violated_limit": violated,
            "strategy": strategy,
        }

    def _execute_batch(
        self, api_calls: list[Callable[..., Any]], timeout: float
    ) -> list[Any]:
        """Execute calls in batches."""
        # Simplified batching - in reality would use GraphQL or batch endpoints
        results = []
        for call in api_calls:
            results.append(call())
        return results

    def _execute_adaptive(
        self, api_calls: list[Callable[..., Any]], timeout: float
    ) -> list[Any]:
        """Execute calls adaptively based on rate limits."""
        results = []
        start_time = time.time()

        for call in api_calls:
            if time.time() - start_time > timeout:
                break

            # Check rate limits
            if self.rate_limits["remaining"] < 100:
                # Low on rate limit, slow down
                time.sleep(0.5)

            results.append(call())
            self.rate_limits["remaining"] -= 1

        return results

    def optimize_request_batch(self, requests: list[dict]) -> list[list[dict]]:
        """Optimize batching of requests.

        Args:
            requests: List of request dictionaries

        Returns:
            List of optimized batches
        """
        # Group by priority
        priority_groups = defaultdict(list)
        for req in requests:
            priority = req.get("priority", "medium")
            priority_groups[priority].append(req)

        # Create batches
        batches = []

        # Process high priority first
        for priority in ["critical", "high", "medium", "low"]:
            if priority in priority_groups:
                group = priority_groups[priority]

                # Split into batches of 10
                for i in range(0, len(group), 10):
                    batches.append(group[i : i + 10])

        return batches

    def update_rate_limits(self, remaining: int, limit: int, reset_time: float):
        """Update rate limit information.

        Args:
            remaining: Remaining API calls
            limit: Total API call limit
            reset_time: When limit resets (timestamp)
        """
        self.rate_limits = {
            "remaining": remaining,
            "limit": limit,
            "reset_time": reset_time,
        }

        logger.info(f"Rate limits updated: {remaining}/{limit} remaining")

    def get_statistics(self) -> dict[str, Any]:
        """Get optimization statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_requests": self.total_requests,
            "rate_limit_violations": self.rate_limit_violations,
            "violation_rate": (
                self.rate_limit_violations / self.total_requests
                if self.total_requests > 0
                else 0
            ),
            "current_rate_limit": self.rate_limits,
            "q_table_size": len(self.q_table),
            "strategies_learned": len(self.q_table),
        }

    def should_throttle(self) -> bool:
        """Determine if we should throttle requests.

        Returns:
            True if should throttle
        """
        # Throttle if less than 10% remaining
        remaining_pct = self.rate_limits["remaining"] / self.rate_limits["limit"]

        return remaining_pct < 0.1


# Global optimizer instance
_global_optimizer: APIOptimizationAgent | None = None
_global_optimizer_lock = threading.Lock()


def get_optimizer() -> APIOptimizationAgent:
    """Get global optimizer instance (thread-safe)."""
    global _global_optimizer
    if _global_optimizer is None:
        with _global_optimizer_lock:
            if _global_optimizer is None:
                _global_optimizer = APIOptimizationAgent()
    return _global_optimizer


if __name__ == "__main__":
    # Example usage
    optimizer = APIOptimizationAgent()

    # Mock API calls
    def mock_api_call(i):
        time.sleep(0.01)  # Simulate API delay
        return {"data": f"result_{i}"}

    # Create test calls
    api_calls = [lambda i=i: mock_api_call(i) for i in range(20)]

    print("API Optimization Agent - Example Usage\n")
    print("=" * 70)

    # Test different strategies
    for strategy in ["sequential", "parallel", "adaptive", "batch"]:
        state = optimizer.get_state(
            rate_limit_remaining=1000, data_staleness=0.5, priority="medium"
        )

        print(f"\nTesting strategy: {strategy}")
        result = optimizer.execute_with_strategy(strategy, api_calls[:5])

        print(f"  Execution time: {result['execution_time']:.3f}s")
        print(f"  API calls made: {result['api_calls_made']}")
        print(f"  Success: {result['success']}")

        # Calculate reward
        reward = optimizer.calculate_reward(
            result["execution_time"],
            result["api_calls_made"],
            result["success"],
            result["violated_limit"],
        )

        print(f"  Reward: {reward:.2f}")

        # Update Q-value
        next_state = optimizer.get_state(
            rate_limit_remaining=995, data_staleness=0.2, priority="medium"
        )
        optimizer.update_q_value(state, strategy, reward, next_state)

    # Show statistics
    stats = optimizer.get_statistics()
    print("\n" + "=" * 70)
    print("Statistics:")
    for key, value in stats.items():
        if key != "current_rate_limit":
            print(f"  {key}: {value}")
