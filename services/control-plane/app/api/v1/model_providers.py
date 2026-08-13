from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.agent.llm_factory import is_mock_mode
from app.core.auth import UserProfile, UserRole, require_role
from app.core.config import settings
from app.models.accounting import get_cumulative_accounting

router = APIRouter(prefix="/models", tags=["models"])


class ProviderStatusDTO(BaseModel):
    name: str
    configured: bool
    reachable: bool
    is_active: bool
    default_model: str
    supported_models: list[str]
    detail: str


class ModelsOverviewDTO(BaseModel):
    providers: list[ProviderStatusDTO]
    routing_policy: dict[str, str]
    accounting: dict[str, Any]


async def _provider_reachable(
    url: str, headers: dict[str, str] | None = None, params: dict[str, str] | None = None
) -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url, headers=headers, params=params)
            return response.status_code < 400
    except httpx.HTTPError:
        return False


@router.get("/providers", response_model=ModelsOverviewDTO)
async def get_providers_overview(
    _user: UserProfile = Depends(require_role(UserRole.ADMIN)),
) -> ModelsOverviewDTO:
    """Return configured and probed provider state without exposing credentials."""
    openai_configured = bool(
        settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock-")
    )
    gemini_configured = bool(settings.GEMINI_API_KEY)
    openai_reachable = openai_configured and await _provider_reachable(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
    )
    gemini_reachable = gemini_configured and await _provider_reachable(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": settings.GEMINI_API_KEY or ""},
    )
    ollama_reachable = await _provider_reachable(f"{settings.OLLAMA_URL.rstrip('/')}/api/tags")
    primary = settings.PRIMARY_LLM_PROVIDER.lower()
    configured_models = {
        "openai": settings.OPENAI_MODEL,
        "gemini": settings.GEMINI_MODEL,
        "ollama": settings.OLLAMA_MODEL,
    }
    routed_model = configured_models.get(primary, settings.OPENAI_MODEL)
    providers = [
        ProviderStatusDTO(
            name="openai",
            configured=openai_configured,
            reachable=openai_reachable,
            is_active=primary == "openai" and openai_reachable,
            default_model=settings.OPENAI_MODEL,
            supported_models=[settings.OPENAI_MODEL],
            detail="reachable" if openai_reachable else "not configured or unreachable",
        ),
        ProviderStatusDTO(
            name="gemini",
            configured=gemini_configured,
            reachable=gemini_reachable,
            is_active=primary == "gemini" and gemini_reachable,
            default_model=settings.GEMINI_MODEL,
            supported_models=[settings.GEMINI_MODEL],
            detail="reachable" if gemini_reachable else "not configured or unreachable",
        ),
        ProviderStatusDTO(
            name="ollama",
            configured=True,
            reachable=ollama_reachable,
            is_active=primary == "ollama" and ollama_reachable,
            default_model=settings.OLLAMA_MODEL,
            supported_models=[settings.OLLAMA_MODEL],
            detail="reachable" if ollama_reachable else "unreachable",
        ),
        ProviderStatusDTO(
            name="offline-test-adapter",
            configured=is_mock_mode(),
            reachable=is_mock_mode(),
            is_active=is_mock_mode() and settings.ENVIRONMENT.lower() != "production",
            default_model="deterministic-test-adapter",
            supported_models=["deterministic-test-adapter"],
            detail="test-only; excluded from live benchmark claims",
        ),
    ]
    routing_policy = {
        "triage": routed_model,
        "investigation": routed_model,
        "rca": routed_model,
        "verification": routed_model,
    }
    return ModelsOverviewDTO(
        providers=providers,
        routing_policy=routing_policy,
        accounting=get_cumulative_accounting().model_dump(),
    )
