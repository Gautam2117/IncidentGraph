from typing import Any

try:
    from prometheus_client import Counter, Histogram

    AI_TOKENS_COUNTER = Counter(
        "incidentgraph_ai_tokens_total",
        "Total tokens consumed by LLM providers",
        ["provider", "model", "token_type"],
    )

    AI_COST_COUNTER = Counter(
        "incidentgraph_ai_cost_usd_total",
        "Total estimated cost in USD for LLM API calls",
        ["provider", "model"],
    )

    TOOL_EXECUTION_HISTOGRAM = Histogram(
        "incidentgraph_tool_execution_seconds",
        "Duration of safe tool executions in seconds",
        ["tool_name"],
    )

    TOOL_ERROR_COUNTER = Counter(
        "incidentgraph_tool_errors_total",
        "Total failed tool executions",
        ["tool_name"],
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

_ai_metrics_stats = {
    "total_tokens": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_cost_usd": 0.0,
    "tool_calls_count": 0,
    "tool_errors_count": 0,
}


def record_token_usage(
    provider: str, model: str, prompt_tokens: int, completion_tokens: int, cost_usd: float
) -> None:
    if PROMETHEUS_AVAILABLE:
        AI_TOKENS_COUNTER.labels(provider=provider, model=model, token_type="prompt").inc(
            prompt_tokens
        )
        AI_TOKENS_COUNTER.labels(provider=provider, model=model, token_type="completion").inc(
            completion_tokens
        )
        AI_COST_COUNTER.labels(provider=provider, model=model).inc(cost_usd)

    _ai_metrics_stats["prompt_tokens"] += prompt_tokens
    _ai_metrics_stats["completion_tokens"] += completion_tokens
    _ai_metrics_stats["total_tokens"] += prompt_tokens + completion_tokens
    _ai_metrics_stats["total_cost_usd"] += cost_usd


def record_tool_execution(tool_name: str, duration_seconds: float, success: bool = True) -> None:
    if PROMETHEUS_AVAILABLE:
        TOOL_EXECUTION_HISTOGRAM.labels(tool_name=tool_name).observe(duration_seconds)
    _ai_metrics_stats["tool_calls_count"] += 1
    if not success:
        if PROMETHEUS_AVAILABLE:
            TOOL_ERROR_COUNTER.labels(tool_name=tool_name).inc()
        _ai_metrics_stats["tool_errors_count"] += 1


def get_ai_metrics_summary() -> dict[str, Any]:
    return dict(_ai_metrics_stats)
