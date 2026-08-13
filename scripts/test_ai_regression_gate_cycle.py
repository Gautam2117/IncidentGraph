#!/usr/bin/env python3
"""Executable fail/recover proof for the multi-metric regression policy.

These artifacts exercise policy mechanics only and are explicitly not benchmark
evidence. A live benchmark baseline requires a configured real model provider.
"""

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from app.eval.metrics import BatchEvalSummary


def baseline_summary() -> BatchEvalSummary:
    return BatchEvalSummary(
        eval_id="policy-self-test-baseline",
        benchmark_mode="live",
        scenario_count=10,
        primary_service_accuracy=0.9,
        root_cause_accuracy=0.8,
        mean_causal_chain_precision=0.8,
        mean_causal_chain_recall=0.75,
        mean_unsupported_claim_rate=0.1,
        mean_tool_choice_accuracy=0.9,
        mean_tool_parameter_accuracy=0.85,
        remediation_accuracy=0.8,
        safe_uncertainty_rate=1.0,
        overall_pass_rate=0.8,
        mean_latency_seconds=8.0,
        p50_latency_seconds=7.0,
        p95_latency_seconds=12.0,
        total_tokens=10_000,
        total_cost_usd=1.0,
    )


def write(path: Path, summary: BatchEvalSummary) -> None:
    path.write_text(json.dumps(summary.model_dump(mode="json"), indent=2))


def run_gate(baseline: Path, candidate: Path) -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = "services/control-plane:."
    result = subprocess.run(  # nosec B603 - fixed local script and interpreter
        [sys.executable, "scripts/eval_regression_gate.py", str(baseline), str(candidate)],
        check=False,
        env=env,
    )
    return result.returncode


def main() -> None:
    output = Path("artifacts/regression-proof")
    output.mkdir(parents=True, exist_ok=True)
    baseline = baseline_summary()
    degraded = deepcopy(baseline)
    degraded.eval_id = "policy-self-test-degraded"
    degraded.root_cause_accuracy = 0.5
    degraded.mean_unsupported_claim_rate = 0.35
    degraded.mean_tool_parameter_accuracy = 0.55
    degraded.safe_uncertainty_rate = 0.6
    recovered = deepcopy(baseline)
    recovered.eval_id = "policy-self-test-recovered"

    baseline_path = output / "baseline.json"
    degraded_path = output / "degraded.json"
    recovered_path = output / "recovered.json"
    write(baseline_path, baseline)
    write(degraded_path, degraded)
    write(recovered_path, recovered)

    degraded_exit = run_gate(baseline_path, degraded_path)
    recovered_exit = run_gate(baseline_path, recovered_path)
    if degraded_exit == 0 or recovered_exit != 0:
        raise SystemExit(
            f"Regression proof failed: degraded_exit={degraded_exit}, recovered_exit={recovered_exit}"
        )
    print(f"Regression proof passed: degraded_exit={degraded_exit}, recovered_exit={recovered_exit}")
    print("Artifacts are policy self-test fixtures, not live AI benchmark evidence.")


if __name__ == "__main__":
    main()
