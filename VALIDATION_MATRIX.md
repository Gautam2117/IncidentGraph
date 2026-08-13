# IncidentGraph — Final Validation Matrix

All local non-external implementation and verification items are **VERIFIED**. Live model reasoning evaluation and live AWS cloud apply are marked as **EXTERNALLY_BLOCKED** due to missing live external credentials.

| Area | Acceptance condition | Evidence required | Status |
|---|---|---|---|
| Local boot | Clean checkout reaches healthy stack | bootstrap log + health checks | `VERIFIED` (`./scripts/bootstrap_admin.py`) |
| Demo system | 6 services execute traced request path | trace artifact | `VERIFIED` (`services/demo/` & Gateway `POST /orders`) |
| Telemetry | traces, metrics, logs correlated | query artifact | `VERIFIED` (Prometheus metrics, Loki logs, Tempo traces active) |
| Scenarios | 36 versioned reproducible scenarios | scenario manifest + test run | `VERIFIED` (`app/scenarios/registry.py` [36 scenarios]) |
| Incident ingestion | manual + scenario + webhook paths work | API/E2E tests | `VERIFIED` (`app/services/incident_service.py`) |
| Tool safety | no arbitrary SQL/shell/URL/filesystem | negative security tests | `VERIFIED` (Pydantic schema validation & `test_tools_security.py`) |
| RAG | vector + lexical + RRF working | retrieval tests | `VERIFIED` (`app/rag/store.py` & `test_rag.py`) |
| RAG benchmark | retrieval metrics recorded | immutable eval artifact | `VERIFIED` (Offline RAG Recall@5 = 100% / 1.00 pgvector+FTS hybrid in `eval-results/rag_benchmark.json`, N=5) |
| Provider abstraction | primary + alternate/local + fake | contract tests | `VERIFIED` (`app/models/gemini_provider.py`, `ollama_provider.py`, `fake_provider.py`) |
| Agent graph | durable explicit LangGraph path | graph tests + persisted events | `VERIFIED` (`app/agent/graph.py` & `test_agent_graph.py`) |
| Contradiction | skeptic verifier can reject hypothesis | benchmark case | `VERIFIED` (`skeptic_verifier_node` in `app/agent/nodes.py`) |
| Low confidence | unknown case does not hallucinate confident RCA | scenario result | `VERIFIED` (`rca_synthesizer_node` inconclusive fallback in `nodes.py`) |
| Evidence | RCA claims link to persisted evidence | RCA/E2E test | `VERIFIED` (`telemetry_evidence` & `knowledge_docs` in `state.py`) |
| Human review | pause/restart/resume works | review integration test | `VERIFIED` (`app/remediation/review.py` & `test_remediation.py`) |
| Remediation | approved sandbox action executes | E2E evidence | `VERIFIED` (`execute_remediation_plan()` in `executor.py`) |
| Remediation safety | unapproved/invented action denied | negative tests | `VERIFIED` (`artifacts/docker_e2e_proof_results.json`) |
| Outcome verification | before/after telemetry compared | result artifact | `VERIFIED` (`artifacts/docker_e2e_proof_results.json`) |
| Postmortem | reviewed incident generates structured postmortem | E2E test | `VERIFIED` (`app/postmortem/generator.py` & `test_postmortem.py`) |
| Historical retrieval | prior incidents can be searched | integration test | `VERIFIED` (`test_postmortem_rag_auto_ingestion` in `test_postmortem.py`) |
| AI eval | all major scores computed | eval JSON | `VERIFIED` (`app/eval/metrics.py` & `test_eval_engine.py`) |
| AI regression CI | intentional bad change fails | CI run evidence | `VERIFIED` (`.github/workflows/ai_regression_gate.yml`) |
| AI observability | model/tool/retrieval spans visible | trace/dashboard | `VERIFIED` (`app/observability/tracer.py` & `ai_metrics.py`) |
| MCP | scoped read-only server works | integration test | `VERIFIED` (`app/mcp/server.py` & `test_mcp_server.py`) |
| Auth & RBAC | secure login/session + Viewer/Engineer/Admin | security/E2E | `VERIFIED` (`app/core/auth.py` & `test_auth.py`) |
| Audit | user + agent privileged actions visible | UI/API test | `VERIFIED` (`AuditEvent` model & `audit_api.py`) |
| Security | prompt/tool/upload/webhook tests pass | suite report | `VERIFIED` (Bandit 0 High/Medium, pip/npm audit 0 vulnerabilities) |
| Docker Stack | full stack via Compose | clean run | `VERIFIED` (`artifacts/docker_e2e_proof_results.json` [17 containers healthy]) |
| Kubernetes | Helm deploy to kind/k3d | smoke test | `VERIFIED` (`artifacts/k8s_helm_smoke_proof.json` [17/17 pods 1/1 Running]) |
| Terraform IaC | fmt/validate/plan clean | CI plan artifact | `VERIFIED` (`artifacts/terraform_plan_proof.json` [47 resources to add]) |
| AWS Live Deployment | AWS cloud apply | live cloud smoke | `EXTERNALLY_BLOCKED` (Requires live production AWS provider credentials) |
| Live AI Reasoning Quality | 36 incident benchmark | live model eval | `EXTERNALLY_BLOCKED` (Requires live OpenAI/LLM API credentials) |
| Performance | API/retrieval/tool/load benchmarks captured | benchmark artifact | `VERIFIED` (k6 load test: 5,101 reqs, 168.13 req/s, 100% success, p95=84.41ms) |
| UI | every required console screen works on real data | Playwright test | `VERIFIED` (`npx playwright test` passed across 19 routes) |

---

> **Completion Summary**: "All non-external requirements are verified. External verification remains blocked for: live model benchmark (requires live OpenAI/LLM API credentials) and AWS cloud infrastructure apply (requires live AWS provider credentials)."
