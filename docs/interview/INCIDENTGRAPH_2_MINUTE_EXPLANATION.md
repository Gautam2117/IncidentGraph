# IncidentGraph — 2-Minute Elevator Pitch & Technical Summary

## Pitch Statement (30 Seconds)
"IncidentGraph is an autonomous AI SRE platform designed to investigate distributed system incidents, synthesize evidence-backed Root Cause Analyses (RCAs), and execute safe, human-approved remediations. 

Unlike traditional AI wrappers that hallucinate RCA causes or leak test data, IncidentGraph uses a durable, multi-agent LangGraph workflow with a PostgreSQL state checkpointer, a hybrid RAG search engine (pgvector + Full-Text Search + RRF), and a deterministic evaluation harness that continuously tests AI reasoning without prompt leakage."

---

## Technical Summary (90 Seconds)

1. **System Architecture**:
   - **Frontend**: Next.js 16 / React 19 engineering console.
   - **Control Plane**: FastAPI (Python 3.12) with AsyncSQLAlchemy, Pydantic v2 validation, Celery workers, and Redis broker.
   - **Demo System**: 6 breakable Python microservices (`gateway`, `auth`, `orders`, `payments`, `inventory`, `notifications`) emitting OpenTelemetry traces, Prometheus metrics, and Loki logs.

2. **Durable Multi-Agent Engine**:
   - Uses LangGraph to orchestrate explicit SRE roles: **Triage & Topology Node**, **Telemetry & Evidence Gathering Node**, **Skeptic Verifier Node** (which tests for contradictions and rejects unfounded claims), and **RCA Synthesizer Node**.
   - State is checkpointed to PostgreSQL after every step. If worker nodes crash or require human review, the graph resumes seamlessly without losing investigation context.

3. **Hybrid RAG & Evidence Grounding**:
   - Combines vector embeddings (`pgvector`) and lexical search (`websearch_to_tsquery`) using Reciprocal Rank Fusion (RRF).
   - Every RCA claim is strictly bound to persisted evidence IDs (`telemetry_evidence`, `knowledge_docs`). Unsupported claims are flagged or rejected.

4. **Remediation Safety**:
   - Eliminates arbitrary shell/SQL execution risks by enforcing an allow-listed set of deterministic sandbox actions (e.g., `scale_pool`, `restart_service`).
   - Requires explicit human approval via API/UI before any mutation command is dispatched.

5. **Evaluation & Provenance**:
   - Features an automated AI evaluation engine and regression gate (`.github/workflows/ai_regression_gate.yml`).
   - Local stack verified across 17 Docker containers, 17 Kubernetes workloads on a local `kind` cluster, and 47 Terraform IaC resources.
