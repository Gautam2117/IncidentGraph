from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.models import User
from app.db.session import get_db

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ph = PasswordHasher()

security = HTTPBearer(auto_error=False)


class UserRole(StrEnum):
    VIEWER = "viewer"
    ENGINEER = "engineer"
    ADMIN = "admin"


class UserProfile(BaseModel):
    id: str
    username: str
    role: UserRole
    email: str


class TokenData(BaseModel):
    username: str
    role: UserRole
    exp: datetime


def hash_password(password: str) -> str:
    """Generates a secure Argon2id hash of the password."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(username: str, role: UserRole) -> str:
    """Creates a standard JWT token string."""
    exp = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "role": role.value,
        "exp": exp,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role_str: str | None = payload.get("role")
        exp_ts: int | None = payload.get("exp")

        if username is None or role_str is None or exp_ts is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        exp = datetime.fromtimestamp(exp_ts, tz=UTC)
        return TokenData(username=username, role=UserRole(role_str), exp=exp)

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format or signature",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> UserProfile:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required",
        )

    token_data = verify_token(credentials.credentials)
    result = await session.execute(select(User).where(User.email == token_data.username))
    db_user = result.scalar_one_or_none()
    if db_user is None or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or no longer exists",
        )
    return UserProfile(
        id=str(db_user.id),
        username=db_user.email.split("@", maxsplit=1)[0],
        role=UserRole(str(db_user.role)),
        email=db_user.email,
    )


def require_role(min_role: UserRole) -> Any:
    role_weights = {UserRole.VIEWER: 1, UserRole.ENGINEER: 2, UserRole.ADMIN: 3}

    async def role_checker(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if role_weights[user.role] < role_weights[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user.role}' lacks required permission level '{min_role}'",
            )
        return user

    return role_checker
