# IncidentGraph — Evaluation & Benchmark Artifact Registry

This registry tracks the hygiene status of all historical and current evaluation, benchmark, and verification artifacts.

> [!IMPORTANT]
> **Ground-Truth Leakage & Fake Model Disclaimer**:
> Historical evaluation files produced during early offline testing using `FakeListChatModel` or early prompt leakage patterns are marked as **`REVOKED_CONTAMINATED`** or **`SUPERSEDED`**. They must never be presented as proof of live-model reasoning quality. Current evidence strictly relies on deterministic execution proofs (`CURRENT`).

---

## 1. Current Verified Evidence Artifacts (`CURRENT`)

| Artifact | Purpose / Measured Metric | Status | Timestamp |
|---|---|---|---|
| [`artifacts/docker_e2e_proof_results.json`](../artifacts/docker_e2e_proof_results.json) | Real 17-container Docker Compose stack launch, fault injection, before/after telemetry, human approval, sandbox remediation & recovery verification | `CURRENT` | 2026-08-13T15:23:18Z |
| [`artifacts/k8s_helm_smoke_proof.json`](../artifacts/k8s_helm_smoke_proof.json) | Local `kind` cluster deployment, Helm chart installation, 17/17 pods 1/1 `Running`, and control-plane incident smoke flow | `CURRENT` | 2026-08-13T15:36:19Z |
| [`artifacts/terraform_plan_proof.json`](../artifacts/terraform_plan_proof.json) | Terraform `init`, `validate`, and 47-resource static `plan` output | `CURRENT` | 2026-08-13T15:37:50Z |
| [`eval-results/rag_benchmark.json`](./rag_benchmark.json) | Hybrid RAG Recall@5 evaluation (PostgreSQL pgvector + FTS RRF) yielding 91.2% clean offline recall | `CURRENT` | 2026-08-13T15:54:26Z |
| [`eval-results/k6-summary.json`](./k6-summary.json) | k6 load performance test (5,101 reqs, 168.13 req/s, 100% success, p95=84.41ms) | `CURRENT` | 2026-08-13T15:27:53Z |
| [`eval-results/bandit.json`](./bandit.json) | Bandit security scan (7,777 LOC, 0 High, 0 Medium issues) | `CURRENT` | 2026-08-13T15:23:33Z |
| [`eval-results/pip-audit.json`](./pip-audit.json) | Python dependency vulnerability audit (0 vulnerabilities) | `CURRENT` | 2026-08-13T15:23:45Z |

---

## 2. Superseded Benchmark Artifacts (`SUPERSEDED`)

| Artifact | Original Purpose | Reason for Status | Status |
|---|---|---|---|
| `eval-results/baseline_eval.json` | Early offline mock suite runs | Replaced by clean production path RAG & load test suites | `SUPERSEDED` |
| `eval-results/degraded_eval.json` | Artificial regression test data | Replaced by automated CI regression gate test scripts | `SUPERSEDED` |
| `eval-results/eval_run_*.json` | Synthetic offline mock evaluations | Produced using offline adapter/mock providers | `SUPERSEDED` |

---

## 3. Revoked / Contaminated Artifacts (`REVOKED_CONTAMINATED`)

| Artifact | Original Claimed Metric | Reason for Revocation | Status |
|---|---|---|---|
| Historical `100% Full-Eval` runs | Claimed 100% RCA accuracy across 36 incidents | Contaminated by ground-truth scenario metadata leakage in early prompt templates or simulated via `FakeListChatModel`. Revoked to prevent false claims. | `REVOKED_CONTAMINATED` |

---

## Summary of Truthful Baselines

- **Live Model Quality**: `EXTERNALLY_BLOCKED` (Requires live LLM API credentials)
- **AWS Cloud Live Apply**: `EXTERNALLY_BLOCKED` (Requires live AWS credentials)
- **All Non-External Code / Infra / Security Requirements**: `VERIFIED`
