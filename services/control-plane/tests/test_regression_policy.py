from copy import deepcopy

from app.eval.metrics import BatchEvalSummary
from app.eval.regression import evaluate_regression


def _summary() -> BatchEvalSummary:
    return BatchEvalSummary(
        eval_id="clean-baseline",
        benchmark_mode="live",
        scenario_count=10,
        primary_service_accuracy=0.9,
        root_cause_accuracy=0.8,
        mean_causal_chain_precision=0.8,
        mean_causal_chain_recall=0.75,
        mean_unsupported_claim_rate=0.1,
        mean_tool_choice_accuracy=0.9,
        mean_tool_parameter_accuracy=0.85,
        remediation_accuracy=0.8,
        safe_uncertainty_rate=1.0,
        overall_pass_rate=0.8,
        mean_latency_seconds=8.0,
        p50_latency_seconds=7.0,
        p95_latency_seconds=12.0,
        total_tokens=10_000,
        total_cost_usd=1.0,
    )


def test_multi_metric_regression_policy_rejects_degraded_candidate() -> None:
    baseline = _summary()
    candidate = deepcopy(baseline)
    candidate.eval_id = "degraded"
    candidate.root_cause_accuracy = 0.6
    candidate.mean_unsupported_claim_rate = 0.3
    candidate.mean_tool_parameter_accuracy = 0.6
    candidate.safe_uncertainty_rate = 0.7
    decision = evaluate_regression(baseline, candidate)
    assert decision.passed is False
    assert any("root_cause_accuracy" in failure for failure in decision.failures)
    assert any("unsupported_claim" in failure for failure in decision.failures)
    assert any("safe_uncertainty" in failure for failure in decision.failures)


def test_multi_metric_regression_policy_accepts_equivalent_candidate() -> None:
    baseline = _summary()
    candidate = deepcopy(baseline)
    candidate.eval_id = "recovered"
    assert evaluate_regression(baseline, candidate).passed is True
