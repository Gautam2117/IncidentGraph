from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserRole, create_access_token, hash_password
from app.core.config import settings
from app.db.models.models import User
from app.db.session import engine
from app.main import app

settings.ENABLE_OFFLINE_MODEL_ADAPTER = True


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    email = "test-engineer@incidentgraph.dev"
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            session.add(
                User(
                    email=email,
                    hashed_password=hash_password("TestEngineerPassword123!"),
                    full_name="Test Engineer",
                    role=UserRole.ENGINEER,
                    is_active=True,
                )
            )
            await session.commit()
    token = create_access_token(email, UserRole.ENGINEER)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest.fixture
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    email = "test-admin@incidentgraph.dev"
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            session.add(
                User(
                    email=email,
                    hashed_password=hash_password("TestAdminPassword123!"),
                    full_name="Test Admin",
                    role=UserRole.ADMIN,
                    is_active=True,
                )
            )
            await session.commit()
    token = create_access_token(email, UserRole.ADMIN)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
