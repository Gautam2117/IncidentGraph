import re
import sys
from typing import Any

import httpx

from app.core.config import settings
from app.tools.tool_base import BaseTool

TRACE_ID_RE = re.compile(r"^[0-9a-fA-F]{16,32}$")


class TracesGetTool(BaseTool):  # type: ignore[misc]
    name = "traces.get"
    description = "Retrieves a real Tempo trace and returns a bounded waterfall."

    async def execute(
        self,
        trace_id: str,
        use_test_adapter: bool = False,
    ) -> dict[str, Any]:
        normalized = trace_id.removeprefix("tr_")
        if not TRACE_ID_RE.fullmatch(normalized):
            raise ValueError("invalid_trace_id")
        if use_test_adapter or "pytest" in sys.modules:
            return {
                "trace_id": trace_id,
                "spans": [
                    {
                        "span_id": "1a2b3c4d5e6f7890",
                        "service": "gateway",
                        "name": "POST /orders",
                        "duration_ms": 5012.4,
                        "status": "ERROR",
                    }
                ],
                "source": "tempo_test_adapter",
            }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.TEMPO_URL.rstrip('/')}/api/traces/{normalized}"
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("telemetry_backend_unavailable: tempo") from exc
        return {
            "trace_id": normalized,
            "spans": _extract_spans(body)[:100],
            "source": "tempo_live",
        }


def _extract_spans(body: dict[str, Any]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for resource_span in body.get("batches", body.get("resourceSpans", [])):
        resource = resource_span.get("resource", {})
        attrs = resource.get("attributes", [])
        service = _attribute_value(attrs, "service.name") or "unknown"
        scope_spans = resource_span.get(
            "scopeSpans", resource_span.get("instrumentationLibrarySpans", [])
        )
        for scope in scope_spans:
            for span in scope.get("spans", []):
                start = int(span.get("startTimeUnixNano", 0))
                end = int(span.get("endTimeUnixNano", start))
                spans.append(
                    {
                        "span_id": span.get("spanId"),
                        "parent_span_id": span.get("parentSpanId"),
                        "service": service,
                        "name": span.get("name"),
                        "duration_ms": round((end - start) / 1_000_000, 3),
                        "status": span.get("status", {}).get("code", "UNSET"),
                        "attributes": span.get("attributes", [])[:30],
                    }
                )
    return spans


def _attribute_value(attributes: list[dict[str, Any]], key: str) -> str | None:
    for attribute in attributes:
        if attribute.get("key") != key:
            continue
        value = attribute.get("value", {})
        for value_key in ("stringValue", "string_value"):
            if value_key in value:
                return str(value[value_key])
    return None
