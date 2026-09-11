# IncidentGraph — Autonomous Incident Investigation, AI Evaluation & Controlled Remediation Platform

IncidentGraph is a production-grade, multi-agent SRE platform built to autonomously investigate distributed system incidents, synthesize evidence-backed Root Cause Analyses (RCAs), enforce durable human-in-the-loop remediation safety, and continuously benchmark AI reasoning quality against versioned ground-truth scenarios.

[**Launch the public interactive showcase →**](https://incidentgraph.vercel.app)

The hosted showcase is recruiter-friendly and requires no account. It replays deterministic proof data through the real console UI so visitors can trace a SEV-1, inspect evidence lineage, explore topology, review evaluation results, and examine a human-gated remediation plan. It is clearly labeled and does not present fixture output as a live-model benchmark.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Clients ["User & Observability Interfaces"]
        UI["Next.js 16 Engineering Console"]
        MCP["Model Context Protocol (MCP) Server"]
    end

    subgraph ControlPlane ["Control Plane & Orchestration"]
        API["FastAPI Control Plane Service"]
        DB[("PostgreSQL + pgvector")]
        Redis[("Redis Cache & Task Broker")]
        Worker["Celery Worker Nodes"]
    end

    subgraph AgentSystem ["Durable LangGraph Multi-Agent Engine"]
        Triage["Triage & Topology Node"]
        Investigate["Telemetry & Evidence Gathering Node"]
        Skeptic["Skeptic Verifier & Contradiction Node"]
        RCA["RCA Synthesizer Node"]
        Remediation["Remediation Plan Generator"]
    end

    subgraph TelemetryStack ["Observability Stack"]
        Otel["OpenTelemetry Collector"]
        Prom["Prometheus Metrics"]
        Loki["Loki Logs"]
        Tempo["Tempo Distributed Traces"]
        Grafana["Grafana Dashboards"]
    end

    subgraph DemoApp ["Target Microservice Environment"]
        GW["Gateway Service"]
        Auth["Auth Service"]
        Orders["Orders Service"]
        Payments["Payments Service"]
        Inv["Inventory Service"]
        Notif["Notifications Service"]
    end

    UI --> API
    MCP --> API
    API --> DB
    API --> Redis
    Worker --> Redis
    Worker --> AgentSystem
    AgentSystem --> DB
    AgentSystem --> TelemetryStack
    DemoApp --> Otel
    Otel --> Prom
    Otel --> Loki
    Otel --> Tempo
    Prom --> Grafana
    Loki --> Grafana
    Tempo --> Grafana
```

---

## Key Features

1. **Durable Multi-Agent Incident Graph**: Built using LangGraph with PostgreSQL checkpointing. Supports checkpoint save/restore across service restarts and durable human-in-the-loop pauses.
2. **Hybrid RAG Retrieval Engine**: Combines `pgvector` semantic embeddings with PostgreSQL Full-Text Search (FTS) using Reciprocal Rank Fusion (RRF) for operational runbooks, postmortems, and service topology documents.
3. **Deterministic Sandbox Remediation**: Strict Pydantic schema validation preventing arbitrary command/shell injection, requiring explicit human review and approval for allow-listed mitigation actions.
4. **Comprehensive AI Evaluation Suite**: Automated benchmark metrics evaluating RCA accuracy, primary service identification, evidence recall, unsupported claim rate, tool-use correctness, and latency/token cost tracking.
5. **Full Observability & Telemetry Integration**: Native OpenTelemetry collector pipeline exporting metrics to Prometheus, logs to Loki, and traces to Tempo.
6. **Production Infrastructure & Deployment**: Containerized with Docker Compose (17 long-running containers plus 2 one-shot init jobs), packaged as a Helm chart for Kubernetes (17 healthy workloads), and defined via AWS ECS/Fargate Terraform IaC.

---

## Verified System Benchmarks & Provenance

All metrics below reflect actual execution results recorded in local proof artifacts.

`npm run verify:claims` is a fail-closed CI gate: it cross-checks the featured numbers below against the committed JSON evidence, validates the six services' telemetry wiring, rejects stale headline metrics, and confirms no authentication token remains in the load-test artifact.

| Metric | Measured Value | Provenance Source | Status |
|---|---|---|---|
| **RAG Recall@5** | 100% (1.00 hybrid RRF, N=5) | [`eval-results/rag_benchmark.json`](./eval-results/rag_benchmark.json) | `VERIFIED` |
| **Backend Test Suite** | 81 tests passing (100% pass) | `pytest services/control-plane/tests` | `VERIFIED` |
| **Python Code Coverage** | 80% measured coverage | `pytest --cov=app` | `VERIFIED` |
| **Security Analysis** | 8,338 LOC scanned, 0 High/Medium | [`eval-results/bandit.json`](./eval-results/bandit.json) | `VERIFIED` |
| **Dependency Audits** | 0 vulnerabilities | `pip-audit`, `npm audit` | `VERIFIED` |
| **Public Showcase E2E** | 3 critical journeys passing | `npm run test:e2e:showcase` | `VERIFIED` |
| **Vercel Production** | Public HTTPS deployment | [incidentgraph.vercel.app](https://incidentgraph.vercel.app) | `LIVE` |
| **k6 Load Performance** | 3,413 reqs, 168.63 req/s, 0% failed, p95=87.44ms | [`eval-results/k6-summary.json`](./eval-results/k6-summary.json) | `VERIFIED` |
| **Playwright E2E Flow** | 2 spec suites passed across 19 pages | `npx playwright test` | `VERIFIED` |
| **Docker Compose Stack** | 17 runtime containers healthy; 2 init jobs complete | [`artifacts/docker_e2e_proof_results.json`](./artifacts/docker_e2e_proof_results.json), [`docker-compose.yml`](./docker-compose.yml) | `VERIFIED` |
| **Kubernetes / Helm** | 17/17 pods 1/1 `Running` on kind cluster | [`artifacts/k8s_helm_smoke_proof.json`](./artifacts/k8s_helm_smoke_proof.json) | `VERIFIED` |
| **Terraform IaC Plan** | 47 resources to add (static plan) | [`artifacts/terraform_plan_proof.json`](./artifacts/terraform_plan_proof.json) | `VERIFIED` |

---

## Explicit External Blockers

| Feature | External Status | Reason |
|---|---|---|
| **Live AI Reasoning Benchmark** | `EXTERNALLY_BLOCKED` | Configured `OPENAI_API_KEY` is a dummy placeholder (`mock-key-or-set-your-key`). Fake model providers are prohibited from generating live benchmark claims. |
| **AWS Cloud Live Apply** | `INTENTIONALLY_DEFERRED` | `terraform plan` is static-verified (47 resources). The full multi-AZ stack has an explicit $150/month budget guardrail and requires a production domain/TLS setup, so it is not silently provisioned for a portfolio demo. |

---

## Quick Start (Local Docker Compose)

```bash
# 1. Clone repository
git clone https://github.com/Gautam2117/IncidentGraph.git
cd IncidentGraph

# 2. Copy environment blueprint
cp .env.example .env

# 3. Launch 17 runtime containers and 2 one-shot init jobs
DOCKER_HOST=unix:///$HOME/.colima/default/docker.sock docker-compose up -d --build

# 4. Verify stack health
curl -sS http://localhost:8000/api/v1/health/live
curl -sS http://localhost:8001/health/live

# 5. Access Console UI
open http://localhost:3000
```

---

## Kubernetes Quick Start (Helm on Kind)

```bash
# 1. Create local kind cluster
kind create cluster --name incidentgraph-test

# 2. Load docker images
kind load docker-image incidentgraph-control-plane:latest incidentgraph-console:latest --name incidentgraph-test

# 3. Create required Kubernetes secret
kubectl create namespace incidentgraph
kubectl -n incidentgraph create secret generic incidentgraph-secrets \
  --from-literal=postgres-password="testpassword" \
  --from-literal=database-url="postgresql+asyncpg://incidentgraph:testpassword@incidentgraph-postgres:5432/incidentgraph_db" \
  --from-literal=secret-key="test-secret-key-at-least-32-chars-long" \
  --from-literal=webhook-signing-secret="testsecret1234567890" \
  --from-literal=bootstrap-admin-password="adminpassword123456" \
  --from-literal=grafana-admin-password="testsecret1234567890"

# 4. Install Helm chart
helm install incidentgraph deployments/helm/incidentgraph --namespace incidentgraph
```

---

## Terraform Infrastructure Architecture

Located in [`deployments/terraform/`](./deployments/terraform):
- `vpc.tf`: Multi-AZ VPC with public/private subnets and NAT Gateways.
- `ecs.tf`: ECS Fargate tasks for Control Plane, Celery Worker, Console, and OpenTelemetry.
- `rds.tf`: Multi-AZ PostgreSQL 16 instance with `pgvector` support.
- `redis.tf`: AWS ElastiCache Redis cluster for task broker & state cache.
- `alb.tf`: Application Load Balancer with HTTPS listeners.
- `secrets.tf`: AWS Secrets Manager integration.

Validate locally:
```bash
cd deployments/terraform
terraform init -backend=false
terraform validate
terraform plan -var-file=testing.tfvars
```

## Console & UI Showcase

![Incidents Dashboard](./docs/assets/incidents_dashboard.png)
*Active & Historical Incident Investigation Dashboard*

![Scenario Lab](./docs/assets/scenarios_lab.png)
*Chaos Scenario Trigger & Simulation Suite (36 Scenarios)*

![Evaluation Harness](./docs/assets/evaluations_harness.png)
*AI Reasoning Evaluation & Benchmark Engine*

---

## Documentation Index

- [Final Verification Report](FINAL_VERIFICATION_REPORT.md)
- [Resume Proof Ledger](RESUME_PROOF.md)
- [Validation Matrix](VALIDATION_MATRIX.md)
- [Evaluation Artifact Registry](eval-results/EVALUATION_ARTIFACT_REGISTRY.md)
- [Architecture & Design](ARCHITECTURE_AND_DESIGN.md)
- [God-Mode PRD](INCIDENTGRAPH_GODMODE_PRD.md)
- [10-Minute Interview Walkthrough](docs/interview/INCIDENTGRAPH_10_MINUTE_WALKTHROUGH.md)
- [2-Minute Explanation](docs/interview/INCIDENTGRAPH_2_MINUTE_EXPLANATION.md)
- [SRE/AI Interview Q&A](docs/interview/INCIDENTGRAPH_QUESTIONS_AND_ANSWERS.md)
- [Architecture Cheatsheet](docs/interview/INCIDENTGRAPH_ARCHITECTURE_CHEATSHEET.md)
