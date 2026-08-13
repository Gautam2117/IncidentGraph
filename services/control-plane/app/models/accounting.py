from pydantic import BaseModel

MODEL_PRICING: dict[str, dict[str, float]] = {
    # price per 1M tokens (input, output)
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "ollama-llama3": {"input": 0.0, "output": 0.0},
    "fake-model": {"input": 0.0, "output": 0.0},
}


class CumulativeAccounting(BaseModel):
    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0


_global_accounting = CumulativeAccounting()


def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model_name, {"input": 0.10, "output": 0.40})
    input_cost = (prompt_tokens / 1_000_000.0) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000.0) * pricing["output"]
    return round(input_cost + output_cost, 6)


def record_usage(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    cost = calculate_cost(model_name, prompt_tokens, completion_tokens)
    _global_accounting.total_requests += 1
    _global_accounting.total_prompt_tokens += prompt_tokens
    _global_accounting.total_completion_tokens += completion_tokens
    _global_accounting.total_tokens += prompt_tokens + completion_tokens
    _global_accounting.total_cost_usd = round(_global_accounting.total_cost_usd + cost, 6)
    return cost


def get_cumulative_accounting() -> CumulativeAccounting:
    return _global_accounting
