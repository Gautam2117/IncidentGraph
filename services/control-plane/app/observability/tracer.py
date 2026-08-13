import os
import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode


def setup_telemetry(app: FastAPI, service_name: str = "control-plane") -> None:
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"), insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


tracer = trace.get_tracer("incidentgraph.ai_observability", "1.0.0")

SENSITIVE_KEYS_REGEX = re.compile(
    r"(api_?key|token|auth|password|secret|credential)", re.IGNORECASE
)


def redact_sensitive_payload(payload: Any) -> Any:
    """Sanitizes dictionary payloads by redacting sensitive keys."""
    if isinstance(payload, dict):
        sanitized = {}
        for k, v in payload.items():
            if SENSITIVE_KEYS_REGEX.search(str(k)):
                sanitized[k] = "[REDACTED_SECRET]"
            else:
                sanitized[k] = redact_sensitive_payload(v)
        return sanitized
    elif isinstance(payload, list):
        return [redact_sensitive_payload(item) for item in payload]
    return payload


@asynccontextmanager
async def trace_agent_node(node_name: str, incident_id: str) -> AsyncGenerator[trace.Span, None]:
    with tracer.start_as_current_span(f"agent.node.{node_name}") as span:
        span.set_attribute("incident.id", incident_id)
        span.set_attribute("agent.node.name", node_name)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@asynccontextmanager
async def trace_tool_execution(
    tool_name: str, params: dict[str, Any]
) -> AsyncGenerator[trace.Span, None]:
    sanitized_params = redact_sensitive_payload(params)
    with tracer.start_as_current_span(f"tool.execution.{tool_name}") as span:
        span.set_attribute("tool.name", tool_name)
        span.set_attribute("tool.params", str(sanitized_params))
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@asynccontextmanager
async def trace_model_generation(
    provider_name: str, model_name: str
) -> AsyncGenerator[trace.Span, None]:
    with tracer.start_as_current_span(f"llm.generate.{provider_name}") as span:
        span.set_attribute("llm.provider", provider_name)
        span.set_attribute("llm.model", model_name)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
