import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    UserProfile,
    UserRole,
    create_access_token,
    hash_password,
    require_role,
    verify_password,
    verify_token,
)
from app.db.models.models import User


def test_password_hashing_and_verification() -> None:
    pw = "SuperSecretPassword123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_creation_and_verification() -> None:
    token = create_access_token("admin_user", UserRole.ADMIN)
    token_data = verify_token(token)

    assert token_data.username == "admin_user"
    assert token_data.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_login_api_success_and_failure(async_client: AsyncClient) -> None:
    # Success
    res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test-engineer",
            "password": "TestEngineerPassword123!",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "engineer"

    # Failure
    bad_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "test-engineer", "password": "wrongpassword"},
    )
    assert bad_res.status_code == 401


@pytest.mark.asyncio
async def test_rbac_permission_enforcement() -> None:
    admin_user = UserProfile(id="1", username="admin", role=UserRole.ADMIN, email="a@dev.com")
    viewer_user = UserProfile(id="2", username="viewer", role=UserRole.VIEWER, email="v@dev.com")

    checker = require_role(UserRole.ENGINEER)

    # Admin passes engineer requirement
    res_admin = await checker(user=admin_user)
    assert res_admin.username == "admin"

    # Viewer fails engineer requirement
    with pytest.raises(HTTPException) as exc_info:
        await checker(user=viewer_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_rbac_enforced_on_scenario_mutation_api(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"viewer-negative-{uuid.uuid4().hex}@incidentgraph.dev"
    db_session.add(
        User(
            email=email,
            hashed_password=hash_password("ViewerNegativePassword123!"),
            role=UserRole.VIEWER,
            is_active=True,
        )
    )
    await db_session.commit()
    viewer_token = create_access_token(email, UserRole.VIEWER)
    headers = {"Authorization": f"Bearer {viewer_token}"}

    read_response = await async_client.get("/api/v1/scenarios", headers=headers)
    assert read_response.status_code == 200

    mutation_response = await async_client.post(
        "/api/v1/scenarios/harmless_deployment/trigger",
        headers=headers,
    )
    assert mutation_response.status_code == 403

    unauthenticated = await async_client.get(
        "/api/v1/scenarios",
        headers={"Authorization": ""},
    )
    assert unauthenticated.status_code == 401
