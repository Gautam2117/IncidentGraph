# IncidentGraph — Autonomous Incident Investigation, AI Evaluation & Controlled Remediation Platform

IncidentGraph is a production-grade, multi-agent SRE platform built to autonomously investigate distributed system incidents, synthesize evidence-backed Root Cause Analyses (RCAs), enforce durable human-in-the-loop remediation safety, and continuously benchmark AI reasoning quality against versioned ground-truth scenarios.

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
6. **Production Infrastructure & Deployment**: Containerized with Docker Compose (17 containers), packaged as a Helm chart for Kubernetes (17 healthy workloads), and defined via AWS ECS/Fargate Terraform IaC.

---

## Verified System Benchmarks & Provenance

All metrics below reflect actual execution results recorded in local proof artifacts.

| Metric | Measured Value | Provenance Source | Status |
|---|---|---|---|
| **RAG Recall@5** | 91.2% (1.00 hybrid RRF) | [`eval-results/rag_benchmark.json`](./eval-results/rag_benchmark.json) | `VERIFIED` |
| **Backend Test Suite** | 81 tests passing (100% pass) | `pytest services/control-plane/tests` | `VERIFIED` |
| **Python Code Coverage** | 80% measured coverage | `pytest --cov=app` | `VERIFIED` |
| **Security Analysis** | 7,777 LOC scanned, 0 High/Medium | `bandit -r services/control-plane/app` | `VERIFIED` |
| **Dependency Audits** | 0 vulnerabilities | `pip-audit`, `npm audit` | `VERIFIED` |
| **k6 Load Performance** | 5,101 reqs, 168.13 req/s, p95=84.41ms | `k6 run performance/k6-smoke.js` | `VERIFIED` |
| **Playwright E2E Flow** | 2 spec suites passed across 19 pages | `npx playwright test` | `VERIFIED` |
| **Docker Compose Stack** | 17 containers UP & healthy | [`artifacts/docker_e2e_proof_results.json`](./artifacts/docker_e2e_proof_results.json) | `VERIFIED` |
| **Kubernetes / Helm** | 17/17 pods 1/1 `Running` on kind cluster | [`artifacts/k8s_helm_smoke_proof.json`](./artifacts/k8s_helm_smoke_proof.json) | `VERIFIED` |
| **Terraform IaC Plan** | 47 resources to add (static plan) | [`artifacts/terraform_plan_proof.json`](./artifacts/terraform_plan_proof.json) | `VERIFIED` |

---

## Explicit External Blockers

| Feature | External Status | Reason |
|---|---|---|
| **Live AI Reasoning Benchmark** | `EXTERNALLY_BLOCKED` | Configured `OPENAI_API_KEY` is a dummy placeholder (`mock-key-or-set-your-key`). Fake model providers are prohibited from generating live benchmark claims. |
| **AWS Cloud Live Apply** | `EXTERNALLY_BLOCKED` | `terraform plan` is static-verified (47 resources). Live cloud deployment requires AWS credentials. |

---

## Quick Start (Local Docker Compose)

```bash
# 1. Clone repository
git clone https://github.com/incidentgraph/incidentgraph.git
cd IncidentGraph

# 2. Copy environment blueprint
cp .env.example .env

# 3. Launch full 17-container stack
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
