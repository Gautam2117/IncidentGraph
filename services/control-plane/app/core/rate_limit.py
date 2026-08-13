"""Redis-backed fixed-window rate limits for unauthenticated ingress routes."""

import asyncio
import time
from dataclasses import dataclass, field

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.core.config import settings


@dataclass(eq=False)
class RateLimiter:
    scope: str
    limit: int
    window_seconds: int
    _fallback_hits: dict[str, tuple[int, float]] = field(default_factory=dict)
    _fallback_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time()) // self.window_seconds
        key = f"ratelimit:{self.scope}:{client_ip}:{window}"
        count: int
        client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
        try:
            count = int(await client.incr(key))
            if count == 1:
                await client.expire(key, self.window_seconds + 1)
        except redis.RedisError as exc:
            if settings.ENVIRONMENT.lower() == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate-limit service is unavailable",
                ) from exc
            count = await self._increment_fallback(key)
        finally:
            await client.aclose()  # type: ignore[attr-defined]

        if count > self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {self.scope}",
                headers={"Retry-After": str(self.window_seconds)},
            )

    async def _increment_fallback(self, key: str) -> int:
        now = time.monotonic()
        async with self._fallback_lock:
            count, expires_at = self._fallback_hits.get(key, (0, now + self.window_seconds))
            if expires_at <= now:
                count, expires_at = 0, now + self.window_seconds
            count += 1
            self._fallback_hits[key] = (count, expires_at)
            return count


login_rate_limit = RateLimiter(scope="login", limit=10, window_seconds=60)
webhook_rate_limit = RateLimiter(scope="webhook", limit=60, window_seconds=60)
