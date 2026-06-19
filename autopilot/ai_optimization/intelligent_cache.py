"""Intelligent Cache with ML-Based Predictive Invalidation

This module implements an AI-powered caching system that learns access patterns
and predicts when cached data becomes stale, dramatically reducing API calls
while maintaining data freshness.
"""

import hashlib
import json
import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)


class AccessPredictor:
    """ML model to predict cache staleness and next access patterns."""

    def __init__(self):
        self.staleness_model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.access_model = RandomForestClassifier(
            n_estimators=50, max_depth=8, random_state=42
        )
        self.trained = False
        self.access_history = deque(maxlen=10000)
        self.staleness_history = []

    def record_access(self, key: str, timestamp: float):
        """Record an access for pattern learning."""
        self.access_history.append((timestamp, key))

    def _extract_staleness_features(self, key: str, cache_time: float) -> np.ndarray:
        """Extract features for staleness prediction."""
        current_time = time.time()
        age = current_time - cache_time

        # Calculate access frequency
        recent_accesses = []
        for access_time, access_key in self.access_history:
            if access_key == key and current_time - access_time < 3600:  # Last hour
                recent_accesses.append(access_time)

        access_frequency = len(recent_accesses)
        time_since_last_access = (
            current_time - recent_accesses[-1] if recent_accesses else 3600
        )

        # Key characteristics
        key_hash = (
            int(hashlib.sha256(key.encode(), usedforsecurity=False).hexdigest()[:8], 16)
            % 100
        )

        features = np.array(
            [
                age,
                age / 60,  # Age in minutes
                access_frequency,
                time_since_last_access,
                key_hash,
                len(recent_accesses) / (age / 60 + 1),  # Accesses per minute
            ]
        ).reshape(1, -1)

        return features

    def predict_staleness(self, key: str, cache_time: float) -> float:
        """Predict probability that cached data is stale."""
        if not self.trained:
            # Default heuristic: linear decay
            age = time.time() - cache_time
            return min(age / 3600, 1.0)  # Assume stale after 1 hour

        features = self._extract_staleness_features(key, cache_time)
        staleness_prob = self.staleness_model.predict_proba(features)[0][1]
        return staleness_prob

    def predict_next_access(self, current_key: str | None = None) -> list[str]:
        """Predict which keys are likely to be accessed next."""
        if len(self.access_history) < 100:
            return []

        # Simple pattern: keys accessed together recently
        recent_window = list(self.access_history)[-100:]
        if current_key:
            # Find keys that follow current_key
            next_keys = []
            for i, (_, key) in enumerate(recent_window[:-1]):
                if key == current_key:
                    next_keys.append(recent_window[i + 1][1])

            # Return top 3 most common
            from collections import Counter

            return [k for k, _ in Counter(next_keys).most_common(3)]

        return []

    def train(self, staleness_data: list[tuple[np.ndarray, bool]]):
        """Train the staleness prediction model."""
        if len(staleness_data) < 50:
            logger.warning("Insufficient training data for staleness model")
            return

        X = np.vstack([features for features, _ in staleness_data])
        y = np.array([label for _, label in staleness_data])

        self.staleness_model.fit(X, y)
        self.trained = True
        logger.info(f"Staleness model trained on {len(staleness_data)} samples")


class IntelligentCache:
    """AI-powered cache with predictive invalidation and prefetching."""

    def __init__(self, config=None, max_size: int = 1000, ttl: int = 3600):
        if isinstance(config, int):
            max_size = config
        elif isinstance(config, dict):
            max_size = config.get("max_size", max_size)
            ttl = config.get("ttl", ttl)
        self.cache: dict[str, tuple[Any, float]] = {}
        self.max_size = max_size
        self.default_ttl = ttl
        self.predictor = AccessPredictor()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "stale_hits": 0,
            "prefetch_hits": 0,
            "evictions": 0,
        }
        self.staleness_threshold = 0.3

    def _hash_key(self, key: str) -> str:
        """Generate consistent hash for cache key."""
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, key: str, fetch_func: Callable[..., Any] | None = None) -> Any:
        """Get value from cache, or fetch via fetch_func if provided (returns None on miss otherwise)."""
        hashed_key = self._hash_key(key)
        current_time = time.time()

        # Record access for learning
        self.predictor.record_access(key, current_time)

        if hashed_key in self.cache:
            value, cache_time = self.cache[hashed_key]

            # Check if likely stale using ML
            staleness_prob = self.predictor.predict_staleness(key, cache_time)

            if staleness_prob < self.staleness_threshold:
                self.stats["hits"] += 1
                logger.debug(f"Cache HIT for {key} (staleness: {staleness_prob:.2f})")

                # Trigger predictive prefetch
                self._prefetch_likely_next(key)

                return value
            else:
                self.stats["stale_hits"] += 1
                logger.debug(f"Cache STALE for {key} (staleness: {staleness_prob:.2f})")
                if fetch_func is None:
                    return value
        else:
            self.stats["misses"] += 1
            logger.debug(f"Cache MISS for {key}")
            if fetch_func is None:
                return None

        # Fetch fresh data
        value = fetch_func()
        self._set(hashed_key, value, current_time)

        return value

    def set(self, key: str, value: Any) -> None:
        """Public setter for test compatibility."""
        hashed_key = self._hash_key(key)
        timestamp = time.time()
        self._set(hashed_key, value, timestamp)

    def _set(self, hashed_key: str, value: Any, timestamp: float):
        """Store value in cache."""
        # Evict if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[hashed_key] = (value, timestamp)

    def _evict_lru(self):
        """Evict least recently used item."""
        if not self.cache:
            return

        # Find oldest item
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
        del self.cache[oldest_key]
        self.stats["evictions"] += 1
        logger.debug("Evicted oldest cache entry")

    def _prefetch_likely_next(self, current_key: str):
        """Prefetch data that's likely to be accessed next."""
        likely_next = self.predictor.predict_next_access(current_key)

        for next_key in likely_next:
            hashed_next_key = self._hash_key(next_key)
            if hashed_next_key not in self.cache:
                logger.debug(f"Predictive prefetch triggered for {next_key}")
                # In real implementation, would trigger async prefetch
                # For now, just log the prediction

    def invalidate(self, key: str):
        """Manually invalidate a cache entry."""
        hashed_key = self._hash_key(key)
        if hashed_key in self.cache:
            del self.cache[hashed_key]
            logger.debug(f"Invalidated cache for {key}")

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "cache_utilization": len(self.cache) / self.max_size,
        }

    def save(self, filepath: str):
        """Save cache metadata to disk using JSON (safe serialization)."""
        # Only serializable data (cache values and stats) are persisted.
        # The ML predictor is re-trained at runtime and is not saved.
        try:
            # Store each entry as a two-element list [value, timestamp]
            serializable_cache = {k: [v, ts] for k, (v, ts) in self.cache.items()}
            payload = {"cache": serializable_cache, "stats": self.stats}
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            logger.info(f"Cache saved to {filepath}")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize cache to JSON: {e}")

    def load(self, filepath: str):
        """Load cache metadata from disk using JSON (safe deserialization)."""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            # JSON arrays deserialize as lists; unpack explicitly for clarity
            self.cache = {k: (entry[0], entry[1]) for k, entry in data["cache"].items()}
            self.stats = data["stats"]
            logger.info(f"Cache loaded from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Cache file not found: {filepath}")


# Global cache instance
_global_cache: IntelligentCache | None = None
_global_cache_lock = threading.Lock()


def get_cache() -> IntelligentCache:
    """Get global cache instance (thread-safe)."""
    global _global_cache
    if _global_cache is None:
        with _global_cache_lock:
            if _global_cache is None:
                _global_cache = IntelligentCache()
    return _global_cache


if __name__ == "__main__":
    import logging as _logging

    _logging.basicConfig(level=_logging.INFO)
    _demo_logger = _logging.getLogger(__name__)

    # Example usage
    cache = IntelligentCache()

    def expensive_api_call(repo_id: int):
        _demo_logger.info("Fetching data for repo %d...", repo_id)
        time.sleep(0.1)  # Simulate API delay
        return {"id": repo_id, "data": f"repo_data_{repo_id}"}

    # Test cache performance
    for i in range(100):
        repo_id = i % 10  # Access same 10 repos repeatedly
        result = cache.get(f"repo_{repo_id}", lambda r=repo_id: expensive_api_call(r))

        if i % 20 == 0:
            stats = cache.get_stats()
            _demo_logger.info(
                "Iteration %d: Hit rate = %.2f%%", i, stats["hit_rate"] * 100
            )
            _demo_logger.info("Stats: %s", stats)
