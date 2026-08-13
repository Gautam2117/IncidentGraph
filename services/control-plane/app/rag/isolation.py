from typing import Any

FORBIDDEN_GROUND_TRUTH_KEYS = {
    "ground_truth",
    "primary_service",
    "root_cause_category",
    "causal_chain",
    "remediation_action_type",
    "remediation_params",
}


def contains_ground_truth(metadata: dict[str, Any] | None) -> bool:
    """Returns True if dictionary contains forbidden scenario ground-truth attributes."""
    if not metadata:
        return False
    for key in FORBIDDEN_GROUND_TRUTH_KEYS:
        if key in metadata:
            return True
    return False


def sanitize_rag_chunk_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Sanitizes metadata dictionary by stripping any ground-truth fields."""
    return {k: v for k, v in metadata.items() if k not in FORBIDDEN_GROUND_TRUTH_KEYS}
