import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_api_requires_admin(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/audit/events")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_api_returns_persisted_events(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/api/v1/audit/events?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
