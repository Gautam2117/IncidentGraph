from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserProfile, UserRole, require_role
from app.db.models import Deployment
from app.db.session import get_db

router = APIRouter(prefix="/deployments", tags=["deployments"])


class DeploymentDTO(BaseModel):
    id: str
    service_name: str
    version: str
    environment: str
    deployed_at: str
    git_sha: str
    deployed_by: str
    status: str


@router.get("", response_model=list[DeploymentDTO])
async def list_deployments(
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> list[DeploymentDTO]:
    """Returns deployment history across services."""
    stmt = select(Deployment).order_by(Deployment.deployed_at.desc())
    result = await session.execute(stmt)
    deployments = result.scalars().all()

    # If no deployments exist, you could either return empty list or seed the DB.
    # We will just return what's in the DB.
    return [
        DeploymentDTO(
            id=str(dep.id),
            service_name=dep.service_name,
            version=dep.version,
            environment=dep.environment,
            deployed_at=dep.deployed_at.isoformat() if dep.deployed_at else "",
            git_sha=dep.git_sha or "",
            deployed_by=dep.deployed_by or "",
            status=dep.status,
        )
        for dep in deployments
    ]
