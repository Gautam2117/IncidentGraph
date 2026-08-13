# IncidentGraph — Architecture & Tech Stack Cheatsheet

Quick-reference technical cheatsheet for system design and code architecture reviews.

---

## Tech Stack at a Glance

| Component | Technology | Version | Key Responsibilities |
|---|---|---|---|
| **Frontend UI** | Next.js / React / TypeScript | Next.js 16.3, React 19 | Engineering console, incident dashboard, interactive graph review |
| **Control Plane** | Python / FastAPI / Pydantic | Python 3.12, FastAPI 0.115+, Pydantic v2 | Async REST API, RBAC authorization, audit logging |
| **Agent Graph** | LangGraph / AsyncSQLAlchemy | LangGraph 0.2+ | Multi-role SRE graph, state checkpointing, human-in-the-loop review |
| **RAG & Search** | PostgreSQL / pgvector / FTS | PostgreSQL 16, pgvector 0.8 | Semantic vector search + Full-Text Search + Reciprocal Rank Fusion (RRF) |
| **Async Worker** | Celery / Redis | Celery 5.4, Redis 7.4 | Background job execution, task broker, cache store |
| **Observability** | OpenTelemetry / Prometheus / Loki / Tempo / Grafana | OTEL 0.135, Prom v3.5, Loki 3.5, Tempo 2.8, Grafana 12.1 | Distributed trace collection, log ingestion, metric scraping, visualization |
| **Containers & K8s** | Docker Compose / Helm / Kind | Docker 27+, Helm v3, Kind v1.36 | Local 17-container stack, Kubernetes Helm package deployment |
| **Cloud IaC** | Terraform / AWS ECS Fargate | Terraform v1.15, AWS Provider v5.100 | Multi-AZ VPC, ECS Fargate, RDS PostgreSQL, ElastiCache Redis, ALB |

---

## Agent State Schema (`InvestigationState`)

```python
class InvestigationState(BaseModel):
    incident_id: str
    target_service: str
    scenario_id: str | None = None
    step_count: int = 0
    max_steps: int = 10
    status: str = "RUNNING"
    
    # Hypotheses & Verifications
    hypotheses: list[Hypothesis] = []
    skeptic_findings: list[SkepticFinding] = []
    
    # Grounded Evidence
    telemetry_evidence: list[EvidenceItem] = []
    knowledge_docs: list[KnowledgeDocItem] = []
    
    # Outputs & Control
    rca_report: RCAReport | None = None
    remediation_plan: RemediationPlan | None = None
    requires_human_approval: bool = True
    human_decision: str | None = None
```

---

## Key File Locations

- **Agent Graph Engine**: [`services/control-plane/app/agent/graph.py`](../../services/control-plane/app/agent/graph.py)
- **Agent Nodes & Skeptic Logic**: [`services/control-plane/app/agent/nodes.py`](../../services/control-plane/app/agent/nodes.py)
- **RAG Store & RRF Search**: [`services/control-plane/app/rag/store.py`](../../services/control-plane/app/rag/store.py)
- **Remediation Execution**: [`services/control-plane/app/remediation/executor.py`](../../services/control-plane/app/remediation/executor.py)
- **Scenario Registry (36 Scenarios)**: [`services/control-plane/app/scenarios/registry.py`](../../services/control-plane/app/scenarios/registry.py)
- **Docker E2E Proof Script**: [`scripts/execute_docker_e2e_proof.py`](../../scripts/execute_docker_e2e_proof.py)
- **Helm Chart**: [`deployments/helm/incidentgraph/`](../../deployments/helm/incidentgraph)
- **Terraform IaC**: [`deployments/terraform/`](../../deployments/terraform)

---

## RRF Fusion Formula

$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

where $k = 60$, combining `pgvector` rank $r_{\text{vector}}(d)$ and Full-Text Search rank $r_{\text{fts}}(d)$.
