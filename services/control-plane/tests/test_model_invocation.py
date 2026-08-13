from typing import Any

import pytest
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import model_invocation
from app.agent.model_invocation import invoke_structured, invoke_text
from app.agent.state import InvestigationState
from app.core.config import settings
from app.db.models.investigation_models import Investigation as DBInvestigation
from app.db.models.investigation_models import ModelCall
from app.services.incident_service import CreateIncidentRequest, create_incident


class StructuredAnswer(BaseModel):
    answer: str


@pytest.mark.asyncio
async def test_live_model_invocations_are_audited(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    incident = await create_incident(
        db_session,
        CreateIncidentRequest(title="Model audit", severity="low", target_service="orders"),
    )
    state = InvestigationState(incident_id=incident.id)
    from app.agent.agent_runner import save_investigation_checkpoint

    await save_investigation_checkpoint(db_session, state)
    inv = (
        await db_session.scalars(
            select(DBInvestigation).where(DBInvestigation.incident_id == incident.id)
        )
    ).first()
    assert inv is not None
    inv_id = inv.id
    monkeypatch.setattr(settings, "PRIMARY_LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "audit-model")
    monkeypatch.setattr(settings, "LLM_INPUT_COST_PER_MILLION_USD", 2.0)
    monkeypatch.setattr(settings, "LLM_OUTPUT_COST_PER_MILLION_USD", 4.0)

    raw = AIMessage(
        content="ok",
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    )

    class FakeStructuredModel:
        def with_structured_output(
            self, _schema: type[BaseModel], *, include_raw: bool
        ) -> RunnableLambda[Any, Any]:
            assert include_raw is True
            return RunnableLambda(
                lambda _value: {"parsed": StructuredAnswer(answer="safe"), "raw": raw}
            )

    monkeypatch.setattr(model_invocation, "get_chat_model", lambda temperature=0: FakeStructuredModel())
    prompt = ChatPromptTemplate.from_messages([("human", "Question: {question}")])
    parsed = await invoke_structured(
        db_session,
        incident.id,
        "audit-structured.v1",
        prompt,
        {"question": "status"},
        StructuredAnswer,
    )
    assert parsed.answer == "safe"

    class FakeTextModel:
        async def ainvoke(self, _messages: object) -> AIMessage:
            return raw

    monkeypatch.setattr(model_invocation, "get_chat_model", lambda temperature=0: FakeTextModel())
    text_result = await invoke_text(
        db_session,
        incident.id,
        "audit-text.v1",
        [],
    )
    assert text_result.content == "ok"
    await db_session.commit()

    calls = list((await db_session.scalars(select(ModelCall))).all())
    matching = [call for call in calls if call.investigation_id == inv_id]
    assert len(matching) == 2
    assert {call.graph_version for call in matching} == {"investigation-graph.v1"}
    assert {call.prompt_tokens for call in matching} == {10}
    assert {call.completion_tokens for call in matching} == {5}
    assert all(abs(call.cost_usd - 0.00004) < 1e-7 for call in matching)
    assert all(call.latency_ms >= 0 for call in matching)
    assert {call.provider for call in matching} == {"openai"}
