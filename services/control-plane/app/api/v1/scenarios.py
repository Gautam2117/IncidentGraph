from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserProfile, UserRole, require_role
from app.db.session import get_db
from app.scenarios.registry import get_scenario, list_scenarios
from app.scenarios.runner import get_scenario_run, reset_scenario, trigger_scenario
from app.scenarios.schema import ScenarioRun

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[dict[str, Any]])
async def list_available_scenarios(
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> list[dict[str, Any]]:
    """Lists all available scenarios with Ground Truth stripped for model safety."""
    return [scen.get_safe_metadata() for scen in list_scenarios()]


@router.get("/{scenario_id}", response_model=dict[str, Any])
async def get_scenario_details(
    scenario_id: str,
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> dict[str, Any]:
    """Gets scenario details with Ground Truth stripped for model safety."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found",
        )
    return dict(scenario.get_safe_metadata())


@router.post("/{scenario_id}/trigger", response_model=ScenarioRun)
async def trigger_scenario_run(
    scenario_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> ScenarioRun:
    """Triggers fault injection and starts scenario run."""
    try:
        return await trigger_scenario(session, scenario_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/{scenario_id}/reset", response_model=ScenarioRun)
async def reset_scenario_run(
    scenario_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> ScenarioRun:
    """Resets fault injection and returns scenario to clean baseline state."""
    return await reset_scenario(session, scenario_id)


@router.get("/{scenario_id}/run", response_model=ScenarioRun)
async def get_latest_scenario_run(
    scenario_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> ScenarioRun:
    run = await get_scenario_run(session, scenario_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No run found for scenario '{scenario_id}'",
        )
    return run
