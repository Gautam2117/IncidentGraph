# IncidentGraph — GOD-MODE FINAL PRODUCT REQUIREMENTS DOCUMENT

**Status:** LOCKED FINAL TARGET  
**Build philosophy:** one complete system, end-to-end  
**No MVP / P0 / P1 / P2 split**  
**No feature is considered complete until integrated and validated**

---

# 1. Product definition

IncidentGraph is a production-style AI incident investigation, reliability evaluation, and controlled remediation platform built around a deliberately breakable distributed application.

It ingests or creates incidents, correlates real telemetry and deployment history, retrieves operational knowledge, coordinates multiple bounded AI reasoning roles through a durable LangGraph workflow, produces evidence-backed root-cause analyses, recommends or executes only approved sandbox remediations, and continuously benchmarks itself against reproducible ground-truth incidents.

The final product must prove deep competence across:
- TypeScript / React / Next.js
- Python / FastAPI
- distributed systems
- PostgreSQL / pgvector
- Redis / async jobs
- RAG
- agent orchestration
- tool calling
- MCP
- structured outputs
- AI evaluation
- LLM observability
- OpenTelemetry
- testing
- CI/CD
- Docker
- Kubernetes
- AWS
- Terraform
- security
- auth / RBAC
- cost / latency controls
- system design

---

# 2. Product thesis

Most AI incident tools and portfolio projects fail in one of two ways:
1. they are a chat UI over logs, or
2. they generate plausible RCAs without proving the diagnosis.

IncidentGraph is built around a stronger contract:

> **The system must show its evidence, show what it ruled out, measure whether it was correct, and fail safely when confidence is insufficient.**

---

# 3. Final user experience

A user can:

1. Open a polished engineering console.
2. See live health of a distributed demo application.
3. Trigger a controlled fault or ingest an alert.
4. Watch traces, metrics and logs degrade in real time.
5. Open an incident.
6. Start or automatically trigger an investigation.
7. Watch every investigation step:
   - incident normalization
   - service impact analysis
   - RAG retrieval
   - hypothesis generation
   - tool calls
   - evidence collection
   - contradiction search
   - verification
   - remediation planning
   - human review
8. Read an RCA with:
   - root cause
   - confidence score
   - affected services
   - causal chain
   - linked evidence
   - rejected hypotheses
   - unknowns
   - remediation plan
9. Approve a safe sandbox remediation.
10. Watch the system verify whether the remediation improved telemetry.
11. Generate a structured postmortem.
12. Compare the run against ground truth.
13. See evaluation metrics, latency and AI cost.
14. Inspect agent traces and tool permissions.
15. Re-run the same scenario after changing prompts/models/graph code.
16. See CI reject an AI regression.
17. View architecture, deployment and benchmark proof.

---

# 4. Complete final architecture

## 4.1 Frontend
- Next.js
- TypeScript
- Tailwind
- accessible component primitives
- typed API client
- live investigation updates
- error/loading/empty states
- topology visualization
- trace waterfall
- logs viewer
- metrics charts
- evaluation comparison views

## 4.2 Control plane
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- OpenAPI
- auth/session middleware
- rate limiting
- RBAC
- audit logging

## 4.3 Agent system
- LangGraph
- durable checkpoints
- resumability
- human interrupts
- bounded tool/model budgets
- structured state
- explicit agent roles:
  - Incident Coordinator
  - Knowledge Retriever
  - Hypothesis Investigator
  - Evidence Analyst
  - Contradiction / Skeptic Verifier
  - Remediation Planner
  - Outcome Verifier
  - Postmortem Composer
- agents are nodes/subgraphs, NOT unbounded chatty swarm agents

## 4.4 RAG
- PostgreSQL
- pgvector
- Postgres FTS
- hybrid retrieval
- Reciprocal Rank Fusion
- metadata filters
- optional reranker only after measured benefit
- retrieval diagnostics
- source versioning
- injection-resistant ingestion
- retrieval benchmark

## 4.5 Async jobs
- Redis
- Celery
- idempotent tasks
- retry/backoff
- cancellation
- dead/failure persistence
- resumable graph state

## 4.6 Demo distributed system
Required services:
- gateway
- auth
- orders
- payments
- inventory
- notifications
- PostgreSQL
- Redis where application behavior justifies it

## 4.7 Telemetry
- OpenTelemetry SDKs
- OpenTelemetry Collector
- Prometheus
- Tempo
- Loki
- Grafana
- trace-log correlation
- service version/deployment attributes
- IncidentGraph's own AI/tool/retrieval spans

## 4.8 MCP
- MCP-compatible operations server
- authenticated/scoped
- read-only telemetry + knowledge tools
- audited
- no arbitrary shell / SQL / URL fetching

## 4.9 Testing
- Pytest
- contract tests
- integration tests
- Testcontainers where valuable
- Playwright
- security tests
- prompt-injection tests
- k6
- deterministic model fakes
- live-model eval suite

## 4.10 DevOps
- Docker
- Docker Compose
- Kubernetes manifests + Helm chart
- local Kubernetes validation via kind/k3d
- GitHub Actions
- CodeQL or equivalent static analysis
- dependency scan
- container scan
- SBOM generation where practical

## 4.11 Cloud
- Terraform
- AWS
- VPC/networking
- container registry
- managed PostgreSQL where feasible
- container compute
- load balancer
- secret management
- logging/monitoring
- HTTPS/custom domain if available
- budget guardrails

The hosted architecture may use ECS/Fargate for cost efficiency while Kubernetes support is validated locally through Helm/kind. This is intentional: Kubernetes is learned and implemented without forcing an expensive EKS portfolio deployment.

---

# 5. Complete demo system behavior

Normal path:

`Client -> Gateway -> Auth -> Orders -> Inventory -> Payments -> Database -> Notification`

All requests propagate W3C trace context.

Services expose:
- `/health/live`
- `/health/ready`
- `/version`
- business endpoints needed for scenarios

Structured logs include:
- timestamp
- service
- severity
- message
- trace_id when available
- span_id when available
- deployment version
- environment

Metrics include:
- request count
- request duration
- errors
- dependency duration
- DB pool utilization
- queue depth where applicable
- retry count
- timeout count
- process resource metrics where meaningful

---

# 6. Complete incident scenario library

The final repository must contain at least 30 reproducible scenarios and target 40+ when stable.

Mandatory categories:
1. DB connection pool exhaustion
2. missing DB index / slow query
3. N+1 query
4. database lock contention
5. bad application deployment
6. bad configuration deployment
7. payment latency
8. payment 5xx burst
9. payment throttling
10. auth latency
11. auth error spike
12. expired auth signing/config error simulation
13. inventory timeout
14. inventory stale response
15. gateway rate-limit misconfiguration
16. retry storm
17. CPU saturation
18. memory pressure
19. Redis unavailable
20. Redis latency
21. queue backlog
22. notification worker failure
23. DNS/network simulation
24. dependency partial failure
25. dependency cascading failure
26. timeout configuration regression
27. circuit-breaker open scenario
28. misleading correlated signal
29. multiple simultaneous weak signals
30. insufficient-evidence / unknown root cause
31. recovered-before-investigation
32. repeat incident matching historical postmortem
33. telemetry gap
34. deployment with no causal impact
35. prompt-injection content in operational knowledge
36. tool timeout during investigation

Each scenario:
- versioned
- seeded
- deterministic enough for repeatability
- reversible
- bounded
- cleans itself up
- stores ground truth outside agent context

---

# 7. Alert and incident ingestion

Support:
- scenario-generated alerts
- manual incident creation
- generic webhook alert ingestion

Normalized alert schema:
- source
- severity
- service
- event_type
- observed_at
- labels
- summary
- raw_payload_hash

Webhook security:
- secret/signature
- rate limit
- size limit
- schema validation
- replay protection where feasible

---

# 8. Investigation graph

## 8.1 State

The durable state includes:
- incident
- context
- affected services
- retrieval results
- hypotheses
- evidence
- contradictory evidence
- rejected hypotheses
- tool call ledger
- model call ledger
- budgets
- graph version
- prompt versions
- model/provider versions
- remediation plan
- remediation execution result
- final RCA
- postmortem
- errors
- checkpoint metadata

## 8.2 Workflow

`Normalize -> Scope -> Retrieve -> Hypothesize -> Gather -> Analyze -> Skeptic Verify -> Gather More (bounded loop) -> RCA -> Remediation Plan -> Human Approval -> Sandbox Remediation -> Outcome Verify -> Postmortem -> Complete`

Alternate routes:
- insufficient evidence -> low-confidence RCA
- tool/model failure -> recover/retry -> failed state
- human rejection -> request evidence / modify plan
- remediation rejected -> no execution, still close RCA
- remediation ineffective -> rollback where supported

## 8.3 Explicit roles

### Incident Coordinator
Maintains state and determines next bounded step.

### Knowledge Retriever
Builds retrieval queries and selects evidence-worthy runbook/postmortem context.

### Hypothesis Investigator
Produces multiple testable causal hypotheses.

### Evidence Analyst
Maps telemetry to or against hypotheses.

### Skeptic Verifier
Actively searches for contradictions and unsupported leaps.

### Remediation Planner
Produces safe sandbox-only action plan with expected outcome and rollback.

### Outcome Verifier
Measures telemetry after approved remediation.

### Postmortem Composer
Creates structured timeline, root cause, contributing factors and prevention items.

These roles may share a model/provider but have isolated prompts/schemas and explicit responsibilities.

---

# 9. Operational tools

Mandatory internal tools:
- metrics.query
- metrics.compare_baseline
- logs.search
- traces.get
- traces.search
- deployments.list
- topology.get
- knowledge.search
- incidents.search_history
- configs.get_safe_snapshot
- scenario.get_metadata_without_ground_truth
- remediation.preview
- remediation.execute_sandbox
- remediation.rollback_sandbox
- remediation.verify_outcome

All tool inputs:
- typed
- validated
- bounded
- audited
- timeout protected

AI never gets:
- unrestricted shell
- arbitrary SQL
- arbitrary filesystem
- arbitrary HTTP
- cloud credentials
- arbitrary Kubernetes exec
- secret values

---

# 10. Controlled remediation

The final product DOES include remediation, but only in the sandbox/demo environment.

Examples:
- rollback demo service version
- restore safe configuration
- restart sandbox worker
- reset simulated pool configuration
- clear simulated queue backlog
- disable injected fault

Requirements:
- plan generated before execution
- deterministic allow-list maps action types to trusted implementation functions
- human approval required
- impact preview
- rollback available where applicable
- audit event
- outcome verification
- AI cannot invent new executable action types

This provides safe "agent acts on system" depth without unsafe autonomous infrastructure control.

---

# 11. Knowledge system

Document types:
- runbook
- postmortem
- architecture
- deployment procedure
- service ownership
- known failure pattern
- SLO/SLA documentation

Required capabilities:
- upload
- validation
- text extraction
- chunking
- versioning
- re-index
- delete/archive
- semantic search
- lexical search
- hybrid fusion
- source metadata
- retrieval debugger
- relevancy annotations
- red-team fixtures

---

# 12. RAG evaluation

Maintain a query/relevance dataset.

Metrics:
- Recall@K
- Precision@K
- MRR
- nDCG where useful
- source diversity
- service-filter correctness

Run:
- vector-only
- lexical-only
- hybrid

Keep benchmark evidence showing why hybrid retrieval is chosen.

If a reranker is added, prove it improves benchmark quality enough to justify latency/cost.

---

# 13. AI evaluation system

The evaluation system is a first-class subsystem.

Required metrics:
- root-cause category accuracy
- primary-service accuracy
- causal-chain correctness
- evidence recall
- evidence precision
- unsupported-claim rate
- tool-choice correctness
- tool-parameter correctness
- redundant tool-call rate
- verifier contradiction quality
- safe-uncertainty behavior
- remediation plan correctness
- remediation outcome success
- retrieval Recall@K
- latency p50/p95
- time-to-first-evidence
- model calls
- tool calls
- token usage
- estimated cost
- budget compliance

Results stored immutably and versioned by:
- git SHA
- scenario versions
- prompt versions
- graph version
- model/provider
- retrieval config
- timestamp

---

# 14. Model/provider architecture

Implement provider abstraction.

Support at minimum:
- one primary remote LLM provider
- one alternate provider OR local/Ollama-compatible adapter
- deterministic fake provider for tests

Capabilities abstracted:
- chat/completions
- structured outputs
- tool calling
- embeddings

Model selection policy:
- cheaper model for classification/extraction when benchmark supports it
- stronger reasoning model for hypothesis/verifier where needed
- explicit fallback
- timeout
- cost accounting

No provider-specific code leaks into domain layer.

---

# 15. AI observability

Trace:
- investigation
- graph node
- model call
- tool call
- retrieval
- scoring
- remediation
- outcome verification

Metrics:
- investigation duration
- model duration
- tool duration
- tool error rate
- token count
- cost estimate
- retries
- unsupported claims
- eval accuracy
- retrieval quality

Logs:
- structured
- redacted
- correlated

Dashboard:
- model/provider
- prompt/graph version
- cost
- latency
- failure mode
- tool usage

---

# 16. Human-in-the-loop

Human review can:
- approve RCA
- reject RCA
- request more evidence
- annotate root cause
- approve/reject remediation
- edit remediation parameters within safe bounds
- approve postmortem

LangGraph must pause durably and resume across process restart.

---

# 17. Postmortem generation

Structured postmortem:
- incident summary
- severity
- timeline
- impact
- root cause
- contributing factors
- evidence
- detection gap
- remediation performed
- recovery verification
- prevention items
- follow-up actions
- unresolved unknowns

Export:
- Markdown
- JSON
- optional PDF later only if needed

Generated postmortems can enter knowledge base after explicit review.

---

# 18. Historical learning

Support search over previous incidents:
- semantic similarity
- service/category filters
- time
- prior resolution
- postmortem links

Historical incidents may be retrieved as evidence/context but cannot override current telemetry.

---

# 19. Auth and RBAC

Roles:
- Viewer
- Engineer
- Admin

Viewer:
- view dashboards/incidents/evals/RCAs

Engineer:
- create/trigger scenarios
- start investigation
- review RCA
- approve sandbox remediation

Admin:
- manage users
- manage knowledge
- manage model/retrieval config
- manage webhook credentials

Authentication:
- secure session or JWT
- hashed credentials or OAuth
- expiry
- server-side authorization

---

# 20. Security

Mandatory:
- CSRF protection where applicable
- rate limiting
- input validation
- upload validation
- content size limits
- secret management
- dependency scanning
- container scanning
- static analysis
- secure headers
- audit log
- prompt injection tests
- tool boundary tests
- RBAC tests
- webhook auth
- no secrets in telemetry
- no sensitive full prompt logging by default

Threat model document required.

---

# 21. Data layer

Required entities:
- users
- workspaces (single default workspace supported; schema future-proofs isolation)
- incidents
- incident_events
- investigations
- investigation_events
- hypotheses
- evidence
- tool_calls
- model_calls
- remediation_plans
- remediation_executions
- knowledge_documents
- knowledge_chunks
- deployments
- service_catalog
- scenarios
- scenario_runs
- evaluation_runs
- evaluation_results
- prompt_versions
- graph_versions
- audit_events
- webhook_sources

Use UUIDs, timestamps, constraints, indexes and Alembic migrations.

---

# 22. API

Versioned `/api/v1`.

Required groups:
- auth
- users/admin
- services/topology
- incidents
- investigations
- evidence
- knowledge
- scenarios
- remediation
- evaluations
- postmortems
- webhooks
- audit
- health/version

API contracts documented through OpenAPI.

---

# 23. UI routes

Mandatory:
- `/`
- `/login`
- `/dashboard`
- `/incidents`
- `/incidents/[id]`
- `/investigations/[id]`
- `/topology`
- `/knowledge`
- `/knowledge/[id]`
- `/scenarios`
- `/scenario-runs/[id]`
- `/evaluations`
- `/evaluations/[id]`
- `/evaluations/compare`
- `/audit`
- `/settings`
- `/settings/models`
- `/settings/retrieval`
- `/settings/webhooks`

---

# 24. UI standards

The UI is a serious engineering console.

Mandatory components:
- service topology
- severity/status badges
- metrics charts
- trace waterfall
- log viewer
- investigation timeline
- tool call inspector
- hypothesis comparison
- evidence explorer
- RCA document
- remediation approval panel
- outcome verification panel
- postmortem viewer
- retrieval debugger
- evaluation matrix
- regression diff
- audit log
- system health popover
- command/search palette

No fake data masquerading as live.

---

# 25. Docker

Local canonical environment:
- web
- api
- worker
- postgres + pgvector
- redis
- demo services
- otel collector
- prometheus
- tempo
- loki
- grafana
- scenario runner
- optional local model runtime if configured

Single documented bootstrap.

---

# 26. Kubernetes

Implement:
- namespace
- ConfigMaps
- Secrets references
- Deployments
- Services
- Ingress
- readiness/liveness
- resource requests/limits
- autoscaling where sensible
- Helm chart
- environment values
- local validation with kind or k3d
- smoke test

Do NOT claim production EKS deployment unless actually deployed there.

---

# 27. AWS + Terraform

Terraform modules:
- network
- security groups
- ECR
- compute
- ALB
- RDS
- secret/config
- DNS/TLS where used
- IAM least privilege
- observability/platform logging

Hosted target may use ECS Fargate for cost efficiency.

Required:
- fmt
- validate
- plan in CI
- documented apply
- migrations
- smoke test
- rollback
- destroy instructions
- budget/cost note

---

# 28. CI/CD

Workflows:
- pull request quality gate
- unit tests
- type/lint
- integration tests
- contract tests
- security/static analysis
- container scan
- Docker builds
- Playwright
- AI smoke eval
- full scheduled/manual eval
- regression comparison
- Terraform fmt/validate/plan
- deployment workflow
- post-deploy smoke

An intentionally bad prompt/graph change must be demonstrably able to fail an eval gate.

---

# 29. Performance and reliability

Requirements:
- pagination
- bounded query result sizes
- DB indexes
- retry/backoff
- timeouts
- idempotency
- deduped investigation starts
- durable checkpoints
- cancellation
- health/readiness
- graceful degradation
- error boundaries
- partial evidence persistence

Benchmark:
- API
- retrieval
- telemetry queries
- investigation orchestration excluding provider variance
- controlled concurrent workload

---

# 30. Cost engineering

Track:
- per investigation
- per model
- per scenario
- per benchmark run

Controls:
- budgets
- model routing
- caching
- embedding dedup
- context compression
- tool result summarization
- rate limits
- evaluation scheduling

---

# 31. Documentation

Required:
- README
- architecture
- threat model
- evaluation methodology
- deployment
- local runbook
- ADRs
- API docs
- interview notes
- resume proof
- known limitations
- cost notes

ADRs required for:
- LangGraph
- pgvector
- hybrid retrieval
- Redis/Celery
- observability stack
- MCP
- read-only tool boundary
- remediation boundary
- Kubernetes support
- AWS ECS hosted target
- model provider abstraction
- eval-gated AI changes

---

# 32. Public demo

The public/demo environment must have:
- seeded workspace
- safe demo user or public read-only mode
- rate-limited scenario triggering
- reset capability
- no real infrastructure access
- no real secrets
- predictable guided demo
- status indicators
- benchmark page

---

# 33. README benchmark proof

README may display numbers only from a committed or release-linked evaluation artifact.

Required proof:
- number of instrumented services
- scenario count
- RCA accuracy
- service accuracy
- evidence metrics
- retrieval metrics
- latency
- cost
- tool-use correctness
- unsupported-claim rate

---

# 34. Completion rule

IncidentGraph is 100% complete only when EVERY mandatory item in `FULL_BUILD_TRACKER.md` is complete and every row in `VALIDATION_MATRIX.md` is PASS.

No "phase complete" counts as product complete.

The only acceptable unfinished items are external blockers that cannot be solved in code (for example missing cloud credentials). Such items must be explicitly marked BLOCKED, not DONE.

