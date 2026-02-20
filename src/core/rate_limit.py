"""
Rate limiting implementation using Redis or in-memory fallback.

Provides sliding window rate limiting with configurable limits per endpoint.
Falls back to in-memory storage when Redis is unavailable.
"""

import asyncio
import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status

from src.core.config import settings


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    Used as fallback when Redis is not available.
    Note: Not suitable for multi-process deployments.
    """

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Check if a key has exceeded the rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., IP + endpoint).
            limit: Maximum number of requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            Tuple of (is_limited, remaining_requests).
        """
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds

            # Clean up old entries
            self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]

            current_count = len(self._requests[key])

            if current_count >= limit:
                return True, 0

            # Add current request
            self._requests[key].append(now)

            return False, limit - current_count - 1

    async def reset(self, key: str) -> None:
        """Reset rate limit for a specific key."""
        async with self._lock:
            self._requests.pop(key, None)

    async def cleanup(self) -> None:
        """Remove expired entries from all keys."""
        async with self._lock:
            now = time.time()
            keys_to_remove = []

            for key, timestamps in self._requests.items():
                # Keep only timestamps from last hour (max reasonable window)
                self._requests[key] = [ts for ts in timestamps if ts > now - 3600]
                if not self._requests[key]:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._requests[key]


class RedisRateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.

    Suitable for distributed deployments with multiple processes.
    """

    def __init__(self, redis_client: "Redis") -> None:  # type: ignore[name-defined]
        self._redis = redis_client

    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Check if a key has exceeded the rate limit using Redis sorted sets.

        Args:
            key: Unique identifier for the rate limit.
            limit: Maximum number of requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            Tuple of (is_limited, remaining_requests).
        """
        now = time.time()
        window_start = now - window_seconds
        rate_key = f"rate_limit:{key}"

        pipe = self._redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(rate_key, 0, window_start)

        # Count current entries
        pipe.zcard(rate_key)

        # Add current request with current timestamp as score
        pipe.zadd(rate_key, {str(now): now})

        # Set expiry on the key
        pipe.expire(rate_key, window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= limit:
            # Remove the request we just added since we're rate limited
            await self._redis.zrem(rate_key, str(now))
            return True, 0

        return False, limit - current_count - 1

    async def reset(self, key: str) -> None:
        """Reset rate limit for a specific key."""
        await self._redis.delete(f"rate_limit:{key}")


# Global rate limiter instance
_rate_limiter: InMemoryRateLimiter | RedisRateLimiter | None = None


def get_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    """
    Get the rate limiter instance.

    Returns in-memory limiter by default. Can be upgraded to Redis
    by calling set_redis_rate_limiter().
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


def set_redis_rate_limiter(redis_client: "Redis") -> None:  # type: ignore[name-defined]
    """
    Set up Redis-based rate limiting.

    Call this during application startup if Redis is available.
    """
    global _rate_limiter
    _rate_limiter = RedisRateLimiter(redis_client)


def rate_limit(
    limit: int | None = None,
    window_seconds: int = 60,
    key_func: Callable[[Request], str] | None = None,
) -> Callable:
    """
    Rate limiting dependency factory.

    Args:
        limit: Maximum requests per window. Defaults to settings value.
        window_seconds: Time window in seconds. Defaults to 60.
        key_func: Function to generate rate limit key from request.
                  Defaults to client IP + path.

    Returns:
        FastAPI dependency function.

    Usage:
        @router.get("/endpoint", dependencies=[Depends(rate_limit(limit=10))])
        async def endpoint():
            ...
    """
    if limit is None:
        limit = settings.rate_limit_per_minute

    async def rate_limit_dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return

        # Generate rate limit key
        if key_func:
            key = key_func(request)
        else:
            # Default: IP + path
            client_ip = request.client.host if request.client else "unknown"
            key = f"{client_ip}:{request.url.path}"

        limiter = get_rate_limiter()
        is_limited, remaining = await limiter.is_rate_limited(
            key=key,
            limit=limit,  # type: ignore[arg-type]
            window_seconds=window_seconds,
        )

        # Add rate limit headers
        request.state.rate_limit_limit = limit
        request.state.rate_limit_remaining = remaining

        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window_seconds),
                    "Retry-After": str(window_seconds),
                },
            )

    return rate_limit_dependency


def auth_rate_limit() -> Callable:
    """
    Rate limiting for authentication endpoints.

    Uses stricter limits to prevent brute force attacks.
    """
    return rate_limit(
        limit=settings.auth_rate_limit_per_minute,
        window_seconds=60,
    )
