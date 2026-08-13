from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCallRequest(BaseModel):
    id: str
    tool_name: str
    arguments: dict[str, Any]


class LLMResponse(BaseModel):
    content: str
    structured_data: dict[str, Any] | None = None
    tool_calls: list[ToolCallRequest] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_usd: float = 0.0
    model_name: str = "fake-model"
    provider_name: str = "fake"


class ModelProvider:
    provider_name: str = "base"
    default_model: str = "base-model"

    async def generate(
        self, prompt: str, system_instruction: str | None = None, model: str | None = None
    ) -> LLMResponse:
        raise NotImplementedError

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> tuple[T, LLMResponse]:
        raise NotImplementedError

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        raise NotImplementedError
