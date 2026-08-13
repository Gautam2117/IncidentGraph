from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserProfile, UserRole, require_role
from app.db.session import get_db
from app.postmortem.generator import (
    PostmortemReport,
    generate_postmortem,
    get_postmortem,
)

router = APIRouter(prefix="/postmortems", tags=["postmortems"])


class GeneratePostmortemRequest(BaseModel):
    incident_id: str


@router.post("/generate", response_model=PostmortemReport, status_code=status.HTTP_201_CREATED)
async def generate_incident_postmortem(
    req: GeneratePostmortemRequest,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> PostmortemReport:
    """Generates an automated postmortem report and indexes it into the RAG knowledge base."""
    try:
        return await generate_postmortem(session, req.incident_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/{incident_id}", response_model=PostmortemReport)
async def get_incident_postmortem(
    incident_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> PostmortemReport:
    """Retrieves postmortem report for a specific incident."""
    pm = await get_postmortem(session, incident_id)
    if not pm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Postmortem for incident '{incident_id}' not found",
        )
    return pm


@router.get("/{incident_id}/markdown")
async def get_incident_postmortem_markdown(
    incident_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> Response:
    """Retrieves postmortem report formatted as raw Markdown."""
    pm = await get_postmortem(session, incident_id)
    if not pm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Postmortem for incident '{incident_id}' not found",
        )
    return Response(content=pm.markdown_content, media_type="text/markdown")
