import logging
import sys
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.agent.nodes as nodes
from app.agent.state import InvestigationState
from app.db.models.investigation_models import Investigation

logger = logging.getLogger(__name__)
MAX_INVESTIGATION_STEPS = 25
_test_memory_saver = MemorySaver()


def route_next_node(state: InvestigationState) -> str:
    if state.status == "open":
        return "triage"
    elif state.status == "investigating":
        if not state.telemetry_evidence:
            return "telemetry"
        if not state.knowledge_search_completed:
            return "knowledge"
        if not state.hypotheses:
            return "hypothesis"
        if not state.skeptic_feedback:
            return "skeptic"
        return "rca"
    elif state.status == "rca_ready":
        if not state.rca_report:
            return "rca"
        if not state.remediation_plan:
            return "remediation"
    elif state.status == "remediating":
        if (
            state.remediation_plan
            and state.remediation_plan.requires_human_approval
            and not state.remediation_plan.approved
        ):
            if state.history and state.history[-1] == "human_review_gate_node":
                pass
            return "human_review"
        return "outcome"
    elif state.status in {"resolved", "remediation_failed", "remediation_inconclusive", "cancelled"}:
        return END

    logger.warning(
        f"Workflow reached unknown state/status combo ({state.status}). Terminating graph loop."
    )
    return END


CompiledInvestigationGraph = CompiledStateGraph[Any, None, Any, Any]


def create_agent_graph(
    session: AsyncSession,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledInvestigationGraph:
    workflow = StateGraph(InvestigationState)

    async def _cancel_if_requested(state: InvestigationState) -> bool:
        requested = await session.scalar(
            select(Investigation.cancellation_requested).where(
                Investigation.incident_id == state.incident_id
            )
        )
        if requested:
            state.status = "cancelled"
            state.history.append("cancellation_guard")
            return True
        return False

    # We pass the session by wrapping the nodes dynamically
    async def _triage(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.triage_node(session, state)

    async def _telemetry(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.telemetry_investigator_node(session, state)

    async def _knowledge(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.knowledge_investigator_node(session, state)

    async def _hypothesis(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.hypothesis_generator_node(session, state)

    async def _skeptic(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.skeptic_verifier_node(session, state)

    async def _rca(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.rca_synthesizer_node(session, state)

    async def _remediation(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.remediation_planner_node(session, state)

    async def _human_review(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.human_review_gate_node(session, state)

    async def _outcome(state: InvestigationState) -> InvestigationState:
        if await _cancel_if_requested(state):
            return state
        return await nodes.outcome_verifier_node(session, state)

    workflow.add_node("triage", _triage)
    workflow.add_node("telemetry", _telemetry)
    workflow.add_node("knowledge", _knowledge)
    workflow.add_node("hypothesis", _hypothesis)
    workflow.add_node("skeptic", _skeptic)
    workflow.add_node("rca", _rca)
    workflow.add_node("remediation", _remediation)
    workflow.add_node("human_review", _human_review)
    workflow.add_node("outcome", _outcome)

    node_names = [
        "triage",
        "telemetry",
        "knowledge",
        "hypothesis",
        "skeptic",
        "rca",
        "remediation",
        "human_review",
        "outcome",
    ]
    for node in node_names:
        workflow.add_conditional_edges(node, route_next_node)

    workflow.set_entry_point("triage")
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["human_review"],
    )


async def _invoke_with_checkpointer(
    session: AsyncSession,
    state: InvestigationState,
    checkpointer: BaseCheckpointSaver[Any],
) -> InvestigationState:
    graph = create_agent_graph(session, checkpointer)
    config: RunnableConfig = {
        "recursion_limit": MAX_INVESTIGATION_STEPS,
        "configurable": {"thread_id": state.incident_id},
    }
    saved_state = await checkpointer.aget_tuple(config)
    if saved_state is None:
        result = await graph.ainvoke(state, config=config)
    else:
        # The relational investigation record contains the reviewed state. Merge
        # it into the durable LangGraph checkpoint, then resume with only the
        # thread ID represented by ``config``.
        await graph.aupdate_state(
            config,
            state.model_dump(mode="json"),
            as_node="human_review",
        )
        result = await graph.ainvoke(None, config=config)
    return InvestigationState.model_validate(result)


async def run_investigation_workflow(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    """Executes the multi-role agent investigation graph with recursion guard and state checkpointing."""
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        from app.core.config import settings

        # In-memory checkpoints are a test adapter only. Provider credentials
        # must never decide durability in production or local runtime.
        if "pytest" in sys.modules:
            return await _invoke_with_checkpointer(session, state, _test_memory_saver)

        if settings.DATABASE_URL is None:
            raise RuntimeError("DATABASE_URL is required for durable LangGraph execution")
        conn_string = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            await checkpointer.setup()
            return await _invoke_with_checkpointer(session, state, checkpointer)
    except Exception:
        logger.exception("Investigation graph execution failed")
        raise
