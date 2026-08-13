import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.scenarios.schema import ScenarioDefinition


class ScenarioEvalMetric(BaseModel):
    scenario_id: str
    scenario_title: str
    primary_service_match: bool
    root_cause_match: bool
    causal_chain_precision: float
    causal_chain_recall: float
    unsupported_claim_rate: float
    evidence_source_count: int
    tool_choice_accuracy: float
    tool_parameter_accuracy: float
    redundant_tool_calls: int
    safe_uncertainty: bool
    remediation_match: bool
    latency_seconds: float
    total_tokens: int
    cost_usd: float
    passed: bool


class BatchEvalSummary(BaseModel):
    eval_id: str
    benchmark_mode: str
    scenario_count: int
    primary_service_accuracy: float
    root_cause_accuracy: float
    mean_causal_chain_precision: float
    mean_causal_chain_recall: float
    mean_unsupported_claim_rate: float
    mean_tool_choice_accuracy: float
    mean_tool_parameter_accuracy: float
    remediation_accuracy: float
    safe_uncertainty_rate: float
    overall_pass_rate: float
    mean_latency_seconds: float
    p50_latency_seconds: float
    p95_latency_seconds: float
    total_tokens: int
    total_cost_usd: float
    metrics: list[ScenarioEvalMetric] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "with", "from"}
    }


def _claims_match(predicted: str, expected: str) -> bool:
    predicted_tokens = _tokens(predicted)
    expected_tokens = _tokens(expected)
    if not predicted_tokens or not expected_tokens:
        return False
    return len(predicted_tokens & expected_tokens) / len(predicted_tokens | expected_tokens) >= 0.3


def _chain_scores(predicted: list[str], expected: list[str]) -> tuple[float, float]:
    matched_predicted = sum(
        1 for claim in predicted if any(_claims_match(claim, truth) for truth in expected)
    )
    matched_expected = sum(
        1 for truth in expected if any(_claims_match(claim, truth) for claim in predicted)
    )
    precision = matched_predicted / len(predicted) if predicted else 0.0
    recall = matched_expected / len(expected) if expected else 1.0
    return round(precision, 4), round(recall, 4)


def evaluate_scenario_result(
    scenario: ScenarioDefinition,
    predicted_service: str | None,
    predicted_root_cause: str | None,
    predicted_remediation: str | None,
    latency_seconds: float,
    total_tokens: int,
    cost_usd: float,
    predicted_causal_chain: list[str] | None = None,
    telemetry_evidence: list[dict[str, Any]] | None = None,
    is_conclusive: bool = False,
) -> ScenarioEvalMetric:
    """Score model output only after inference has completed.

    This is the sole evaluation boundary allowed to read scenario ground truth.
    """
    gt = scenario.ground_truth
    gt_cause = str(gt.root_cause_category)
    service_match = bool(
        predicted_service
        and (
            predicted_service.lower() == gt.primary_service.lower()
            or gt.primary_service.lower() in predicted_service.lower()
        )
    )
    cause_match = bool(
        predicted_root_cause
        and (
            predicted_root_cause.lower() in gt_cause.lower()
            or gt_cause.lower() in predicted_root_cause.lower()
        )
    )
    remediation_match = bool(
        predicted_remediation
        and predicted_remediation.lower() == gt.remediation_action_type.lower()
    )

    predicted_chain = predicted_causal_chain or []
    chain_precision, chain_recall = _chain_scores(predicted_chain, gt.causal_chain)
    unsupported_claim_rate = round(1.0 - chain_precision, 4) if predicted_chain else 0.0

    evidence = telemetry_evidence or []
    tool_names = [str(item.get("tool", "")) for item in evidence if item.get("tool")]
    known_tools = {"metrics.query", "logs.search", "traces.search", "traces.get"}
    valid_tool_count = sum(1 for name in tool_names if name in known_tools)
    tool_choice_accuracy = round(valid_tool_count / len(tool_names), 4) if tool_names else 0.0
    parameter_checks = [
        str(item.get("arguments", {}).get("service", "")).lower() == gt.primary_service.lower()
        for item in evidence
        if item.get("arguments")
    ]
    tool_parameter_accuracy = (
        round(sum(parameter_checks) / len(parameter_checks), 4) if parameter_checks else 0.0
    )
    redundant_tool_calls = len(tool_names) - len(set(tool_names))
    safe_uncertainty = (cause_match and is_conclusive) or (not cause_match and not is_conclusive)
    passed = service_match and cause_match and chain_recall >= 0.5 and unsupported_claim_rate <= 0.5

    return ScenarioEvalMetric(
        scenario_id=scenario.id,
        scenario_title=scenario.title,
        primary_service_match=service_match,
        root_cause_match=cause_match,
        causal_chain_precision=chain_precision,
        causal_chain_recall=chain_recall,
        unsupported_claim_rate=unsupported_claim_rate,
        evidence_source_count=len(evidence),
        tool_choice_accuracy=tool_choice_accuracy,
        tool_parameter_accuracy=tool_parameter_accuracy,
        redundant_tool_calls=redundant_tool_calls,
        safe_uncertainty=safe_uncertainty,
        remediation_match=remediation_match,
        latency_seconds=round(latency_seconds, 2),
        total_tokens=total_tokens,
        cost_usd=round(cost_usd, 6),
        passed=passed,
    )
