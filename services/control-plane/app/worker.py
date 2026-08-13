"""Celery worker entrypoint for durable, bounded background operations."""

import asyncio
from typing import Any, cast

from celery import Celery

from app.agent.agent_runner import execute_investigation
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.eval.eval_runner import BenchmarkMode, run_batch_eval

celery_app = Celery("incidentgraph", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=1_740,
    task_time_limit=1_800,
    result_expires=86_400,
)


async def _execute_investigation(incident_id: str) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        state = await execute_investigation(session, incident_id)
        return cast(dict[str, Any], state.model_dump(mode="json"))


@celery_app.task(name="incidentgraph.run_investigation")  # type: ignore[untyped-decorator]
def run_investigation_task(incident_id: str) -> dict[str, Any]:
    """Run an investigation in a worker process with a fresh DB session."""
    return asyncio.run(_execute_investigation(incident_id))


async def _execute_evaluation(
    scenario_ids: list[str] | None, benchmark_mode: BenchmarkMode
) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        summary = await run_batch_eval(
            session,
            scenarios_filter=scenario_ids,
            benchmark_mode=benchmark_mode,
            export_json=True,
        )
        return cast(dict[str, Any], summary.model_dump(mode="json"))


@celery_app.task(name="incidentgraph.run_evaluation")  # type: ignore[untyped-decorator]
def run_evaluation_task(
    scenario_ids: list[str] | None = None, benchmark_mode: BenchmarkMode = "live"
) -> dict[str, Any]:
    """Run an offline or live benchmark batch outside the API process."""
    return asyncio.run(_execute_evaluation(scenario_ids, benchmark_mode))
