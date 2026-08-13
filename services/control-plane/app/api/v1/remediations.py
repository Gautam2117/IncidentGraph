from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent_runner import get_investigation_checkpoint
from app.core.auth import UserProfile, UserRole, require_role
from app.db.session import get_db
from app.remediation.executor import RemediationExecutionResult, execute_remediation_plan
from app.remediation.review import (
    HumanReviewDecision,
    HumanReviewRecord,
    submit_human_review,
)

router = APIRouter(prefix="/remediations", tags=["remediations"])


class SubmitReviewRequest(BaseModel):
    incident_id: str
    decision: HumanReviewDecision
    comments: str | None = None


class ExecuteRemediationRequest(BaseModel):
    incident_id: str
    dry_run: bool = False


@router.post("/{plan_id}/review", response_model=HumanReviewRecord)
async def review_remediation_plan(
    plan_id: str,
    req: SubmitReviewRequest,
    session: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> HumanReviewRecord:
    """Submits a human approval, rejection, or request-more-evidence decision."""
    return await submit_human_review(
        session=session,
        plan_id=plan_id,
        incident_id=req.incident_id,
        decision=req.decision,
        reviewer=user.email,
        comments=req.comments,
    )


@router.post("/{plan_id}/execute", response_model=RemediationExecutionResult)
async def trigger_remediation_execution(
    plan_id: str,
    req: ExecuteRemediationRequest,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> RemediationExecutionResult:
    """Triggers live or dry-run execution of a remediation plan."""
    state = await get_investigation_checkpoint(session, req.incident_id)
    if not state or not state.remediation_plan or state.remediation_plan.plan_id != plan_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Remediation plan '{plan_id}' for incident '{req.incident_id}' not found",
        )

    try:
        return await execute_remediation_plan(session, state.remediation_plan, dry_run=req.dry_run)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
