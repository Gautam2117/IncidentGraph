import os

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.eval.eval_runner import run_batch_eval, run_scenario_eval
from app.eval.metrics import evaluate_scenario_result
from app.scenarios.registry import list_scenarios


@pytest.mark.asyncio
async def test_scenario_eval_metric_computation(db_session: AsyncSession) -> None:
    scenarios = list_scenarios()
    assert len(scenarios) >= 36

    metric = await run_scenario_eval(db_session, "db_pool_exhaustion", benchmark_mode="offline")
    assert metric.scenario_id == "db_pool_exhaustion"
    assert metric.primary_service_match is True
    # Generic test telemetry intentionally contains no scenario answer. Exact
    # root-cause success here would be evidence of benchmark leakage.
    assert metric.root_cause_match is False
    assert metric.passed is False


@pytest.mark.asyncio
async def test_batch_eval_runner(db_session: AsyncSession) -> None:
    # Run evaluation across first 3 scenarios
    summary = await run_batch_eval(
        db_session,
        scenarios_filter=["db_pool_exhaustion", "slow_query_missing_index", "n_plus_one_query"],
        export_json=True,
        benchmark_mode="offline",
    )

    assert summary.scenario_count == 3
    assert summary.primary_service_accuracy == 1.0
    assert summary.benchmark_mode == "offline"
    assert 0.0 <= summary.root_cause_accuracy <= 1.0
    assert 0.0 <= summary.overall_pass_rate <= 1.0
    assert len(summary.metrics) == 3

    # Verify JSON export file exists in eval-results/
    assert os.path.exists(f"eval-results/eval_{summary.eval_id}.json")


def test_metric_scorer_rewards_supported_known_result() -> None:
    scenario = next(item for item in list_scenarios() if item.id == "db_pool_exhaustion")
    truth = scenario.ground_truth
    metric = evaluate_scenario_result(
        scenario=scenario,
        predicted_service=truth.primary_service,
        predicted_root_cause=str(truth.root_cause_category),
        predicted_remediation=truth.remediation_action_type,
        predicted_causal_chain=truth.causal_chain,
        telemetry_evidence=[
            {
                "tool": "metrics.query",
                "arguments": {"service": truth.primary_service},
                "data": {},
            }
        ],
        is_conclusive=True,
        latency_seconds=1.0,
        total_tokens=100,
        cost_usd=0.01,
    )
    assert metric.passed is True
    assert metric.causal_chain_precision == 1.0
    assert metric.causal_chain_recall == 1.0
    assert metric.unsupported_claim_rate == 0.0
    assert metric.tool_parameter_accuracy == 1.0


@pytest.mark.asyncio
async def test_eval_api_endpoints(async_client: AsyncClient) -> None:
    run_res = await async_client.post(
        "/api/v1/evals/run",
        json={
            "scenarios": ["db_pool_exhaustion"],
            "export_json": False,
            "benchmark_mode": "offline",
        },
    )
    assert run_res.status_code == 200
    data = run_res.json()
    assert data["scenario_count"] == 1
    assert data["benchmark_mode"] == "offline"

    latest_res = await async_client.get("/api/v1/evals/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["eval_id"] == data["eval_id"]

    list_res = await async_client.get("/api/v1/evals?limit=5")
    assert list_res.status_code == 200
    assert any(item["eval_id"] == data["eval_id"] for item in list_res.json())

    detail_res = await async_client.get(f"/api/v1/evals/{data['eval_id']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["benchmark_mode"] == "offline"

    missing_res = await async_client.get("/api/v1/evals/not-a-real-evaluation")
    assert missing_res.status_code == 404
