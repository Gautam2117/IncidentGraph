# ADR-001: Multi-Role Durable LangGraph Architecture

## Context
Generic chat-oriented agent loops often suffer from non-deterministic execution, prompt entanglement, difficult observability, and an inability to safely resume after human intervention or worker crashes.

## Decision
We use **LangGraph** with explicit nodes representing bounded reasoning roles (Incident Coordinator, Knowledge Retriever, Hypothesis Investigator, Evidence Analyst, Skeptic Verifier, Remediation Planner, Outcome Verifier, Postmortem Composer) backed by durable Postgres/Redis checkpoints.

## Status
Accepted

## Consequences
- Every investigation step is an explicit node transition with typed inputs and outputs.
- Human review (RCA & Remediation approval) pauses execution durably across service restarts.
- Strict token and tool budgets can be enforced at the graph runtime layer.
