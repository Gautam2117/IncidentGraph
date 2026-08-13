import pytest
from httpx import AsyncClient

from app.observability.ai_metrics import (
    get_ai_metrics_summary,
    record_token_usage,
    record_tool_execution,
)
from app.observability.tracer import (
    redact_sensitive_payload,
    trace_agent_node,
    trace_tool_execution,
)


def test_redact_sensitive_payload() -> None:
    raw_payload = {
        "service": "inventory",
        "api_key": "secret_abc_123",
        "nested": {
            "password": "my_db_password",
            "normal_field": "public_data",
        },
        "authorization_token": "Bearer token_xyz",
    }

    sanitized = redact_sensitive_payload(raw_payload)

    assert sanitized["service"] == "inventory"
    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["password"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["normal_field"] == "public_data"
    assert sanitized["authorization_token"] == "[REDACTED_SECRET]"


@pytest.mark.asyncio
async def test_otel_tracer_spans() -> None:
    async with trace_agent_node("telemetry_investigator_node", incident_id="inc_obs_001") as span:
        assert span is not None

    async with trace_tool_execution(
        "metrics.query", {"service": "inventory", "api_key": "123"}
    ) as span:
        assert span is not None


def test_prometheus_metrics_recording() -> None:
    record_token_usage(
        provider="fake",
        model="fake-model",
        prompt_tokens=100,
        completion_tokens=50,
        cost_usd=0.0001,
    )
    record_tool_execution(tool_name="metrics.query", duration_seconds=0.05, success=True)

    summary = get_ai_metrics_summary()
    assert summary["prompt_tokens"] >= 100
    assert summary["completion_tokens"] >= 50
    assert summary["total_cost_usd"] > 0
    assert summary["tool_calls_count"] >= 1


@pytest.mark.asyncio
async def test_observability_api_endpoint(async_client: AsyncClient) -> None:
    res = await async_client.get("/api/v1/observability/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_tokens" in data
    assert "total_cost_usd" in data
