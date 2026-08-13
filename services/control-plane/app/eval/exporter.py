import json
import os

from app.eval.metrics import BatchEvalSummary

EVAL_RESULTS_DIR = "eval-results"


def export_eval_result_json(summary: BatchEvalSummary) -> str:
    """Exports evaluation summary as an immutable JSON file in eval-results/ directory."""
    os.makedirs(EVAL_RESULTS_DIR, exist_ok=True)
    filename = f"eval_{summary.eval_id}.json"
    filepath = os.path.join(EVAL_RESULTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary.model_dump(), f, indent=2)

    return filepath
