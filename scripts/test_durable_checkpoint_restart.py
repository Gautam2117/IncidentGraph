#!/usr/bin/env python3
"""
F4 — Multi-Process Durable LangGraph Restart Proof (A1 — fixed)

Invariant: Process 2 receives ONLY the thread_id string.
           It never receives a serialised InvestigationState payload.
           All state is loaded exclusively from the PostgreSQL checkpoint store
           (AsyncPostgresSaver) that Process 1 wrote to.

Flow
----
Process 1:
  1. Creates an incident in PostgreSQL.
  2. Builds the agent graph with AsyncPostgresSaver (real DB checkpointer).
  3. Runs graph.ainvoke() — graph runs until interrupt_after=["human_review"].
  4. Writes ONLY {"thread_id": "..."} to a private temporary handoff file and exits.
  5. Does NOT write state to disk.

Handoff:
  Main process reads thread_id from the file.  No state is read.

Process 2:
  1. Receives thread_id as a CLI argument (injected into script via f-string).
  2. Opens AsyncPostgresSaver connection to same PostgreSQL DB.
  3. Calls checkpointer.aget_tuple() — verifies checkpoint exists.
  4. Reads status and remediation_plan directly from checkpoint channel_values.
  5. Updates remediation_plan.approved = True via graph.aupdate_state().
  6. Resumes with graph.ainvoke(None, config) — state comes from DB only.
  7. Asserts final status is "resolved".
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Process 1 script
# ---------------------------------------------------------------------------
_P1_SCRIPT = """
import asyncio
import json
import os
from app.db.session import AsyncSessionLocal
from app.services.incident_service import create_incident, CreateIncidentRequest
from app.agent.graph import create_agent_graph
from app.agent.state import InvestigationState
from app.core.config import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def p1() -> None:
    pid = os.getpid()
    async with AsyncSessionLocal() as session:
        inc = await create_incident(
            session,
            CreateIncidentRequest(
                title="P1 Durability Test — LangGraph PostgresSaver",
                severity="critical",
                target_service="payments",
                scenario_id="payment_latency",
            ),
        )
        inc_id = str(inc.id)
        print(f"P1_PID:{pid}")
        print(f"P1_THREAD_ID:{inc_id}")

        # Use AsyncPostgresSaver (real DB checkpoint) — independent of LLM mode
        conn_string = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            await checkpointer.setup()
            graph = create_agent_graph(session, checkpointer)
            config = {"recursion_limit": 25, "configurable": {"thread_id": inc_id}}

            init_state = InvestigationState(incident_id=inc_id, target_service="payments")
            # graph.ainvoke returns at interrupt_after=["human_review"]
            partial = await graph.ainvoke(init_state, config=config)
            partial_state = InvestigationState(**partial)
            print(f"P1_STATUS:{partial_state.status}")
            if partial_state.remediation_plan:
                print(f"P1_PLAN_ID:{partial_state.remediation_plan.plan_id}")

    # Write ONLY thread_id — never the full state
    with open(os.environ["DURABLE_HANDOFF_PATH"], "w") as f:
        json.dump({"thread_id": inc_id}, f)
    print("P1_WROTE_THREAD_ID_ONLY:True")


asyncio.run(p1())
"""


# ---------------------------------------------------------------------------
# Process 2 script — receives thread_id only (injected via f-string below)
# ---------------------------------------------------------------------------
def _build_p2_script(thread_id: str) -> str:
    return f"""
import asyncio
import os
from app.db.session import AsyncSessionLocal
from app.agent.graph import create_agent_graph
from app.agent.state import InvestigationState, RemediationPlan
from app.core.config import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

THREAD_ID = "{thread_id}"  # Only datum passed from Process 1


async def p2() -> None:
    pid = os.getpid()
    print(f"P2_PID:{{pid}}")
    print(f"P2_THREAD_ID:{{THREAD_ID}}")

    conn_string = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    async with AsyncSessionLocal() as session:
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            graph = create_agent_graph(session, checkpointer)
            config = {{"recursion_limit": 25, "configurable": {{"thread_id": THREAD_ID}}}}

            # ----------------------------------------------------------------
            # Critical assertion: checkpoint must exist in DB
            # Process 2 NEVER received a state payload — only THREAD_ID
            # ----------------------------------------------------------------
            saved_tuple = await checkpointer.aget_tuple(config)
            assert saved_tuple is not None, (
                "FATAL: No checkpoint found in PostgreSQL for thread_id="
                + THREAD_ID
            )
            print("P2_CHECKPOINT_FROM_DB:True")

            # Read status directly from DB checkpoint
            ch = saved_tuple.checkpoint.get("channel_values", {{}})
            db_status = ch.get("status", "unknown")
            print(f"P2_DB_STATUS:{{db_status}}")

            # Approve the remediation plan (as a human operator would)
            raw_plan = ch.get("remediation_plan")
            if raw_plan is not None:
                if isinstance(raw_plan, dict):
                    raw_plan["approved"] = True
                else:
                    # Pydantic model instance inside the checkpoint
                    raw_plan = raw_plan.model_dump()
                    raw_plan["approved"] = True

                await graph.aupdate_state(
                    config,
                    {{"remediation_plan": raw_plan, "status": "remediating"}},
                    as_node="human_review",
                )
                print("P2_PLAN_APPROVED:True")

            # Resume from DB state — None means "continue from last checkpoint"
            final = await graph.ainvoke(None, config=config)
            final_state = InvestigationState(**final)
            print(f"P2_FINAL_STATUS:{{final_state.status}}")


asyncio.run(p2())
"""


# ---------------------------------------------------------------------------
# Subprocess runners
# ---------------------------------------------------------------------------


def _run_subprocess(label: str, script: str, handoff_path: Path | None = None) -> str:
    env = dict(
        os.environ,
        PYTHONPATH=os.getcwd(),
        SECRET_KEY="12345678901234567890123456789012",
    )
    if handoff_path is not None:
        env["DURABLE_HANDOFF_PATH"] = str(handoff_path)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
    )
    print(f"--- {label} STDOUT ---")
    print(result.stdout)
    if result.returncode != 0:
        print(f"--- {label} STDERR ---")
        print(result.stderr[-3000:])  # tail to avoid flooding
        sys.exit(1)
    return result.stdout


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 66)
    print("F4 — MULTI-PROCESS DURABLE LANGGRAPH RESTART PROOF (A1)")
    print("  Checkpointer : AsyncPostgresSaver (PostgreSQL)")
    print("  Handoff      : thread_id ONLY — no state payload")
    print("=" * 66)

    with tempfile.TemporaryDirectory(prefix="incidentgraph-durability-") as temp_dir:
        handoff_path = Path(temp_dir) / "thread-id.json"
        out1 = _run_subprocess("PROCESS 1", _P1_SCRIPT, handoff_path)

        assert "P1_WROTE_THREAD_ID_ONLY:True" in out1, (
            "Process 1 did not confirm writing thread_id to disk"
        )

        with handoff_path.open(encoding="utf-8") as handoff_file:
            data = json.load(handoff_file)
        thread_id = data["thread_id"]

    print(f"\n[HANDOFF] Passing ONLY thread_id={thread_id!r} to Process 2\n")

    out2 = _run_subprocess("PROCESS 2", _build_p2_script(thread_id))

    # Core invariant checks
    assert "P2_CHECKPOINT_FROM_DB:True" in out2, (
        "Process 2 did not confirm loading checkpoint from PostgreSQL"
    )
    assert "P2_FINAL_STATUS:resolved" in out2, "Process 2 did not reach resolved status"

    print("=" * 66)
    print("✅  MULTI-PROCESS DURABLE RESTART VERIFIED")
    print("    Process 1  →  checkpoint saved to PostgreSQL")
    print("    Process 2  ←  checkpoint loaded from PostgreSQL (thread_id only)")
    print("    Result     →  investigation resolved after human approval")
    print("=" * 66)


if __name__ == "__main__":
    main()
