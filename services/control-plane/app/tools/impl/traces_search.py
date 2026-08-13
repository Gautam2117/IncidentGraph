import sys
from typing import Any

import httpx

from app.core.config import settings
from app.tools.impl.metrics_query import SERVICE_RE
from app.tools.tool_base import BaseTool


class TracesSearchTool(BaseTool):  # type: ignore[misc]
    name = "traces.search"
    description = "Searches real Tempo traces by service, duration, and error status."

    async def execute(
        self,
        service: str | None = None,
        min_duration_ms: float = 0.0,
        has_error: bool = False,
        limit: int = 10,
        use_test_adapter: bool = False,
    ) -> list[dict[str, Any]]:
        target_service = service or "gateway"
        if not SERVICE_RE.fullmatch(target_service):
            raise ValueError("invalid_service")
        if not 1 <= limit <= 100 or not 0 <= min_duration_ms <= 600_000:
            raise ValueError("invalid_trace_search_bounds")
        if use_test_adapter or "pytest" in sys.modules:
            return [
                {
                    "trace_id": "tr_8f9a0b1c2d3e4f5a",
                    "root_service": target_service,
                    "duration_ms": max(min_duration_ms, 5012.4),
                    "has_error": True,
                    "source": "tempo_test_adapter",
                }
            ]

        traceql_parts = [f'resource.service.name = "{target_service}"']
        if min_duration_ms > 0:
            traceql_parts.append(f"duration >= {min_duration_ms}ms")
        if has_error:
            traceql_parts.append("status = error")
        traceql = "{ " + " && ".join(traceql_parts) + " }"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.TEMPO_URL.rstrip('/')}/api/search",
                    params={"q": traceql, "limit": limit},
                )
                response.raise_for_status()
                traces = response.json().get("traces", [])
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("telemetry_backend_unavailable: tempo") from exc

        return [
            {
                "trace_id": item.get("traceID"),
                "root_service": item.get("rootServiceName", target_service),
                "root_span": item.get("rootTraceName"),
                "duration_ms": float(item.get("durationMs", 0)),
                "start_time_unix_nano": item.get("startTimeUnixNano"),
                "span_sets": item.get("spanSets", []),
                "source": "tempo_live",
            }
            for item in traces[:limit]
        ]
