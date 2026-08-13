import uuid
from typing import Any, TypeVar

from pydantic import BaseModel

from app.models.accounting import record_usage
from app.models.model_base import LLMResponse, ModelProvider, TokenUsage, ToolCallRequest

T = TypeVar("T", bound=BaseModel)


class FakeModelProvider(ModelProvider):  # type: ignore[misc]
    provider_name = "fake"
    default_model = "fake-model"

    def __init__(self, predefined_response: str | None = None) -> None:
        self.predefined_response = predefined_response

    async def generate(
        self, prompt: str, system_instruction: str | None = None, model: str | None = None
    ) -> LLMResponse:
        model_name = model or self.default_model
        content = self.predefined_response or f"Fake LLM response for prompt: '{prompt[:50]}...'"
        prompt_tokens = len(prompt.split()) + 10
        completion_tokens = len(content.split()) + 5
        cost = record_usage(model_name, prompt_tokens, completion_tokens)

        return LLMResponse(
            content=content,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            cost_usd=cost,
            model_name=model_name,
            provider_name=self.provider_name,
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> tuple[T, LLMResponse]:
        model_name = model or self.default_model

        # Construct dummy model instance from schema annotations
        dummy_kwargs: dict[str, Any] = {}
        for name, field in response_schema.model_fields.items():
            if field.annotation is str or field.annotation == str | None:
                dummy_kwargs[name] = f"sample_{name}"
            elif field.annotation is int or field.annotation == int | None:
                dummy_kwargs[name] = 100
            elif field.annotation is float or field.annotation == float | None:
                dummy_kwargs[name] = 0.95
            elif field.annotation is bool or field.annotation == bool | None:
                dummy_kwargs[name] = True
            elif str(field.annotation).startswith("list"):
                dummy_kwargs[name] = ["item_1", "item_2"]
            else:
                dummy_kwargs[name] = f"mock_{name}"

        instance = response_schema.model_validate(dummy_kwargs)
        json_str = instance.model_dump_json()

        prompt_tokens = len(prompt.split()) + 15
        completion_tokens = len(json_str.split()) + 10
        cost = record_usage(model_name, prompt_tokens, completion_tokens)

        resp = LLMResponse(
            content=json_str,
            structured_data=instance.model_dump(),
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            cost_usd=cost,
            model_name=model_name,
            provider_name=self.provider_name,
        )
        return instance, resp

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        model_name = model or self.default_model
        tool_name = tools[0]["name"] if tools else "metrics.query"
        tool_call = ToolCallRequest(
            id=f"call_{uuid.uuid4().hex[:8]}",
            tool_name=tool_name,
            arguments={"service": "inventory", "metric_type": "http_requests_total"},
        )

        prompt_tokens = len(prompt.split()) + 20
        completion_tokens = 25
        cost = record_usage(model_name, prompt_tokens, completion_tokens)

        return LLMResponse(
            content=f"Decided to call tool {tool_name}",
            tool_calls=[tool_call],
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            cost_usd=cost,
            model_name=model_name,
            provider_name=self.provider_name,
        )
