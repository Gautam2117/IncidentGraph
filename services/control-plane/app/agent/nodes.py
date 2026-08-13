import json
import uuid
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_factory import is_mock_mode
from app.agent.model_invocation import invoke_structured, invoke_text
from app.agent.state import (
    Hypothesis,
    InvestigationState,
    RCAReport,
    RemediationPlan,
    RemediationStep,
)
from app.observability.tracer import trace_agent_node
from app.rag.store import get_rag_store
from app.services.incident_service import add_incident_event, get_incident
from app.tools.tool_registry import execute_tool


def _use_offline_adapter(state: InvestigationState) -> bool:
    """Select the explicit per-run or deployment-level offline adapter."""
    return bool(state.use_test_adapters or is_mock_mode())


async def triage_node(session: AsyncSession, state: InvestigationState) -> InvestigationState:
    async with trace_agent_node("triage_node", state.incident_id):
        state.step_count += 1
        state.history.append("triage_node")

        inc = await get_incident(session, state.incident_id)
        target_service = inc.target_service if inc and inc.target_service else "inventory"
        state.target_service = target_service
        state.triage_summary = (
            f"Triaged incident '{state.incident_id}'. Scoped target service: '{target_service}'."
        )
        state.status = "investigating"

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="system",
            actor="triage_agent",
            title="Incident Triaged",
            payload={"summary": state.triage_summary, "target_service": target_service},
        )
        return state


async def telemetry_investigator_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    """Collect telemetry evidence for the target service.

    Mock mode: executes all three standard diagnostic tools unconditionally.
    Live LLM mode: uses an evidence-driven loop — the LLM selects which tool
    to call next based on evidence gathered so far, stopping when it signals
    ``DONE`` or the ``MAX_TOOL_CALLS`` cap is reached. This allows the model
    to focus on the most diagnostic signal rather than always running all tools.
    """
    MAX_TOOL_CALLS = 5

    # Available tools the LLM may choose from
    AVAILABLE_TOOLS = [
        {"name": "metrics.query", "description": "Query Prometheus metrics for a service"},
        {"name": "logs.search", "description": "Search Loki error/warning logs for a service"},
        {"name": "traces.search", "description": "Retrieve Tempo distributed traces for a service"},
    ]

    async with trace_agent_node("telemetry_investigator_node", state.incident_id):
        state.step_count += 1
        state.history.append("telemetry_investigator_node")

        service = state.target_service or "inventory"
        evidence: list[dict[str, Any]] = []

        if _use_offline_adapter(state):
            # Deterministic: call all three diagnostic tools unconditionally.
            adapter_args = {"use_test_adapter": state.use_test_adapters}
            metrics_res = await execute_tool("metrics.query", {"service": service, **adapter_args})
            logs_res = await execute_tool(
                "logs.search", {"service": service, "severity": "ERROR", **adapter_args}
            )
            traces_res = await execute_tool(
                "traces.search", {"service": service, "has_error": True, **adapter_args}
            )
            evidence = [
                {
                    "tool": "metrics.query",
                    "arguments": {"service": service},
                    "data": metrics_res.data,
                },
                {
                    "tool": "logs.search",
                    "arguments": {"service": service, "severity": "ERROR"},
                    "data": logs_res.data,
                },
                {
                    "tool": "traces.search",
                    "arguments": {"service": service, "has_error": True},
                    "data": traces_res.data,
                },
            ]
        else:
            # Evidence-driven loop: ask the LLM which tool to call next.
            from langchain_core.messages import HumanMessage, SystemMessage

            system_msg = SystemMessage(
                content=(
                    "You are an SRE diagnostic agent. Choose the most informative tool to call next "
                    f"for service '{service}'. Available tools: "
                    + ", ".join(t["name"] for t in AVAILABLE_TOOLS)
                    + ". Respond with ONLY the tool name (e.g. 'metrics.query') or 'DONE' to stop."
                )
            )

            for _iteration in range(MAX_TOOL_CALLS):
                context = f"Evidence collected so far ({len(evidence)} items):\n" + json.dumps(
                    [{"tool": e["tool"]} for e in evidence], default=str
                )
                response = await invoke_text(
                    session,
                    state.incident_id,
                    "telemetry-tool-selection.v1",
                    [system_msg, HumanMessage(content=context)],
                )
                chosen = response.content.strip().lower()

                if chosen == "done" or not chosen:
                    break

                # Resolve tool name (accept partial matches for robustness)
                matched_tool = next(
                    (t["name"] for t in AVAILABLE_TOOLS if t["name"] in chosen),
                    None,
                )
                if not matched_tool:
                    break  # LLM chose an unknown tool — stop iteration

                default_args: dict[str, object] = {"service": service}
                if "logs" in matched_tool:
                    default_args["severity"] = "ERROR"
                if "traces" in matched_tool:
                    default_args["has_error"] = True

                tool_res = await execute_tool(matched_tool, default_args)
                evidence.append(
                    {"tool": matched_tool, "arguments": default_args, "data": tool_res.data}
                )

        state.telemetry_evidence.extend(evidence)

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="retrieval",
            actor="telemetry_investigator",
            title="Telemetry Evidence Collected",
            payload={
                "evidence_count": len(evidence),
                "tools_called": [e["tool"] for e in evidence],
                "mode": "offline_adapter" if _use_offline_adapter(state) else "live_llm",
            },
        )
        return state


async def knowledge_investigator_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    async with trace_agent_node("knowledge_investigator_node", state.incident_id):
        state.step_count += 1
        state.history.append("knowledge_investigator_node")

        rag_store = get_rag_store()
        query = f"Incident on service {state.target_service} error logs connection pool latency"
        results = await rag_store.search_hybrid(session, query, top_k=3)

        docs = [
            {
                "chunk_id": chunk.chunk_id,
                "title": chunk.metadata.get("title", ""),
                "content": chunk.content[:200],
            }
            for chunk, _score in results
        ]
        state.knowledge_docs.extend(docs)
        # An empty result set is still a completed retrieval attempt. Without a
        # separate marker, the router repeatedly invokes this node until the
        # graph recursion guard fires on a new/empty knowledge base.
        state.knowledge_search_completed = True

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="retrieval",
            actor="knowledge_investigator",
            title="Knowledge Runbooks Retrieved",
            payload={"retrieved_docs": [d["title"] for d in docs]},
        )
        return state


async def hypothesis_generator_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    async with trace_agent_node("hypothesis_generator_node", state.incident_id):
        state.step_count += 1
        state.history.append("hypothesis_generator_node")

        service = state.target_service or "inventory"

        if _use_offline_adapter(state):
            # Ground-truth isolated fallback: analyze telemetry evidence and knowledge docs.
            # This heuristic is intentionally simple — it exists only so the pipeline
            # can complete end-to-end in offline tests without a real model.
            # Set OPENAI_API_KEY to a real key to enable LLM-driven hypothesis generation.
            category, desc, evidence_summary = _infer_hypothesis_from_evidence(
                state.telemetry_evidence, state.knowledge_docs, service
            )
            h1 = Hypothesis(
                id=f"hyp_{uuid.uuid4().hex[:6]}",
                target_service=service,
                root_cause_category=category,
                description=desc,
                confidence=0.90,
                supporting_evidence=evidence_summary,
                status="proposed",
            )
            state.hypotheses.append(h1)
        else:
            # Live LLM path — structured output directly into Hypothesis schema.
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are an expert SRE. Analyse the telemetry evidence and knowledge "
                        "runbooks to propose the most likely root cause hypothesis. "
                        "Be specific about the root_cause_category and supporting_evidence.",
                    ),
                    (
                        "human",
                        "Telemetry:\n{telemetry}\n\nKnowledge Runbooks:\n{knowledge}\n\nTarget Service: {service}",
                    ),
                ]
            )
            result = await invoke_structured(
                session,
                state.incident_id,
                "hypothesis-generation.v1",
                prompt,
                {
                    "telemetry": json.dumps(state.telemetry_evidence, default=str),
                    "knowledge": json.dumps(state.knowledge_docs, default=str),
                    "service": service,
                },
                Hypothesis,
            )
            result.id = f"hyp_{uuid.uuid4().hex[:6]}"
            result.status = "proposed"
            h1 = result
            state.hypotheses.append(h1)

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="hypothesis",
            actor="hypothesis_generator",
            title="Root Cause Hypothesis Formulated",
            payload={
                "hypothesis_id": h1.id,
                "description": h1.description,
                "confidence": h1.confidence,
                "mode": "offline_adapter" if _use_offline_adapter(state) else "live_llm",
            },
        )
        return state


async def skeptic_verifier_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    """Verify each proposed hypothesis against telemetry evidence.

    Possible outcomes per hypothesis:
    - ``verified``             — evidence supports the hypothesis
    - ``rejected``             — evidence contradicts the hypothesis
    - ``insufficient_evidence`` — not enough telemetry to decide
    """
    async with trace_agent_node("skeptic_verifier_node", state.incident_id):
        state.step_count += 1
        state.history.append("skeptic_verifier_node")

        for h in state.hypotheses:
            if h.status != "proposed":
                continue

            if _use_offline_adapter(state):
                # Offline heuristic:
                #  - confidence < 0.5        → rejected (too weak, evidence doesn't support)
                #  - confidence >= 0.5 + no evidence → insufficient_evidence (can't evaluate)
                #  - confidence >= 0.5 + evidence    → verified
                evidence_items = len(state.telemetry_evidence)
                if h.confidence < 0.5:
                    h.status = "rejected"
                    state.skeptic_feedback.append(
                        f"Hypothesis {h.id} REJECTED: confidence {h.confidence:.2f} is below threshold."
                    )
                elif evidence_items == 0:
                    h.status = "insufficient_evidence"
                    state.skeptic_feedback.append(
                        f"Hypothesis {h.id} INSUFFICIENT_EVIDENCE: no telemetry collected to evaluate."
                    )
                else:
                    h.status = "verified"
                    state.skeptic_feedback.append(
                        f"Hypothesis {h.id} VERIFIED: confidence {h.confidence:.2f} with "
                        f"{evidence_items} evidence items."
                    )
            else:
                # Live LLM path — ask a skeptic to verify with structured output.
                from pydantic import BaseModel  # local import avoids top-level circularity

                class VerificationOutput(BaseModel):
                    status: str  # "verified", "rejected", or "insufficient_evidence"
                    feedback: str

                prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            "You are an SRE skeptic verifier. Evaluate the hypothesis strictly "
                            "against the telemetry evidence. Output one of three statuses: "
                            "'verified' (evidence supports), 'rejected' (evidence contradicts), "
                            "'insufficient_evidence' (not enough data to decide). Be conservative.",
                        ),
                        (
                            "human",
                            "Hypothesis:\n{hypothesis}\n\nTelemetry Evidence:\n{telemetry}",
                        ),
                    ]
                )
                result = await invoke_structured(
                    session,
                    state.incident_id,
                    "skeptic-verification.v1",
                    prompt,
                    {
                        "hypothesis": h.model_dump_json(),
                        "telemetry": json.dumps(state.telemetry_evidence, default=str),
                    },
                    VerificationOutput,
                )
                h.status = result.status
                state.skeptic_feedback.append(
                    f"Hypothesis {h.id} {result.status.upper()}: {result.feedback}"
                )

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="verifier",
            actor="skeptic_verifier",
            title="Hypothesis Evidence Verification",
            payload={
                "verified_count": len([h for h in state.hypotheses if h.status == "verified"]),
                "rejected_count": len([h for h in state.hypotheses if h.status == "rejected"]),
                "insufficient_count": len(
                    [h for h in state.hypotheses if h.status == "insufficient_evidence"]
                ),
                "mode": "offline_adapter" if _use_offline_adapter(state) else "live_llm",
            },
        )
        return state


async def rca_synthesizer_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    async with trace_agent_node("rca_synthesizer_node", state.incident_id):
        state.step_count += 1
        state.history.append("rca_synthesizer_node")

        verified_hypotheses = [h for h in state.hypotheses if h.status == "verified"]

        if verified_hypotheses:
            top_h = max(verified_hypotheses, key=lambda x: x.confidence)
            if _use_offline_adapter(state):
                rca = RCAReport(
                    summary=top_h.description,
                    primary_service=top_h.target_service,
                    root_cause_category=top_h.root_cause_category,
                    causal_chain=top_h.supporting_evidence
                    or ["Evidence collected", "Hypothesis matched"],
                    confidence_score=top_h.confidence,
                    is_conclusive=True,
                )
            else:
                # Live LLM path — synthesise full RCA from verified hypothesis + telemetry.
                prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            "You are a senior SRE synthesising a Root Cause Analysis (RCA) report. "
                            "Use the verified hypothesis and full telemetry to produce a precise, "
                            "actionable RCA with a step-by-step causal chain.",
                        ),
                        (
                            "human",
                            "Verified Hypothesis:\n{hypothesis}\n\nTelemetry Evidence:\n{telemetry}",
                        ),
                    ]
                )
                rca = await invoke_structured(
                    session,
                    state.incident_id,
                    "rca-synthesis.v1",
                    prompt,
                    {
                        "hypothesis": top_h.model_dump_json(),
                        "telemetry": json.dumps(state.telemetry_evidence, default=str),
                    },
                    RCAReport,
                )
        else:
            rca = RCAReport(
                summary="INSUFFICIENT_EVIDENCE: No verified hypotheses. Telemetry and logs inconclusive.",
                primary_service=state.target_service or "unknown",
                root_cause_category="unknown",
                causal_chain=[],
                confidence_score=0.0,
                is_conclusive=False,
            )

        state.rca_report = rca
        state.status = "rca_ready"

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="rca",
            actor="rca_synthesizer",
            title="Root Cause Analysis Synthesized",
            payload=rca.model_dump(),
        )
        return state


def _infer_hypothesis_from_evidence(
    telemetry_evidence: list[dict[str, Any]],
    knowledge_docs: list[dict[str, Any]],
    service: str,
) -> tuple[str, str, list[str]]:
    """Strictly infers root cause hypothesis from collected telemetry evidence without reading scenario ground truth."""
    combined_text = ""
    evidence_items = []
    for item in telemetry_evidence:
        data = item.get("data")
        if isinstance(data, list):
            for d in data:
                if isinstance(d, dict):
                    msg = d.get("message", "") or d.get("logger", "")
                    combined_text += " " + str(msg)
                    if msg:
                        evidence_items.append(str(msg))
        elif isinstance(data, dict):
            combined_text += " " + str(data)

    text_lower = combined_text.lower()

    if "pool" in text_lower or "20/20" in text_lower:
        category = "database_pool_exhaustion"
        desc = f"Database connection pool capacity exhausted on service '{service}'."
    elif "index" in text_lower or "scan" in text_lower or "n+1" in text_lower:
        category = "missing_database_index"
        desc = f"Unindexed database query causing high CPU and latency on service '{service}'."
    elif "jwt" in text_lower or "token" in text_lower or "signature" in text_lower:
        category = "invalid_jwt_signature"
        desc = f"Authentication token signature mismatch or secret key misconfiguration on '{service}'."
    elif (
        "kafka" in text_lower
        or "partition" in text_lower
        or "lag" in text_lower
        or "queue" in text_lower
    ):
        category = "kafka_partition_lag"
        desc = f"Kafka message consumer partition backlog or deadletter queue accumulation on '{service}'."
    elif "circuit" in text_lower or "breaker" in text_lower:
        category = "circuit_breaker_trip"
        desc = f"Circuit breaker opened due to downstream error rate on '{service}'."
    elif "rate limit" in text_lower or "429" in text_lower or "throttl" in text_lower:
        category = "downstream_dependency_latency"
        desc = f"Rate limit throttling or high dependency latency on '{service}'."
    elif "memory" in text_lower or "oom" in text_lower or "leak" in text_lower:
        category = "memory_leak_oom_killed"
        desc = f"Excessive memory allocation leading to eviction or OOM error on '{service}'."
    else:
        category = "downstream_dependency_latency"
        desc = f"Upstream response timeout or high dependency latency affecting '{service}'."

    summary = (
        evidence_items[:3]
        if evidence_items
        else [f"Telemetry evidence collected for service {service}"]
    )
    return category, desc, summary


def _infer_remediation_action(root_cause_category: str, service: str) -> tuple[str, dict[str, Any]]:
    """Derives allowed remediation action from agent RCA report without scenario lookup."""
    cat = (root_cause_category or "").lower()
    if "pool" in cat or "lock" in cat:
        return "scale_pool", {"service": service, "max_connections": 50}
    elif "deployment" in cat or "config" in cat or "jwt" in cat:
        return "rollback_deploy", {"service": service, "version": "previous"}
    elif "cache" in cat:
        return "flush_cache", {"service": service}
    elif "circuit" in cat:
        return "reset_circuit_breaker", {"service": service}
    return "restart_service", {"service": service}


async def remediation_planner_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    async with trace_agent_node("remediation_planner_node", state.incident_id):
        state.step_count += 1
        state.history.append("remediation_planner_node")

        service = state.target_service or "inventory"
        rca_summary = state.rca_report.summary if state.rca_report else ""
        rca_cat = state.rca_report.root_cause_category if state.rca_report else ""

        ALLOWED_ACTIONS = {
            "scale_pool",
            "restart_service",
            "rollback_deploy",
            "reset_circuit_breaker",
            "flush_cache",
        }

        if _use_offline_adapter(state):
            action_type, action_params = _infer_remediation_action(rca_cat, service)
            plan = RemediationPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                incident_id=state.incident_id,
                steps=[
                    RemediationStep(
                        step_number=1,
                        action_type=action_type,
                        description=f"Remediation action '{action_type}' for service '{service}'",
                        target_service=service,
                        parameters=action_params,
                        is_safe=True,
                    )
                ],
                risk_level="high",
                requires_human_approval=True,
                approved=False,
            )
        else:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a senior SRE remediation engineer. Design a safe remediation plan "
                        "for the incident. Only use action_type values from this strict allow-list: "
                        + ", ".join(sorted(ALLOWED_ACTIONS))
                        + ". "
                        "Set requires_human_approval=True and approved=False.",
                    ),
                    (
                        "human",
                        "Target Service: {service}\nRoot Cause Category: {cat}\nRCA Summary:\n{summary}",
                    ),
                ]
            )
            plan = await invoke_structured(
                session,
                state.incident_id,
                "remediation-plan.v1",
                prompt,
                {
                    "service": service,
                    "cat": rca_cat,
                    "summary": rca_summary,
                },
                RemediationPlan,
            )
            plan.plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            plan.incident_id = state.incident_id
            plan.requires_human_approval = True
            plan.approved = False
            # Filter any step actions to strictly allowed set
            for step in plan.steps:
                if step.action_type not in ALLOWED_ACTIONS:
                    step.action_type = "restart_service"  # safe fallback

        state.remediation_plan = plan
        state.status = "remediating"

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="remediation",
            actor="remediation_planner",
            title="Remediation Action Plan Created",
            payload=plan.model_dump(),
        )
        return state


async def human_review_gate_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    async with trace_agent_node("human_review_gate_node", state.incident_id):
        state.step_count += 1
        state.history.append("human_review_gate_node")

        if state.remediation_plan and state.remediation_plan.requires_human_approval:
            state.remediation_plan.approved = False
            await add_incident_event(
                session,
                incident_id=state.incident_id,
                event_type="system",
                actor="human_gate",
                title="Paused for Human Approval",
                payload={"plan_id": state.remediation_plan.plan_id},
            )
        return state


async def outcome_verifier_node(
    session: AsyncSession, state: InvestigationState
) -> InvestigationState:
    async with trace_agent_node("outcome_verifier_node", state.incident_id):
        state.step_count += 1
        state.history.append("outcome_verifier_node")

        from app.remediation.executor import execute_remediation_plan

        if state.remediation_plan is None or not state.remediation_plan.approved:
            state.status = "remediation_failed"
            result_payload = {
                "success": False,
                "verification_passed": False,
                "error": "approved_remediation_plan_required",
            }
        else:
            execution = await execute_remediation_plan(
                session,
                state.remediation_plan,
                dry_run=False,
            )
            result_payload = execution.model_dump(mode="json")
            if execution.success and execution.verification_passed:
                state.status = "resolved"
            elif execution.step_results and all(step.success for step in execution.step_results):
                state.status = "remediation_inconclusive"
            else:
                state.status = "remediation_failed"

        state.remediation_execution = result_payload

        await add_incident_event(
            session,
            incident_id=state.incident_id,
            event_type="outcome",
            actor="outcome_verifier",
            title="Remediation Outcome Classified",
            payload={"status": state.status, **result_payload},
        )
        return state
