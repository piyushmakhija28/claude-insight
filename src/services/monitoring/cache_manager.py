"""
TTL-based thread-safe in-memory cache for high-frequency API responses.

Provides a singleton TTLCache instance that caches expensive computations
(metrics, policy counts, historical chart data) with automatic expiration.
Thread-safe for concurrent access from Flask request handlers and SocketIO.

Usage:
    from services.monitoring.cache_manager import get_cache
    cache = get_cache()
    if cache.get('metrics') is None:
        data = expensive_computation()
        cache.set('metrics', data, ttl=30)
    else:
        data = cache.get('metrics')
"""

import threading
import time
from typing import Optional, Any


class TTLCache:
    """Thread-safe in-memory cache with time-to-live (TTL) support.

    Each cached value automatically expires after its TTL expires.
    Perfect for caching metrics, policy counts, and historical data
    that is expensive to compute but changes infrequently.
    """

    def __init__(self):
        """Initialize empty cache with lock for thread safety."""
        self._cache = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if present and not expired.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if present and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry_time = self._cache[key]
            if time.time() > expiry_time:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: int = 30) -> None:
        """Store value in cache with TTL.

        Args:
            key: Cache key to store under
            value: Value to cache (any picklable Python object)
            ttl: Time-to-live in seconds (default 30)
        """
        with self._lock:
            expiry_time = time.time() + ttl
            self._cache[key] = (value, expiry_time)

    def invalidate(self, key: str) -> None:
        """Manually remove cached value.

        Args:
            key: Cache key to remove
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cached values.

        Useful for full cache invalidation or cleanup.
        """
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if current_time > expiry
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


# Global singleton cache instance
_cache_instance: Optional[TTLCache] = None


def get_cache() -> TTLCache:
    """Get or create the global TTL cache singleton.

    Returns:
        Global TTLCache instance (thread-safe)
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = TTLCache()
    return _cache_instance
