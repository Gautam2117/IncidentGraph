import pytest
from httpx import AsyncClient
from pydantic import BaseModel

from app.agent.llm_factory import get_chat_model, is_mock_mode
from app.core.config import settings
from app.models.accounting import calculate_cost, get_cumulative_accounting
from app.models.fake_provider import FakeModelProvider
from app.models.fallback import FallbackProvider
from app.models.gemini_provider import GeminiProvider
from app.models.router import ModelRouter


class DummyRCAHypothesis(BaseModel):
    root_cause_service: str
    confidence: float
    is_confirmed: bool


@pytest.mark.asyncio
async def test_fake_provider_text_generation() -> None:
    provider = FakeModelProvider()
    res = await provider.generate("Analyze slow database queries")
    assert res.content.startswith("Fake LLM response")
    assert res.token_usage.total_tokens > 0
    assert res.provider_name == "fake"


@pytest.mark.asyncio
async def test_fake_provider_structured_output() -> None:
    provider = FakeModelProvider()
    obj, res = await provider.generate_structured("Analyze RCA", response_schema=DummyRCAHypothesis)
    assert isinstance(obj, DummyRCAHypothesis)
    assert obj.root_cause_service == "sample_root_cause_service"
    assert obj.confidence == 0.95
    assert obj.is_confirmed is True
    assert res.structured_data is not None


@pytest.mark.asyncio
async def test_fake_provider_tool_calls() -> None:
    provider = FakeModelProvider()
    tools = [{"name": "metrics.query", "description": "query metrics"}]
    res = await provider.generate_with_tools("Check inventory latency", tools=tools)
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "metrics.query"


@pytest.mark.asyncio
async def test_fallback_provider_chain() -> None:
    primary = GeminiProvider()
    fallback = FakeModelProvider()
    chain = FallbackProvider([primary, fallback])

    res = await chain.generate("Test prompt")
    assert res.content is not None
    assert res.token_usage.total_tokens > 0


def test_token_and_cost_accounting() -> None:
    cost = calculate_cost("gemini-1.5-pro", prompt_tokens=1_000_000, completion_tokens=1_000_000)
    assert cost == 6.25  # $1.25 input + $5.00 output

    acct = get_cumulative_accounting()
    assert acct.total_requests >= 0


def test_model_router_tier_allocation() -> None:
    router = ModelRouter()
    assert router.select_model("triage") == "gemini-1.5-flash"
    assert router.select_model("rca") == "gemini-1.5-pro"


def test_agent_factory_routes_configured_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "PRIMARY_LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_MODEL", "llama3.2")
    assert is_mock_mode() is False
    model = get_chat_model()
    assert model.model_name == "llama3.2"


@pytest.mark.asyncio
async def test_models_overview_api(async_client: AsyncClient, admin_client: AsyncClient) -> None:
    engineer_res = await async_client.get("/api/v1/models/providers")
    assert engineer_res.status_code == 403
    res = await admin_client.get("/api/v1/models/providers")
    assert res.status_code == 200
    data = res.json()
    assert "providers" in data
    assert "routing_policy" in data
    assert data["routing_policy"]["rca"] == settings.OPENAI_MODEL
    assert all("reachable" in provider for provider in data["providers"])
