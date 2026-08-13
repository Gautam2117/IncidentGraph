import os
import time
import uuid
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_investigation_workflow
from app.agent.state import InvestigationState
from app.db.models.eval_models import EvaluationResult, EvaluationRun
from app.eval.exporter import export_eval_result_json
from app.eval.metrics import BatchEvalSummary, ScenarioEvalMetric, evaluate_scenario_result
from app.scenarios.registry import list_scenarios
from app.scenarios.runner import reset_scenario, trigger_scenario
from app.services.incident_service import CreateIncidentRequest, create_incident

BenchmarkMode = Literal["offline", "live"]

_latest_batch_summary: BatchEvalSummary | None = None


async def run_scenario_eval(
    session: AsyncSession, scenario_id: str, benchmark_mode: BenchmarkMode = "live"
) -> ScenarioEvalMetric:
    scenarios = list_scenarios()
    sc_match = [s for s in scenarios if s.id == scenario_id]
    if not sc_match:
        raise ValueError(f"Scenario '{scenario_id}' not found")
    scenario = sc_match[0]

    # Evaluation may use only model-visible scenario metadata before the run.
    # Hidden ground truth is read exclusively by evaluate_scenario_result after
    # the investigation has produced its final output.
    safe_metadata = scenario.get_safe_metadata()
    if benchmark_mode == "live":
        # A live benchmark owns the entire fault lifecycle. Reset first so a
        # previous failed run cannot contaminate this result.
        await reset_scenario(session, scenario.id)
        await trigger_scenario(session, scenario.id)

    try:
        inc = await create_incident(
            session,
            CreateIncidentRequest(
                title=f"Eval: {scenario.title}",
                severity="high",
                target_service=str(safe_metadata["target_service"]),
                scenario_id=scenario.id,
            ),
        )

        from langchain_community.callbacks.manager import get_openai_callback

        t0 = time.perf_counter()
        state = InvestigationState(
            incident_id=inc.id,
            target_service=str(safe_metadata["target_service"]),
            use_test_adapters=benchmark_mode == "offline",
        )

        with get_openai_callback() as cb:
            final_state = await run_investigation_workflow(session, state)

        duration_s = time.perf_counter() - t0

        pred_service = final_state.rca_report.primary_service if final_state.rca_report else None
        pred_cause = final_state.rca_report.root_cause_category if final_state.rca_report else None
        pred_remediation = (
            final_state.remediation_plan.steps[0].action_type
            if final_state.remediation_plan and final_state.remediation_plan.steps
            else None
        )

        return evaluate_scenario_result(
            scenario=scenario,
            predicted_service=pred_service,
            predicted_root_cause=pred_cause,
            predicted_remediation=pred_remediation,
            latency_seconds=duration_s,
            total_tokens=cb.total_tokens,
            cost_usd=cb.total_cost,
            predicted_causal_chain=(
                final_state.rca_report.causal_chain if final_state.rca_report else []
            ),
            telemetry_evidence=final_state.telemetry_evidence,
            is_conclusive=(
                final_state.rca_report.is_conclusive if final_state.rca_report else False
            ),
        )
    finally:
        if benchmark_mode == "live":
            await reset_scenario(session, scenario.id)


async def run_batch_eval(
    session: AsyncSession,
    scenarios_filter: list[str] | None = None,
    export_json: bool = True,
    benchmark_mode: BenchmarkMode = "live",
) -> BatchEvalSummary:
    global _latest_batch_summary
    scenarios = list_scenarios()
    if scenarios_filter:
        scenarios = [s for s in scenarios if s.id in scenarios_filter]

    eval_id = f"run_{uuid.uuid4().hex[:12]}"
    metrics: list[ScenarioEvalMetric] = []
    db_run = EvaluationRun(
        external_id=eval_id,
        benchmark_mode=benchmark_mode,
        commit_sha=os.getenv("GITHUB_SHA") or os.getenv("GIT_COMMIT_SHA"),
        status="running",
        total_scenarios=len(scenarios),
        passed_scenarios=0,
    )
    session.add(db_run)
    await session.commit()
    await session.refresh(db_run)
    db_run_id = db_run.id

    try:
        for sc in scenarios:
            metric = await run_scenario_eval(session, sc.id, benchmark_mode=benchmark_mode)
            metrics.append(metric)
            session.add(
                EvaluationResult(
                    run_id=db_run_id,
                    scenario_id=sc.id,
                    passed=metric.passed,
                    metrics=metric.model_dump(mode="json"),
                )
            )
            await session.commit()
    except Exception as exc:
        await session.rollback()
        failed_run = await session.get(EvaluationRun, db_run_id)
        if failed_run is None:
            raise RuntimeError("Evaluation run disappeared during execution") from exc
        failed_run.status = "failed"
        failed_run.completed_at = datetime.now(UTC)
        failed_run.summary = {
            "error_type": type(exc).__name__,
            "completed_scenarios": len(metrics),
        }
        await session.commit()
        raise

    n = len(metrics) if metrics else 1
    passed_count = sum(1 for m in metrics if m.passed)
    service_match_count = sum(1 for m in metrics if m.primary_service_match)
    cause_match_count = sum(1 for m in metrics if m.root_cause_match)
    remediation_match_count = sum(1 for m in metrics if m.remediation_match)
    latencies = sorted(m.latency_seconds for m in metrics)

    summary = BatchEvalSummary(
        eval_id=eval_id,
        benchmark_mode=benchmark_mode,
        scenario_count=len(metrics),
        primary_service_accuracy=round(service_match_count / n, 4),
        root_cause_accuracy=round(cause_match_count / n, 4),
        mean_causal_chain_precision=round(sum(m.causal_chain_precision for m in metrics) / n, 4),
        mean_causal_chain_recall=round(sum(m.causal_chain_recall for m in metrics) / n, 4),
        mean_unsupported_claim_rate=round(sum(m.unsupported_claim_rate for m in metrics) / n, 4),
        mean_tool_choice_accuracy=round(sum(m.tool_choice_accuracy for m in metrics) / n, 4),
        mean_tool_parameter_accuracy=round(sum(m.tool_parameter_accuracy for m in metrics) / n, 4),
        remediation_accuracy=round(remediation_match_count / n, 4),
        safe_uncertainty_rate=round(sum(m.safe_uncertainty for m in metrics) / n, 4),
        overall_pass_rate=round(passed_count / n, 4),
        mean_latency_seconds=round(sum(m.latency_seconds for m in metrics) / n, 2),
        p50_latency_seconds=_percentile(latencies, 0.50),
        p95_latency_seconds=_percentile(latencies, 0.95),
        total_tokens=sum(m.total_tokens for m in metrics),
        total_cost_usd=round(sum(m.cost_usd for m in metrics), 6),
        metrics=metrics,
    )

    if export_json:
        export_eval_result_json(summary)

    completed_run = await session.get(EvaluationRun, db_run_id)
    if completed_run is None:
        raise RuntimeError("Evaluation run disappeared before summary persistence")
    completed_run.status = "completed"
    completed_run.passed_scenarios = passed_count
    completed_run.summary = summary.model_dump(mode="json")
    completed_run.completed_at = datetime.now(UTC)
    await session.commit()
    _latest_batch_summary = summary
    return summary


async def get_latest_eval_summary(session: AsyncSession) -> BatchEvalSummary | None:
    result = await session.execute(
        select(EvaluationRun)
        .where(EvaluationRun.status == "completed")
        .order_by(EvaluationRun.completed_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if run and run.summary:
        return BatchEvalSummary.model_validate(run.summary)
    return _latest_batch_summary


async def get_eval_summary(session: AsyncSession, eval_id: str) -> BatchEvalSummary | None:
    result = await session.execute(
        select(EvaluationRun).where(EvaluationRun.external_id == eval_id)
    )
    run = result.scalar_one_or_none()
    if run and run.summary and run.status == "completed":
        return BatchEvalSummary.model_validate(run.summary)
    return None


async def list_eval_summaries(
    session: AsyncSession, limit: int = 20
) -> list[BatchEvalSummary]:
    result = await session.execute(
        select(EvaluationRun)
        .where(EvaluationRun.status == "completed")
        .order_by(EvaluationRun.completed_at.desc())
        .limit(limit)
    )
    summaries: list[BatchEvalSummary] = []
    for run in result.scalars().all():
        if run.summary:
            summaries.append(BatchEvalSummary.model_validate(run.summary))
    return summaries


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    index = max(0, min(len(values) - 1, int((len(values) - 1) * percentile)))
    return round(values[index], 2)
