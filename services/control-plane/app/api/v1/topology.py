from fastapi import APIRouter, Depends

from app.core.auth import UserProfile, UserRole, require_role
from app.services.topology_extractor import TopologyGraph, extract_system_topology

router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("", response_model=TopologyGraph)
async def get_topology(
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> TopologyGraph:
    """Returns the service topology graph of the distributed demo system."""
    return extract_system_topology()
