import pytest
from httpx import AsyncClient

from app.core.errors import AppError
from app.main import app


@app.get("/api/v1/test-app-error")  # type: ignore[untyped-decorator]
async def trigger_app_error() -> None:
    raise AppError(
        code="INVALID_PAYLOAD",
        message="Test error message",
        status_code=400,
        details={"field": "name"},
    )


@pytest.mark.asyncio
async def test_app_error_contract(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/test-app-error")
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_PAYLOAD"
    assert data["message"] == "Test error message"
    assert data["details"] == {"field": "name"}
    assert "timestamp" in data
    assert "request_id" in data
