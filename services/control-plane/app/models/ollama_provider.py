import json
import uuid
from typing import Any, TypeVar, cast

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.models.accounting import record_usage
from app.models.model_base import LLMResponse, ModelProvider, TokenUsage, ToolCallRequest

T = TypeVar("T", bound=BaseModel)


class OllamaProvider(ModelProvider):  # type: ignore[misc]
    provider_name = "ollama"
    default_model = "llama3.2"

    def __init__(self, host: str | None = None) -> None:
        self.host = (host or settings.OLLAMA_URL).rstrip("/")
        self.default_model = settings.OLLAMA_MODEL

    async def _chat(
        self,
        prompt: str,
        system_instruction: str | None,
        model: str,
        response_format: str | dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        body: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if response_format:
            body["format"] = response_format
        if tools:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                    },
                }
                for tool in tools
            ]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.host}/api/chat", json=body)
            response.raise_for_status()
            data = cast(dict[str, Any], response.json())
        message = data.get("message", {})
        prompt_tokens = int(data.get("prompt_eval_count", 0))
        completion_tokens = int(data.get("eval_count", 0))
        calls = []
        for call in message.get("tool_calls", []):
            function = call.get("function", {})
            calls.append(
                ToolCallRequest(
                    id=f"call_{uuid.uuid4().hex[:12]}",
                    tool_name=str(function.get("name", "")),
                    arguments=dict(function.get("arguments", {})),
                )
            )
        return LLMResponse(
            content=str(message.get("content", "")),
            tool_calls=calls,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            cost_usd=record_usage(model, prompt_tokens, completion_tokens),
            model_name=model,
            provider_name=self.provider_name,
        )

    async def generate(
        self, prompt: str, system_instruction: str | None = None, model: str | None = None
    ) -> LLMResponse:
        return await self._chat(prompt, system_instruction, model or self.default_model)

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> tuple[T, LLMResponse]:
        response = await self._chat(
            prompt,
            system_instruction,
            model or self.default_model,
            response_format=response_schema.model_json_schema(),
        )
        parsed = response_schema.model_validate(json.loads(response.content))
        response.structured_data = parsed.model_dump(mode="json")
        return parsed, response

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        return await self._chat(
            prompt,
            system_instruction,
            model or self.default_model,
            tools=tools,
        )
