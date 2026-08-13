import pytest
from httpx import AsyncClient

from app.scenarios.registry import get_scenario, list_scenarios
from app.scenarios.schema import ScenarioRunState


def test_scenario_registry_completeness() -> None:
    scenarios = list_scenarios()
    assert len(scenarios) >= 36, f"Expected >= 36 scenarios, found {len(scenarios)}"

    scenario_ids = {sc.id for sc in scenarios}
    mandatory_ids = [
        "db_pool_exhaustion",
        "slow_query_missing_index",
        "n_plus_one_query",
        "db_lock_contention",
        "bad_deployment",
        "bad_configuration",
        "payment_latency",
        "payment_5xx_burst",
        "payment_throttling",
        "auth_latency",
        "auth_errors",
        "auth_config_failure",
        "inventory_timeout",
        "inventory_stale_response",
        "gateway_ratelimit_config",
        "retry_storm",
        "cpu_saturation",
        "memory_pressure",
        "redis_unavailable",
        "redis_latency",
        "queue_backlog",
        "notification_worker_failure",
        "dns_network_simulation",
        "partial_dependency_failure",
        "cascading_failure",
        "timeout_regression",
        "circuit_breaker_open",
        "misleading_correlated_signal",
        "multi_weak_signal",
        "insufficient_evidence",
        "recovered_before_investigation",
        "historical_postmortem_repeat",
        "telemetry_gap",
        "harmless_deployment",
        "prompt_injection_runbook",
        "tool_timeout_during_investigation",
    ]
    for required_id in mandatory_ids:
        assert required_id in scenario_ids, f"Missing required scenario: {required_id}"


def test_ground_truth_isolation() -> None:
    scenario = get_scenario("db_pool_exhaustion")
    assert scenario is not None
    safe_data = scenario.get_safe_metadata()
    assert "ground_truth" not in safe_data
    assert "primary_service" not in safe_data
    assert "remediation_action_type" not in safe_data
    assert safe_data["id"] == "db_pool_exhaustion"
    assert safe_data["title"] == "Database Connection Pool Exhaustion"


@pytest.mark.asyncio
async def test_scenario_api_list_and_detail(async_client: AsyncClient) -> None:
    list_res = await async_client.get("/api/v1/scenarios")
    assert list_res.status_code == 200
    scenarios = list_res.json()
    assert len(scenarios) >= 36

    for sc in scenarios:
        assert "ground_truth" not in sc

    detail_res = await async_client.get("/api/v1/scenarios/db_pool_exhaustion")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "ground_truth" not in detail
    assert detail["id"] == "db_pool_exhaustion"


@pytest.mark.asyncio
async def test_scenario_trigger_and_reset(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import AsyncMock, MagicMock

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_res

    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client_instance

    monkeypatch.setattr("app.scenarios.runner.httpx.AsyncClient", mock_client_class)

    res = await async_client.post("/api/v1/scenarios/harmless_deployment/trigger")
    assert res.status_code == 200
    run = res.json()
    assert run["scenario_id"] == "harmless_deployment"
    assert run["state"] in [ScenarioRunState.RUNNING, ScenarioRunState.TRIGGERED]
    assert run["fault_ack"] is True
    assert run["probe_status_code"] == 200

    latest_res = await async_client.get("/api/v1/scenarios/harmless_deployment/run")
    assert latest_res.status_code == 200
    assert latest_res.json()["run_id"] == run["run_id"]

    inject_call = mock_client_instance.post.await_args_list[0]
    assert inject_call.kwargs["params"]["endpoint"] == "/inventory/reserve"
    assert inject_call.kwargs["json"]["scenario_id"] == "harmless_deployment"

    reset_res = await async_client.post("/api/v1/scenarios/harmless_deployment/reset")
    assert reset_res.status_code == 200
    reset_run = reset_res.json()
    assert reset_run["state"] == ScenarioRunState.CLEANED_UP

    missing_res = await async_client.get("/api/v1/scenarios/no-such-scenario/run")
    assert missing_res.status_code == 404
