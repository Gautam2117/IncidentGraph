from datetime import UTC, datetime
from typing import Any, cast

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: str = Field(default="ok")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    service: str = Field(default=settings.OTEL_SERVICE_NAME)


class ComponentHealth(BaseModel):
    status: str
    message: str | None = None


class ReadinessResponse(BaseModel):
    status: str = Field(default="ready")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    components: dict[str, ComponentHealth]


class VersionResponse(BaseModel):
    name: str = Field(default=settings.PROJECT_NAME)
    version: str = Field(default=settings.VERSION)
    environment: str = Field(default=settings.ENVIRONMENT)
    git_sha: str = Field(default=settings.GIT_SHA)


@router.get("/live", response_model=LivenessResponse)
async def health_live() -> LivenessResponse:
    """Liveness probe: verifies process is running."""
    return LivenessResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
async def health_ready(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Readiness probe: verifies database, redis and external system dependencies."""
    components: dict[str, ComponentHealth] = {}
    is_ready = True

    # Check PostgreSQL DB
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = ComponentHealth(status="ok", message="PostgreSQL connected")
    except Exception as e:
        is_ready = False
        components["database"] = ComponentHealth(
            status="error", message=f"Database check failed: {str(e)}"
        )

    # Check Redis
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        await redis_client.ping()
        await cast(Any, redis_client).aclose()
        components["redis"] = ComponentHealth(status="ok", message="Redis connected")
    except Exception as e:
        is_ready = False
        components["redis"] = ComponentHealth(
            status="error", message=f"Redis check failed: {str(e)}"
        )

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    overall_status = "ready" if is_ready else "unhealthy"

    response_data = ReadinessResponse(
        status=overall_status,
        components=components,
    )

    return JSONResponse(status_code=status_code, content=response_data.model_dump())


@router.get("/version", response_model=VersionResponse)
async def health_version() -> VersionResponse:
    """Version probe: exposes system version, environment, and SHA."""
    return VersionResponse()
