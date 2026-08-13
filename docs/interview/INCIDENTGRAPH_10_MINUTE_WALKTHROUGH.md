# IncidentGraph — 10-Minute Deep-Dive Technical Walkthrough

This document provides a minute-by-minute architectural walkthrough of IncidentGraph for technical interviews, system design discussions, and Staff/Principal SRE reviews.

---

## Minute 1: Problem Space & Motivation
"Traditional SRE incident response under high-severity outages suffers from three key pain points:
1. **Telemetry Overload**: Engineers waste critical minutes sifting through raw Loki logs, Tempo traces, and Prometheus dashboards.
2. **AI Hallucinations**: Standard LLM prompts generate confident-sounding root causes that lack empirical grounding or contradict system topology.
3. **Unsafe Automation**: Unchecked LLM agents executing raw shell or SQL commands risk causing secondary outages.

IncidentGraph was designed to solve this by building a **durable, evidence-grounded multi-agent graph** with strict human-in-the-loop safety and reproducible evaluation benchmarks."

---

## Minutes 2–3: Architecture & Telemetry Pipeline
"The system is organized into three distinct layers:
1. **Target Environment**: 6 microservices (`gateway`, `auth`, `orders`, `payments`, `inventory`, `notifications`) instrumented with OpenTelemetry. Telemetry flows into an OpenTelemetry Collector, which exports to Prometheus (metrics), Loki (logs), and Tempo (traces).
2. **Control Plane & Data Layer**: Built with Python 3.12, FastAPI, AsyncSQLAlchemy 2, and PostgreSQL 16 + `pgvector`. Redis handles Celery task dispatch and caching.
3. **Agent Graph Layer**: A multi-role LangGraph engine executing asynchronous nodes."

```
[ Gateway ] -> [ Orders ] -> [ Payments ]
     |             |              |
     +------ OpenTelemetry Collector ------+
                     |
     [ Prometheus ]  [ Loki ]  [ Tempo ]
                     |
             [ Control Plane ]
                     |
         [ Durable LangGraph Engine ]
```

---

## Minutes 4–5: Multi-Agent Investigation Flow & Skeptic Verifier
"When an incident is ingested (via API, manual trigger, or chaos scenario):
1. **Triage & Topology Node**: Inspects the incident title/target service, queries service topology from database models, and sets initial investigation hypotheses.
2. **Telemetry & Evidence Gathering Node**: Queries Prometheus metrics (HTTP error rates, p95 latency), Loki logs (error traces), and Tempo spans to extract empirical evidence.
3. **Skeptic Verifier Node**: This is a critical quality control node. It cross-references gathered telemetry evidence against the initial hypotheses. If telemetry shows normal latency or 0% error rate for a hypothesized service, the Skeptic verifier **explicitly invalidates the hypothesis** and demands further tool queries.
4. **RCA Synthesizer Node**: Synthesizes the final Root Cause Analysis report. Every claim must reference a valid `evidence_id`. If evidence is inconclusive, the synthesizer returns an explicit low-confidence assessment rather than hallucinating."

---

## Minutes 6–7: Durable State Checkpointing & Human-in-the-Loop Remediation
"Two major reliability features govern graph execution:
1. **PostgreSQL Checkpointer**: Every state transition in LangGraph is serialized to PostgreSQL. If the worker process dies or restarts mid-investigation, the graph resumes from the exact node and step without restarting or re-executing LLM calls.
2. **Remediation Review**: The agent generates a candidate remediation plan (e.g., `scale_pool`, `restart_service`). The plan sets `requires_human_approval: true` and transitions the incident to `AWAITING_REVIEW`.
   - The human operator reviews the plan in Next.js UI or API and posts an approval decision (`APPROVED` or `REJECTED`).
   - Only after explicit approval does the executor run the deterministic sandbox action and compare before/after telemetry to verify system recovery."

---

## Minutes 8–9: Hybrid RAG & The Ground-Truth Leakage Incident
"Our retrieval engine uses PostgreSQL `pgvector` for semantic search (embedding operational runbooks and postmortems) and PostgreSQL Full-Text Search (`websearch_to_tsquery`) for exact keyword matches. The results are merged using Reciprocal Rank Fusion (RRF):
$$RRF\\_Score(d) = \\sum_{m \\in M} \\frac{1}{k + r_m(d)}$$

### Ground-Truth Leakage Case Study (Great Interview Story!)
During initial benchmark development, the offline eval runner accidentally leaked ground-truth scenario descriptions into the agent's context prompt. The system achieved a 'fake' 100% RCA accuracy.

During adversarial audit, we discovered that the agent was simply reading the ground-truth text rather than reasoning over telemetry. We immediately:
1. Revoked all contaminated evaluation artifacts (`REVOKED_CONTAMINATED`).
2. Implemented strict metadata stripping in `get_safe_metadata()` to purge ground-truth fields before LLM context injection.
3. Built an automated AI regression gate (`.github/workflows/ai_regression_gate.yml`) that fails any PR where prompt leakage or metric degradation occurs."

---

## Minute 10: Infrastructure, Security & Verification
"The entire stack is verified end-to-end:
- **81 backend pytest tests passing** (80% coverage).
- **Bandit static analysis clean** (0 High/Medium issues).
- **k6 load test**: 5,101 requests at 168 req/s with 0% failure and p95 latency of 84.41 ms.
- **Playwright E2E browser tests**: Passing across all 19 console routes.
- **Docker Compose**: 17 containers healthy (`scripts/execute_docker_e2e_proof.py`).
- **Kubernetes / Helm**: 17/17 pods 1/1 `Running` on a local `kind` cluster.
- **Terraform**: 47-resource static plan validated.

External execution state is explicitly tracked as `EXTERNALLY_BLOCKED` for live LLM API keys and AWS Cloud deployment, demonstrating complete provenance integrity."
