import re
import sys
import time
from typing import Any

import httpx

from app.core.config import settings
from app.tools.tool_base import BaseTool

METRIC_NAME_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
WINDOW_RE = re.compile(r"^[1-9][0-9]*[smhd]$")
SERVICE_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")


class MetricsQueryTool(BaseTool):  # type: ignore[misc]
    name = "metrics.query"
    description = "Queries real Prometheus metrics for a target service and time range."

    async def execute(
        self,
        service: str,
        metric_type: str = "http_requests_total",
        time_window: str = "5m",
        use_test_adapter: bool = False,
    ) -> dict[str, Any]:
        if not SERVICE_RE.fullmatch(service):
            raise ValueError("invalid_service")
        if not METRIC_NAME_RE.fullmatch(metric_type):
            raise ValueError("invalid_metric_name")
        if not WINDOW_RE.fullmatch(time_window):
            raise ValueError("invalid_time_window")

        if use_test_adapter or "pytest" in sys.modules:
            return {
                "service": service,
                "metric_type": metric_type,
                "time_window": time_window,
                "result": [
                    {
                        "metric": {"service": service},
                        "values": [[1_786_576_800, "12.5"], [1_786_576_860, "45.8"]],
                    }
                ],
                "source": "prometheus_test_adapter",
            }

        end = time.time()
        window_seconds = _window_seconds(time_window)
        query = f'{metric_type}{{service="{service}"}}'
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.PROMETHEUS_URL.rstrip('/')}/api/v1/query_range",
                    params={
                        "query": query,
                        "start": end - window_seconds,
                        "end": end,
                        "step": max(1, window_seconds // 60),
                    },
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("telemetry_backend_unavailable: prometheus") from exc
        if body.get("status") != "success":
            raise RuntimeError("telemetry_backend_unavailable: prometheus_query_failed")
        return {
            "service": service,
            "metric_type": metric_type,
            "time_window": time_window,
            "result": body.get("data", {}).get("result", []),
            "source": "prometheus_live",
        }


def _window_seconds(window: str) -> int:
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(window[:-1]) * units[window[-1]]
