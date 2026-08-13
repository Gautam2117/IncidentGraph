from typing import Any

from app.db.session import AsyncSessionLocal
from app.services.incident_service import list_incidents
from app.tools.impl.metrics_query import SERVICE_RE
from app.tools.tool_base import BaseTool


class IncidentsSearchHistoryTool(BaseTool):  # type: ignore[misc]
    name = "incidents.search_history"
    description = "Searches persisted historical incidents by service or severity."

    async def execute(
        self, service: str | None = None, severity: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        if service is not None and not SERVICE_RE.fullmatch(service):
            raise ValueError("invalid_service")
        if severity is not None and severity not in {"low", "medium", "high", "critical"}:
            raise ValueError("invalid_severity")
        if not 1 <= limit <= 100:
            raise ValueError("invalid_limit")
        async with AsyncSessionLocal() as session:
            incidents = await list_incidents(session, severity=severity)
        return [
            incident.model_dump(mode="json")
            for incident in incidents
            if service is None or incident.target_service == service
        ][:limit]
