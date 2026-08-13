import logging
from typing import Any

import httpx
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)


def setup_telemetry(
    service_name: str, otel_endpoint: str = "http://localhost:4317"
) -> trace.Tracer:
    resource = Resource.create({"service.name": service_name, "environment": "demo"})
    provider = TracerProvider(resource=resource)

    try:
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otel_endpoint, insecure=True))
        provider.add_span_processor(processor)
    except Exception as e:
        logger.warning(f"Could not connect to OTLP exporter at {otel_endpoint}: {e}")

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


def get_current_trace_context() -> dict[str, str]:
    """Inject current span trace context into a dictionary for downstream HTTP propagation."""
    carrier: dict[str, str] = {}
    TraceContextTextMapPropagator().inject(carrier)
    return carrier


def extract_trace_context(headers: dict[str, str]) -> Any:
    """Extract W3C traceparent context from HTTP request headers."""
    return TraceContextTextMapPropagator().extract(carrier=headers)


class TracedHTTPClient:
    """HTTP client wrapper propagating W3C traceparent headers across microservices."""

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get(self, path: str, headers: dict[str, str] | None = None) -> httpx.Response:
        req_headers = headers.copy() if headers else {}
        req_headers.update(get_current_trace_context())
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}{path}", headers=req_headers)

    async def post(
        self, path: str, json_data: Any = None, headers: dict[str, str] | None = None
    ) -> httpx.Response:
        req_headers = headers.copy() if headers else {}
        req_headers.update(get_current_trace_context())
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(f"{self.base_url}{path}", json=json_data, headers=req_headers)
