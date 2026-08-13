from typing import Any

from sqlalchemy import select

from app.db.models import Deployment
from app.db.session import AsyncSessionLocal
from app.tools.impl.metrics_query import SERVICE_RE
from app.tools.tool_base import BaseTool


class DeploymentsListTool(BaseTool):  # type: ignore[misc]
    name = "deployments.list"
    description = "Lists persisted service deployments and configuration changes."

    async def execute(self, service: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        if service is not None and not SERVICE_RE.fullmatch(service):
            raise ValueError("invalid_service")
        if not 1 <= limit <= 100:
            raise ValueError("invalid_limit")
        statement = select(Deployment).order_by(Deployment.deployed_at.desc()).limit(limit)
        if service:
            statement = statement.where(Deployment.service_name == service)
        async with AsyncSessionLocal() as session:
            result = await session.execute(statement)
            deployments = result.scalars().all()
        return [
            {
                "id": str(deployment.id),
                "service_name": deployment.service_name,
                "version": deployment.version,
                "environment": deployment.environment,
                "deployed_at": deployment.deployed_at.isoformat(),
                "git_sha": deployment.git_sha,
                "deployed_by": deployment.deployed_by,
                "status": deployment.status,
            }
            for deployment in deployments
        ]
