import sys
from typing import Any

import httpx

from app.scenarios.runtime import get_service_url
from app.tools.impl.metrics_query import SERVICE_RE
from app.tools.tool_base import BaseTool


class ConfigsGetSafeSnapshotTool(BaseTool):  # type: ignore[misc]
    name = "configs.get_safe_snapshot"
    description = "Retrieves a bounded, non-secret service version/configuration snapshot."

    async def execute(self, service: str, use_test_adapter: bool = False) -> dict[str, Any]:
        if not SERVICE_RE.fullmatch(service):
            raise ValueError("invalid_service")
        if use_test_adapter or "pytest" in sys.modules:
            return {
                "service": service,
                "environment": "test",
                "version": "test-adapter",
                "source": "config_test_adapter",
            }
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{get_service_url(service)}/version")
                response.raise_for_status()
                version = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("configuration_backend_unavailable") from exc
        return {
            "service": service,
            "environment": "demo",
            "version": version.get("version"),
            "source": "service_version_endpoint",
        }
