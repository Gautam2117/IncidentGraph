#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from app.eval.metrics import BatchEvalSummary
from app.eval.regression import evaluate_regression


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two IncidentGraph evaluation artifacts")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    baseline = BatchEvalSummary.model_validate_json(args.baseline.read_text())
    candidate = BatchEvalSummary.model_validate_json(args.candidate.read_text())
    decision = evaluate_regression(baseline, candidate)
    print(json.dumps(decision.model_dump(), indent=2))
    raise SystemExit(0 if decision.passed else 1)


if __name__ == "__main__":
    main()
