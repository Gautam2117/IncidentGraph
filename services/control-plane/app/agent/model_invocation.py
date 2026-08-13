"""Audited live-model invocation helpers for investigation graph nodes."""

from __future__ import annotations

import time
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_factory import get_chat_model
from app.core.config import settings
from app.db.models.investigation_models import Investigation, ModelCall

GRAPH_VERSION = "investigation-graph.v1"


def _provider_and_model() -> tuple[str, str]:
    provider = settings.PRIMARY_LLM_PROVIDER.lower()
    if provider == "gemini":
        return provider, settings.GEMINI_MODEL
    if provider == "ollama":
        return provider, settings.OLLAMA_MODEL
    return provider, settings.OPENAI_MODEL


def _usage(message: AIMessage) -> tuple[int, int]:
    usage: dict[str, Any] = dict(message.usage_metadata or {})
    response_usage: dict[str, Any] = dict(message.response_metadata.get("token_usage", {}))
    input_tokens = int(usage.get("input_tokens") or response_usage.get("prompt_tokens") or 0)
    output_tokens = int(
        usage.get("output_tokens") or response_usage.get("completion_tokens") or 0
    )
    return input_tokens, output_tokens


def _estimated_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    # Local inference has no metered API cost. Rates for remote providers are
    # explicit configuration so billing changes cannot silently falsify data.
    if provider == "ollama":
        return 0.0
    input_rate = float(settings.LLM_INPUT_COST_PER_MILLION_USD)
    output_rate = float(settings.LLM_OUTPUT_COST_PER_MILLION_USD)
    return round((input_tokens * input_rate + output_tokens * output_rate) / 1_000_000, 8)


async def _persist_call(
    session: AsyncSession,
    incident_id: str,
    prompt_version: str,
    raw: AIMessage,
    output: dict[str, Any],
    latency_ms: float,
) -> None:
    investigation = await session.scalar(
        select(Investigation).where(Investigation.incident_id == incident_id)
    )
    if investigation is None:
        raise RuntimeError("Investigation must be persisted before a live model invocation")
    provider, model = _provider_and_model()
    input_tokens, output_tokens = _usage(raw)
    session.add(
        ModelCall(
            investigation_id=investigation.id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            graph_version=GRAPH_VERSION,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=_estimated_cost(provider, model, input_tokens, output_tokens),
            structured_output=output,
        )
    )
    await session.flush()


async def invoke_structured[SchemaT: BaseModel](
    session: AsyncSession,
    incident_id: str,
    prompt_version: str,
    prompt: ChatPromptTemplate,
    variables: dict[str, Any],
    schema: type[SchemaT],
) -> SchemaT:
    model = get_chat_model(temperature=0).with_structured_output(schema, include_raw=True)
    started = time.perf_counter()
    response = cast(dict[str, Any], await (prompt | model).ainvoke(variables))
    latency_ms = (time.perf_counter() - started) * 1000
    parsed = cast(SchemaT | None, response.get("parsed"))
    raw = cast(AIMessage, response["raw"])
    if parsed is None:
        raise RuntimeError(f"Model returned invalid structured output for {prompt_version}")
    await _persist_call(
        session,
        incident_id,
        prompt_version,
        raw,
        parsed.model_dump(mode="json"),
        latency_ms,
    )
    return parsed


async def invoke_text(
    session: AsyncSession,
    incident_id: str,
    prompt_version: str,
    messages: list[BaseMessage],
) -> AIMessage:
    started = time.perf_counter()
    response = cast(AIMessage, await get_chat_model(temperature=0).ainvoke(messages))
    latency_ms = (time.perf_counter() - started) * 1000
    await _persist_call(
        session,
        incident_id,
        prompt_version,
        response,
        {"content": str(response.content)},
        latency_ms,
    )
    return response
