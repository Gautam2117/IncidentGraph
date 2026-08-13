"""Idempotently create the first administrator from deployment secrets."""

import asyncio
import os

from sqlalchemy import select

from app.core.auth import hash_password
from app.db.models.models import User, UserRole
from app.db.session import AsyncSessionLocal


async def bootstrap_admin() -> None:
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    full_name = os.environ.get("BOOTSTRAP_ADMIN_FULL_NAME", "IncidentGraph Administrator").strip()
    if not email or "@" not in email:
        raise SystemExit("BOOTSTRAP_ADMIN_EMAIL must be a valid email address")
    if len(password) < 16:
        raise SystemExit("BOOTSTRAP_ADMIN_PASSWORD must contain at least 16 characters")

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(User).where(User.email == email))
        if existing is not None:
            if existing.role != UserRole.ADMIN:
                raise SystemExit("Refusing to overwrite an existing non-admin account")
            print(f"Administrator {email} already exists; no change required")
            return
        session.add(
            User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
        await session.commit()
        print(f"Created administrator {email}")


if __name__ == "__main__":
    asyncio.run(bootstrap_admin())
