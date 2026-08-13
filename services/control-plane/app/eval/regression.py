from pydantic import BaseModel, Field

from app.eval.metrics import BatchEvalSummary


class RegressionPolicy(BaseModel):
    max_accuracy_drop: float = 0.03
    max_quality_drop: float = 0.05
    max_unsupported_claim_increase: float = 0.02
    max_p95_latency_increase_ratio: float = 0.25
    max_cost_increase_ratio: float = 0.25


class RegressionDecision(BaseModel):
    passed: bool
    failures: list[str] = Field(default_factory=list)


def evaluate_regression(
    baseline: BatchEvalSummary,
    candidate: BatchEvalSummary,
    policy: RegressionPolicy | None = None,
) -> RegressionDecision:
    """Compare like-for-like benchmark runs across quality, safety, and efficiency."""
    active = policy or RegressionPolicy()
    failures: list[str] = []
    if baseline.benchmark_mode != candidate.benchmark_mode:
        failures.append("benchmark_mode changed")
    if baseline.scenario_count != candidate.scenario_count:
        failures.append("scenario_count changed")

    accuracy_metrics = (
        "primary_service_accuracy",
        "root_cause_accuracy",
        "remediation_accuracy",
        "overall_pass_rate",
    )
    quality_metrics = (
        "mean_causal_chain_precision",
        "mean_causal_chain_recall",
        "mean_tool_choice_accuracy",
        "mean_tool_parameter_accuracy",
        "safe_uncertainty_rate",
    )
    for name in accuracy_metrics:
        drop = float(getattr(baseline, name)) - float(getattr(candidate, name))
        if drop > active.max_accuracy_drop:
            failures.append(f"{name} dropped by {drop:.4f}")
    for name in quality_metrics:
        drop = float(getattr(baseline, name)) - float(getattr(candidate, name))
        if drop > active.max_quality_drop:
            failures.append(f"{name} dropped by {drop:.4f}")

    unsupported_increase = (
        candidate.mean_unsupported_claim_rate - baseline.mean_unsupported_claim_rate
    )
    if unsupported_increase > active.max_unsupported_claim_increase:
        failures.append(f"mean_unsupported_claim_rate increased by {unsupported_increase:.4f}")

    if baseline.p95_latency_seconds > 0:
        latency_ratio = candidate.p95_latency_seconds / baseline.p95_latency_seconds - 1.0
        if latency_ratio > active.max_p95_latency_increase_ratio:
            failures.append(f"p95_latency_seconds increased by {latency_ratio:.1%}")
    if baseline.total_cost_usd > 0:
        cost_ratio = candidate.total_cost_usd / baseline.total_cost_usd - 1.0
        if cost_ratio > active.max_cost_increase_ratio:
            failures.append(f"total_cost_usd increased by {cost_ratio:.1%}")

    return RegressionDecision(passed=not failures, failures=failures)
