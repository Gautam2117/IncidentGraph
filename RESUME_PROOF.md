# IncidentGraph — Resume Proof Ledger & Audit Provenance

Every value below is backed by explicit, reproducible execution evidence generated in this workspace session.

| Claim | Measured Value | Command / Source Artifact | Git SHA / Timestamp | Status |
|---|---|---|---|---|
| Microservices Stack | 6 demo microservices + control-plane, console, worker | `docker-compose.yml`, `deployments/helm/` | 2026-08-13T15:30:00Z | `VERIFIED` |
| Scenario Suite | 36 scenarios | `services/control-plane/app/scenarios/registry.py` | 2026-08-13T15:36:08Z | `VERIFIED` |
| RAG Retrieval Recall@5 | 100% (1.00 pgvector + FTS RRF hybrid, N=5) | `eval-results/rag_benchmark.json` | 2026-08-13T15:54:26Z | `VERIFIED` |
| Pytest Test Suite | 81 tests passing | `pytest services/control-plane/tests` | 2026-08-13T15:23:29Z | `VERIFIED` |
| Python Code Coverage | 80.12% (3,526 statements, 701 missed) | `eval-results/coverage.json` | 2026-08-13T16:42:42Z | `VERIFIED` |
| Security Static Analysis | 8,338 LOC scanned, 0 High, 0 Medium issues | `eval-results/bandit.json` | 2026-08-13T15:23:33Z | `VERIFIED` |
| Dependency Vulnerabilities | 0 vulnerabilities found | `pip-audit`, `npm audit` (apps/console) | 2026-08-13T15:23:48Z | `VERIFIED` |
| Playwright E2E Browser Test | 2 spec suites passed (19 pages, headers, CSRF boundary) | `npx playwright test` | 2026-08-13T15:27:06Z | `VERIFIED` |
| k6 Performance Load Test | 3,413 requests, 168.63 req/s, 0% failed, p95=87.44ms | `eval-results/k6-summary.json` | 2026-08-13T15:27:53Z | `VERIFIED` |
| Docker Compose End-to-End | 17 long-running containers healthy + 2 one-shot init jobs, real traffic → fault → RCA → remediation → recovery | `docker-compose.yml`, `scripts/execute_docker_e2e_proof.py`, `artifacts/docker_e2e_proof_results.json` | 2026-08-13T15:23:18Z | `VERIFIED` |
| Kubernetes / Helm Deployment | 17 pods 1/1 Running & healthy on kind cluster, smoke flow executed | `artifacts/k8s_helm_smoke_proof.json` | 2026-08-13T15:36:19Z | `VERIFIED` |
| Terraform Plan Validation | 47 resources to add in static plan (`terraform validate` passed) | `artifacts/terraform_plan_proof.json` | 2026-08-13T15:37:50Z | `VERIFIED` |
| Public Portfolio Deployment | Recruiter-facing Next.js showcase live on Vercel | `https://incidentgraph.vercel.app` | 2026-09-11 | `LIVE` |
| AWS Full-Stack Deployment | Intentionally deferred to avoid the stack's $150/month budget guardrail; static plan remains verified | `deployments/terraform/` | 2026-09-11 | `INTENTIONALLY_DEFERRED` |
| Live Model AI Reasoning Quality | Blocked due to placeholder `OPENAI_API_KEY` | `services/control-plane/app/core/config.py` | 2026-08-13T15:20:00Z | `EXTERNALLY_BLOCKED` |

---

## Technical Resume Bullet Templates & Provenance Audit

### Verified Resume Bullets (`VERIFIED`)

- **Distributed Systems & Observability**: Architected an autonomous incident investigation platform across **6 microservices**, coordinating durable multi-agent LangGraph roles with PostgreSQL state checkpointing to analyze OpenTelemetry traces, Loki logs, and Prometheus metrics.
- **Search & Retrieval Systems**: Engineered a hybrid RAG retrieval engine combining **PostgreSQL `pgvector` embeddings** and **Full-Text Search (RRF ranking)**, achieving **100% Recall@5 (N=5)** on operational runbooks and service postmortems.
- **Reliability & Quality Engineering**: Built a continuous evaluation harness with **80.12% test coverage (81 pytest backend tests passing)**, zero vulnerability dependency audits (`pip-audit`, `npm audit`), Playwright E2E browser automation across 19 console routes, and **k6 load testing (3,413 requests at 168.63 req/s with 0% failure rate and p95 latency of 87.44 ms)**.
- **Product Delivery**: Deployed a public, account-free Next.js showcase to Vercel with automated Git production delivery, deterministic evidence replay, and explicit separation from the locally verified full backend stack.
- **Cloud & Container Infrastructure**: Production-packaged with Docker Compose (**17 long-running containers plus 2 one-shot init jobs**), Helm on Kubernetes (17/17 pods 1/1 `Running` on kind cluster), and Terraform IaC (47-resource static plan).

### Bullets Marked as NOT_READY (Awaiting Live External Credentials)

- [NOT_READY] *Achieved 78%+ RCA accuracy across 36 ground-truth incidents using GPT-4o.* -> **Status**: `NOT_READY` / `EXTERNALLY_BLOCKED` (Requires live model API credentials; fake models are prohibited from generating accuracy claims).
- [NOT_READY] *Deployed the full stack to AWS ECS/Fargate in production.* -> **Status**: `NOT_READY` / `INTENTIONALLY_DEFERRED` (The public showcase is live on Vercel; the 47-resource AWS plan is static-verified but not applied).
