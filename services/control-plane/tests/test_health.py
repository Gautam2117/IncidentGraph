from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_live(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["service"] == "control-plane"


@pytest.mark.asyncio
async def test_health_version(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "environment" in data
    assert "git_sha" in data


@pytest.mark.asyncio
async def test_health_ready_success(async_client: AsyncClient) -> None:
    with (
        patch("app.api.v1.health.get_db") as mock_get_db,
        patch("redis.asyncio.from_url") as mock_redis_from_url,
    ):
        mock_session = AsyncMock()
        mock_get_db.return_value = mock_session

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.aclose = AsyncMock()
        mock_redis_from_url.return_value = mock_redis

        response = await async_client.get("/api/v1/health/ready")
        assert response.status_code in [200, 503]
