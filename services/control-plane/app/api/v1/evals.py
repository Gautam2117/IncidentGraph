from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserProfile, UserRole, require_role
from app.db.session import get_db
from app.eval.eval_runner import (
    BenchmarkMode,
    get_eval_summary,
    get_latest_eval_summary,
    list_eval_summaries,
    run_batch_eval,
)
from app.eval.metrics import BatchEvalSummary

router = APIRouter(prefix="/evals", tags=["evals"])


class RunBatchEvalRequest(BaseModel):
    scenarios: list[str] | None = None
    export_json: bool = True
    benchmark_mode: BenchmarkMode = "live"


@router.post("/run", response_model=BatchEvalSummary, status_code=status.HTTP_200_OK)
async def trigger_batch_evaluation(
    req: RunBatchEvalRequest,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> BatchEvalSummary:
    """Triggers an evaluation benchmark run across scenarios."""
    return await run_batch_eval(
        session=session,
        scenarios_filter=req.scenarios,
        export_json=req.export_json,
        benchmark_mode=req.benchmark_mode,
    )


@router.get("/latest", response_model=BatchEvalSummary)
async def get_latest_evaluation(
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> BatchEvalSummary:
    """Retrieves latest evaluation benchmark summary."""
    summary = await get_latest_eval_summary(session)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evaluation run has been completed yet. Trigger POST /api/v1/evals/run first.",
        )
    return summary


@router.get("", response_model=list[BatchEvalSummary])
async def list_evaluations(
    limit: int = 20,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> list[BatchEvalSummary]:
    summaries = await list_eval_summaries(session, limit=max(1, min(limit, 100)))
    return cast(list[BatchEvalSummary], summaries)


@router.get("/{eval_id}", response_model=BatchEvalSummary)
async def get_evaluation(
    eval_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> BatchEvalSummary:
    summary = await get_eval_summary(session, eval_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Completed evaluation '{eval_id}' was not found",
        )
    return summary
