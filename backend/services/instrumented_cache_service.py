"""
Instrumented Redis Cache Service with Performance Metrics

Provides a Redis cache wrapper with automatic performance tracking,
hit/miss rate monitoring, and Prometheus metrics.
"""

import json
import logging
from typing import Any, Optional, Union
import redis

from backend.config import get_settings
from backend.observability.metrics import track_cache_operation, update_cache_hit_ratio

settings = get_settings()
logger = logging.getLogger(__name__)


class InstrumentedCacheService:
    """
    Redis cache service with automatic performance monitoring.

    Tracks:
    - Cache hit/miss rates
    - Operation latency
    - Cache errors
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize instrumented cache service.

        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """
        Get or create Redis client.

        Returns:
            Redis client instance
        """
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self._client.ping()
                logger.info("Redis connection established successfully")
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

        return self._client

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with track_cache_operation("get") as track_result:
            try:
                value = self.client.get(key)

                if value is not None:
                    track_result("hit")
                    logger.debug(f"Cache hit: {key}")

                    # Try to parse JSON
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
                else:
                    track_result("miss")
                    logger.debug(f"Cache miss: {key}")
                    return None

            except Exception as e:
                track_result("error")
                logger.error(f"Cache get error for key {key}: {e}")
                return None
            finally:
                # Update hit ratio periodically
                update_cache_hit_ratio()

    def set(
        self,
        key: str,
        value: Any,
        expiration: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expiration: Expiration time in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        with track_cache_operation("set") as track_result:
            try:
                # Serialize non-string values as JSON
                if not isinstance(value, str):
                    value = json.dumps(value)

                if expiration:
                    result = self.client.setex(key, expiration, value)
                else:
                    result = self.client.set(key, value)

                track_result("success")
                logger.debug(f"Cache set: {key} (expires in {expiration}s)")
                return bool(result)

            except Exception as e:
                track_result("error")
                logger.error(f"Cache set error for key {key}: {e}")
                return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        with track_cache_operation("delete") as track_result:
            try:
                result = self.client.delete(key)
                track_result("success" if result > 0 else "miss")
                logger.debug(f"Cache delete: {key}")
                return result > 0

            except Exception as e:
                track_result("error")
                logger.error(f"Cache delete error for key {key}: {e}")
                return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        with track_cache_operation("exists") as track_result:
            try:
                result = self.client.exists(key)
                track_result("hit" if result > 0 else "miss")
                return result > 0

            except Exception as e:
                track_result("error")
                logger.error(f"Cache exists error for key {key}: {e}")
                return False

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key.

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if expiration was set, False otherwise
        """
        with track_cache_operation("expire") as track_result:
            try:
                result = self.client.expire(key, seconds)
                track_result("success" if result else "miss")
                return result

            except Exception as e:
                track_result("error")
                logger.error(f"Cache expire error for key {key}: {e}")
                return False

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (None for missing keys)
        """
        results = {}

        for key in keys:
            results[key] = self.get(key)

        return results

    def set_many(
        self,
        mapping: dict[str, Any],
        expiration: Optional[int] = None,
    ) -> int:
        """
        Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs
            expiration: Expiration time in seconds (optional)

        Returns:
            Number of keys successfully set
        """
        success_count = 0

        for key, value in mapping.items():
            if self.set(key, value, expiration):
                success_count += 1

        return success_count

    def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple keys from cache.

        Args:
            keys: List of cache keys

        Returns:
            Number of keys successfully deleted
        """
        with track_cache_operation("delete_many") as track_result:
            try:
                if not keys:
                    track_result("success")
                    return 0

                result = self.client.delete(*keys)
                track_result("success")
                logger.debug(f"Cache delete_many: {len(keys)} keys, {result} deleted")
                return result

            except Exception as e:
                track_result("error")
                logger.error(f"Cache delete_many error: {e}")
                return 0

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        with track_cache_operation("clear_pattern") as track_result:
            try:
                keys = list(self.client.scan_iter(match=pattern))
                if not keys:
                    track_result("success")
                    return 0

                result = self.client.delete(*keys)
                track_result("success")
                logger.info(f"Cache cleared pattern {pattern}: {result} keys deleted")
                return result

            except Exception as e:
                track_result("error")
                logger.error(f"Cache clear_pattern error for pattern {pattern}: {e}")
                return 0

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment by (default: 1)

        Returns:
            New value after increment, or None on error
        """
        with track_cache_operation("increment") as track_result:
            try:
                result = self.client.incrby(key, amount)
                track_result("success")
                return result

            except Exception as e:
                track_result("error")
                logger.error(f"Cache increment error for key {key}: {e}")
                return None

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            info = self.client.info("stats")
            return {
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0),
                ),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """
        Calculate cache hit rate.

        Args:
            hits: Number of cache hits
            misses: Number of cache misses

        Returns:
            Hit rate as a percentage (0-100)
        """
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

    def close(self):
        """Close Redis connection."""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global cache service instance
_cache_service: Optional[InstrumentedCacheService] = None


def get_cache_service() -> InstrumentedCacheService:
    """
    Get or create the global cache service instance.

    Returns:
        InstrumentedCacheService instance
    """
    global _cache_service

    if _cache_service is None:
        _cache_service = InstrumentedCacheService()

    return _cache_service


# Convenience alias
cache = get_cache_service()
