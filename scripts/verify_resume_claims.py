#!/usr/bin/env python3
"""Fail closed when featured resume claims drift from committed proof artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def compose_service_count() -> int:
    lines = (ROOT / "docker-compose.yml").read_text(encoding="utf-8").splitlines()
    in_services = False
    count = 0
    for line in lines:
        if line == "services:":
            in_services = True
            continue
        if in_services and line and not line.startswith((" ", "#")):
            break
        if in_services and re.match(r"^  [a-zA-Z0-9_-]+:\s*$", line):
            count += 1
    return count


def main() -> None:
    rag = load_json("eval-results/rag_benchmark.json")["hybrid_rrf"]
    require(rag["query_count"] == 5, "RAG benchmark must contain N=5 queries")
    require(rag["recall_at_5"] == 1.0, "RAG Recall@5 must equal 1.0")

    coverage = load_json("eval-results/coverage.json")["totals"]
    require(coverage["percent_covered"] >= 80.0, "Measured coverage dropped below 80%")

    bandit = load_json("eval-results/bandit.json")["metrics"]["_totals"]
    require(bandit["SEVERITY.HIGH"] == 0, "Bandit found a high-severity issue")
    require(bandit["SEVERITY.MEDIUM"] == 0, "Bandit found a medium-severity issue")
    require(bandit["loc"] == 8338, "README security LOC no longer matches Bandit proof")

    k6 = load_json("eval-results/k6-summary.json")
    metrics = k6["metrics"]
    require(metrics["http_reqs"]["count"] == 3413, "k6 request count drifted")
    require(round(metrics["http_reqs"]["rate"], 2) == 168.63, "k6 request rate drifted")
    require(round(metrics["http_req_duration"]["p(95)"], 2) == 87.44, "k6 p95 drifted")
    require(metrics["http_req_failed"]["value"] == 0, "k6 recorded failed requests")
    require(k6["setup_data"]["token"] == "[REDACTED_FROM_PROOF_ARTIFACT]", "k6 proof must not retain an auth token")

    kubernetes = load_json("artifacts/k8s_helm_smoke_proof.json")
    require(kubernetes["workloads"]["total_pods"] == 17, "Kubernetes workload count drifted")
    require(kubernetes["workloads"]["healthy_pods"] == 17, "Kubernetes proof is not fully healthy")
    require(kubernetes["smoke_flow"]["scenarios_available"] == 36, "Scenario proof count drifted")

    terraform = load_json("artifacts/terraform_plan_proof.json")
    require(terraform["plan"]["to_add"] == 47, "Terraform resource count drifted")
    require(terraform["plan"]["status"] == "VERIFIED_STATIC_PLAN", "Terraform plan is not verified")

    docker = load_json("artifacts/docker_e2e_proof_results.json")
    require(docker["status"] == "VERIFIED", "Docker proof is not verified")
    require(compose_service_count() == 19, "Docker Compose must define 17 runtime services plus 2 init jobs")
    compose_source = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    require("  migrate:" in compose_source, "Compose migration init job is missing")
    require("  bootstrap-admin:" in compose_source, "Compose admin bootstrap init job is missing")

    demo_services = ("gateway", "auth", "orders", "payments", "inventory", "notifications")
    for service in demo_services:
        source = (ROOT / "services" / "demo" / service / "main.py").read_text(encoding="utf-8")
        require("setup_telemetry(SERVICE_NAME)" in source, f"{service} is missing tracing setup")
        require("setup_metrics_middleware(app, SERVICE_NAME)" in source, f"{service} is missing metrics setup")

    canonical_docs = (
        "README.md",
        "RESUME_PROOF.md",
        "eval-results/EVALUATION_ARTIFACT_REGISTRY.md",
    )
    for relative_path in canonical_docs:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        require("3,413" in text and "87.44" in text, f"{relative_path} has stale k6 claims")
        require("incidentgraph.vercel.app" in text, f"{relative_path} omits the live showcase")

    stale_claims = ("5,101", "84.41", "7,777 LOC")
    featured_docs = list(canonical_docs) + [
        "FINAL_VERIFICATION_REPORT.md",
        "RELEASE_READINESS_REPORT.md",
        "GITHUB_RELEASE_REPORT.md",
        "VALIDATION_MATRIX.md",
        "docs/interview/INCIDENTGRAPH_10_MINUTE_WALKTHROUGH.md",
    ]
    for relative_path in featured_docs:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for stale_claim in stale_claims:
            require(stale_claim not in text, f"{relative_path} retains stale claim: {stale_claim}")

    print("Resume evidence gate passed: featured claims match committed proof artifacts.")


if __name__ == "__main__":
    main()
