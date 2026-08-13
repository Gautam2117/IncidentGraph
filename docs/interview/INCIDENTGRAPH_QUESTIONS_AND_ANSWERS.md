# IncidentGraph — SRE & AI Engineering Interview Q&A

This document prepares you for high-level technical questions spanning multi-agent architecture, state checkpointing, RAG hybrid search, security, evaluation leakage, and cloud infrastructure.

---

## 1. LangGraph & Multi-Agent Architecture

### Q: Why did you choose LangGraph instead of a standard ReAct loop or AutoGen?
**Answer**: 
"Standard ReAct loops in plain Python often suffer from uncontrolled state mutation and lack explicit checkpointing. AutoGen's conversational multi-agent paradigm can lead to infinite chat loops between agents without clear state termination. 

LangGraph allowed us to define a **deterministic directed acyclic graph (DAG)** with explicit state schemas (`InvestigationState`). Each node represents a distinct SRE role (Triage, Telemetry Gathering, Skeptic Verification, RCA Synthesis), and transitions are controlled by strict conditional edges. This guarantees bounded execution and predictable tool access."

---

### Q: How does PostgreSQL state checkpointing work when worker nodes crash?
**Answer**: 
"We implement a PostgreSQL checkpointer using AsyncSQLAlchemy. At the boundary of every node execution, the entire `InvestigationState` (including hypotheses, evidence IDs, step count, and current node position) is serialized and stored in PostgreSQL. 

If a Celery worker dies mid-investigation (or during an asynchronous human review pause), another worker picks up the job, queries the latest checkpoint by `incident_id`, and resumes execution directly from the next node without re-executing previous steps or making redundant LLM API calls."

---

## 2. Telemetry, RAG & Search Engine

### Q: How do pgvector, Full-Text Search, and RRF work together in IncidentGraph?
**Answer**: 
"Dense vector embeddings (`pgvector` with cosine distance `<=>`) excel at capturing semantic intent, like matching 'high response latency' to 'performance degradation'. However, vector search often struggles with exact keyword matching like error codes (`ERR_503_DB_CONN`) or specific microservice names.

To solve this, we combine `pgvector` with PostgreSQL Full-Text Search using `websearch_to_tsquery('english', query)`. We merge both result sets using Reciprocal Rank Fusion (RRF):
$$RRF\\_Score(d) = \\sum_{m \\in M} \\frac{1}{k + r_m(d)}$$
where $k=60$. RRF ranks documents that appear near the top of *either* search method without requiring score normalization between vector distance and lexical rank."

---

### Q: How do you prevent hallucinations in the RCA report?
**Answer**: 
"We use three structural safeguards:
1. **Evidence ID Grounding**: Every telemetry metric, log line, or span retrieved by the tools is assigned a unique `evidence_id`. The RCA Synthesizer node is constrained by Pydantic output validation to link every claim to a valid `evidence_id`.
2. **Skeptic Verifier Node**: Before RCA synthesis, the Skeptic node cross-checks telemetry metrics against proposed hypotheses. If telemetry contradicts a hypothesis (e.g., normal CPU usage when a memory leak was claimed), the hypothesis is rejected.
3. **Low-Confidence Fallback**: If gathered evidence is insufficient or contradictory, the agent returns an explicit `INCONCLUSIVE` status instead of guessing."

---

## 3. Ground-Truth Leakage & AI Evaluation

### Q: Tell me about the ground-truth leakage incident and how you fixed it.
**Answer**: 
"During our initial benchmark runs across 36 scenarios, our evaluation suite reported a suspicious '100% RCA accuracy'. During an adversarial audit of the prompt logs, we discovered that scenario definitions included ground-truth root-cause fields that were being accidentally passed into the context window of the evaluation runner. The model wasn't actually investigating telemetry; it was reading the answer from the prompt!

We took immediate action:
1. **Revoked contaminated artifacts**: Marked all historical 100% eval runs as `REVOKED_CONTAMINATED` in the evaluation registry.
2. **Built Ground-Truth Sanitization**: Updated `ScenarioDefinition.get_safe_metadata()` to strictly strip all ground-truth fields before returning metadata to the agent.
3. **Added Leakage Tests**: Added unit tests (`test_scenarios_metadata.py`) verifying that ground-truth fields can never leak into agent contexts.
4. **Automated CI Regression Gate**: Added `.github/workflows/ai_regression_gate.yml` to automatically reject code changes that cause leakage or metric regression."

---

## 4. Security & Remediation Safety

### Q: How do you ensure an AI agent doesn't execute `rm -rf /` or drop production database tables?
**Answer**: 
"We enforce three strict security boundaries:
1. **No Arbitrary Shell or SQL**: Tools do not accept raw SQL strings or shell command lines. All remediation parameters pass through rigid Pydantic models with regular expression constraints.
2. **Deterministic Allow-Listed Actions**: Remediation actions are limited to pre-approved sandbox functions (`scale_pool`, `restart_service`).
3. **Human-in-the-Loop Review**: Every remediation plan sets `requires_human_approval: true`. Execution endpoints return `403 Forbidden` unless a valid human reviewer approval decision (`APPROVED`) is recorded in PostgreSQL."

---

## 5. Infrastructure & Operations

### Q: How is the system deployed across Docker, Kubernetes, and AWS?
**Answer**: 
"IncidentGraph supports three infrastructure targets:
- **Docker Compose**: 17 containers for complete single-node local development, including microservices, control plane, Celery worker, PostgreSQL, Redis, and OpenTelemetry stack.
- **Kubernetes / Helm**: Chart located in `deployments/helm/incidentgraph`. Verified on a local `kind` cluster with 17/17 pods `1/1 Running` and `securityContext` configured with explicit non-root UIDs.
- **AWS ECS / Fargate (Terraform)**: Modular Terraform IaC in `deployments/terraform` deploying VPC across 2 AZs, ECS Fargate services, multi-AZ RDS PostgreSQL with `pgvector`, ElastiCache Redis, ALB with HTTPS, and Secrets Manager. Static plan validated with 47 resources to add."
