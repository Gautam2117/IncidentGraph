#!/usr/bin/env python3
import argparse
import asyncio
import sys

from app.db.session import AsyncSessionLocal
from app.eval.eval_runner import run_batch_eval


async def main() -> None:
    parser = argparse.ArgumentParser(description="IncidentGraph AI Evaluation CLI Runner")
    parser.add_argument(
        "--scenarios", type=str, default="all", help="Comma-separated scenario IDs or 'all'"
    )
    parser.add_argument(
        "--no-export", action="store_true", help="Disable JSON export to eval-results/"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use deterministic test adapters; results are not a live benchmark",
    )
    parser.add_argument(
        "--pass-rate-threshold",
        type=float,
        default=0.0,
        help="Minimum pass rate (0.0 to 1.0) required to exit with success",
    )
    args = parser.parse_args()

    filter_ids = None if args.scenarios == "all" else args.scenarios.split(",")

    print("==========================================================")
    print("IncidentGraph AI Evaluation Batch Runner")
    print("==========================================================")

    async with AsyncSessionLocal() as session:
        summary = await run_batch_eval(
            session=session,
            scenarios_filter=filter_ids,
            export_json=not args.no_export,
            benchmark_mode="offline" if args.offline else "live",
        )

    print(f"\n[Eval ID: {summary.eval_id}]")
    print(f"Benchmark Mode:            {summary.benchmark_mode}")
    print(f"Scenarios Evaluated:       {summary.scenario_count}")
    print(f"Primary Service Accuracy:  {summary.primary_service_accuracy * 100:.1f}%")
    print(f"Root Cause Accuracy:       {summary.root_cause_accuracy * 100:.1f}%")
    print(f"Causal Chain Recall:       {summary.mean_causal_chain_recall * 100:.1f}%")
    print(f"Remediation Accuracy:      {summary.remediation_accuracy * 100:.1f}%")
    print(f"Overall Pass Rate:         {summary.overall_pass_rate * 100:.1f}%")
    print(f"Mean Latency:              {summary.mean_latency_seconds:.2f}s")
    print(f"Total Cost:                ${summary.total_cost_usd:.4f}")
    print("==========================================================\n")

    if args.pass_rate_threshold > 0.0:
        if summary.overall_pass_rate < args.pass_rate_threshold:
            print(
                f"❌ Eval failed: Overall Pass Rate {summary.overall_pass_rate * 100:.1f}% is below threshold {args.pass_rate_threshold * 100:.1f}%"
            )
            sys.exit(1)
        else:
            print(
                f"✅ Eval passed threshold: Overall Pass Rate {summary.overall_pass_rate * 100:.1f}% >= {args.pass_rate_threshold * 100:.1f}%"
            )
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
