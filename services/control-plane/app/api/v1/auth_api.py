from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    UserProfile,
    UserRole,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.core.rate_limit import login_rate_limit
from app.db.models.audit_models import AuditEvent
from app.db.models.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


async def _record_login_audit(
    session: AsyncSession,
    username: str,
    success: bool,
) -> None:
    session.add(
        AuditEvent(
            actor=username,
            action="auth.login.success" if success else "auth.login.failure",
            resource_type="user",
            resource_id=username,
            details={"success": success},
        )
    )
    await session.commit()


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    _rate_limit: None = Depends(login_rate_limit),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate against the PostgreSQL user store and issue an expiring JWT."""
    normalized = req.username.strip().lower()
    demo_email = f"{normalized}@incidentgraph.dev"
    result = await session.execute(
        select(User).where(or_(User.email == normalized, User.email == demo_email))
    )
    user = result.scalar_one_or_none()
    if (
        user is None
        or not user.is_active
        or not verify_password(req.password, user.hashed_password)
    ):
        await _record_login_audit(session, normalized, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    role = UserRole(str(user.role))
    token = create_access_token(username=user.email, role=role)
    await _record_login_audit(session, user.email, success=True)
    return TokenResponse(
        access_token=token,
        role=role.value,
        username=user.email.split("@", maxsplit=1)[0],
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Returns profile for the authenticated, active database user."""
    return user
