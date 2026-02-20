"""
Caching abstraction layer with Redis and in-memory implementations.

Provides a unified interface for caching with automatic serialization.
Falls back to in-memory cache when Redis is unavailable.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, TypeVar

from src.core.config import settings

T = TypeVar("T")


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass


class InMemoryCache(CacheBackend):
    """
    In-memory cache implementation.

    Suitable for single-process deployments or development.
    Note: Data is lost on restart and not shared between processes.
    """

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get a value from cache, respecting TTL."""
        async with self._lock:
            if key not in self._cache:
                return None

            value, expires_at = self._cache[key]

            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return None

            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional TTL in seconds."""
        async with self._lock:
            expires_at = time.time() + ttl if ttl else None
            self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if a key exists and hasn't expired."""
        value = await self.get(key)
        return value is not None

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        async with self._lock:
            now = time.time()
            expired_keys = [
                key
                for key, (_, expires_at) in self._cache.items()
                if expires_at is not None and now > expires_at
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)


class RedisCache(CacheBackend):
    """
    Redis cache implementation.

    Suitable for distributed deployments with multiple processes.
    """

    def __init__(self, redis_client: "Redis") -> None:  # type: ignore[name-defined]
        self._redis = redis_client
        self._prefix = "cache:"

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get a value from Redis, deserializing JSON."""
        value = await self._redis.get(self._make_key(key))

        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.decode() if isinstance(value, bytes) else value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in Redis with optional TTL, serializing to JSON."""
        serialized = json.dumps(value) if not isinstance(value, str) else value

        if ttl:
            await self._redis.setex(self._make_key(key), ttl, serialized)
        else:
            await self._redis.set(self._make_key(key), serialized)

    async def delete(self, key: str) -> None:
        """Delete a key from Redis."""
        await self._redis.delete(self._make_key(key))

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        return await self._redis.exists(self._make_key(key)) > 0

    async def clear(self) -> None:
        """Clear all cached values with our prefix."""
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor=cursor,
                match=f"{self._prefix}*",
                count=100,
            )

            if keys:
                await self._redis.delete(*keys)

            if cursor == 0:
                break


# Global cache instance
_cache: CacheBackend | None = None


def get_cache() -> CacheBackend:
    """
    Get the cache instance.

    Returns in-memory cache by default. Can be upgraded to Redis
    by calling set_redis_cache().
    """
    global _cache
    if _cache is None:
        _cache = InMemoryCache()
    return _cache


def set_redis_cache(redis_client: "Redis") -> None:  # type: ignore[name-defined]
    """
    Set up Redis-based caching.

    Call this during application startup if Redis is available.
    """
    global _cache
    _cache = RedisCache(redis_client)


def cached(
    ttl: int | None = None,
    key_prefix: str = "",
    key_builder: Callable[..., str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Caching decorator for async functions.

    Args:
        ttl: Time-to-live in seconds. Defaults to settings.cache_ttl.
        key_prefix: Prefix for cache key.
        key_builder: Custom function to build cache key from arguments.

    Usage:
        @cached(ttl=300, key_prefix="users")
        async def get_user(user_id: int) -> User:
            ...
    """
    if ttl is None:
        ttl = settings.cache_ttl

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key: prefix:function_name:args:kwargs
                args_key = ":".join(str(arg) for arg in args)
                kwargs_key = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_key}:{kwargs_key}"

            cache = get_cache()

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


async def invalidate_cache(pattern: str) -> None:
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Key pattern to match (supports wildcards for Redis).
    """
    cache = get_cache()

    if isinstance(cache, RedisCache):
        # Redis supports pattern-based deletion
        cursor = 0
        while True:
            cursor, keys = await cache._redis.scan(
                cursor=cursor,
                match=f"cache:{pattern}",
                count=100,
            )

            if keys:
                await cache._redis.delete(*keys)

            if cursor == 0:
                break
    else:
        # For in-memory cache, just delete the exact key
        await cache.delete(pattern)
