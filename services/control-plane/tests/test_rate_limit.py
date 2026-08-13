import pytest
from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError
from starlette.requests import Request

from app.core.rate_limit import RateLimiter


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/login",
            "headers": [],
            "client": ("192.0.2.10", 12345),
        }
    )


@pytest.mark.asyncio
async def test_development_rate_limit_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unavailable(*_args: object, **_kwargs: object) -> int:
        raise RedisConnectionError("redis unavailable")

    limiter = RateLimiter(scope="test", limit=2, window_seconds=60)
    monkeypatch.setattr("redis.asyncio.client.Redis.incr", unavailable)
    await limiter(_request())
    await limiter(_request())
    with pytest.raises(HTTPException) as exc_info:
        await limiter(_request())
    assert exc_info.value.status_code == 429
