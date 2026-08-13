from typing import Any

from fastapi import APIRouter, Depends

from app.core.auth import UserProfile, UserRole, require_role
from app.observability.ai_metrics import get_ai_metrics_summary

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/metrics")
async def get_ai_observability_metrics(
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> dict[str, Any]:
    """Returns runtime AI observability metrics including tokens, cost, and tool call stats."""
    return dict(get_ai_metrics_summary())
