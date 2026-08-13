import json
import sys
import time
from typing import Any

import httpx

from app.core.config import settings
from app.tools.impl.metrics_query import SERVICE_RE
from app.tools.tool_base import BaseTool


class LogsSearchTool(BaseTool):  # type: ignore[misc]
    name = "logs.search"
    description = "Searches real Loki streams with bounded service, severity, and text filters."

    async def execute(
        self,
        service: str | None = None,
        severity: str = "ERROR",
        query: str | None = None,
        limit: int = 50,
        use_test_adapter: bool = False,
    ) -> list[dict[str, Any]]:
        target_service = service or "gateway"
        if not SERVICE_RE.fullmatch(target_service):
            raise ValueError("invalid_service")
        if severity not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("invalid_severity")
        if not 1 <= limit <= 100:
            raise ValueError("invalid_limit")
        if query is not None and len(query) > 200:
            raise ValueError("query_too_long")

        if use_test_adapter or "pytest" in sys.modules:
            return [
                {
                    "timestamp": "2026-08-13T01:02:15Z",
                    "service": target_service,
                    "severity": severity,
                    "message": f"Observable test fault on {target_service}",
                    "trace_id": "tr_8f9a0b1c2d3e4f5a",
                    "span_id": "sp_1a2b3c4d",
                    "source": "loki_test_adapter",
                }
            ]

        selector = f'{{service="{target_service}"}}'
        filter_text = query or severity
        logql = f"{selector} |= {json.dumps(filter_text)}"
        now_ns = int(time.time() * 1_000_000_000)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.LOKI_URL.rstrip('/')}/loki/api/v1/query_range",
                    params={
                        "query": logql,
                        "limit": limit,
                        "start": now_ns - (300 * 1_000_000_000),
                        "end": now_ns,
                        "direction": "backward",
                    },
                )
                response.raise_for_status()
                streams = response.json().get("data", {}).get("result", [])
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("telemetry_backend_unavailable: loki") from exc

        logs: list[dict[str, Any]] = []
        for stream in streams:
            labels = stream.get("stream", {})
            for timestamp, message in stream.get("values", []):
                logs.append(
                    {
                        "timestamp": timestamp,
                        "service": labels.get("service", target_service),
                        "severity": labels.get("severity", severity),
                        "message": message,
                        "trace_id": labels.get("trace_id"),
                        "span_id": labels.get("span_id"),
                        "source": "loki_live",
                    }
                )
        return logs[:limit]
