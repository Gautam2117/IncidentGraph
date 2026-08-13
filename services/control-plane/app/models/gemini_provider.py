import uuid
from typing import Any, TypeVar, cast

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.models.accounting import record_usage
from app.models.model_base import LLMResponse, ModelProvider, TokenUsage, ToolCallRequest

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(ModelProvider):  # type: ignore[misc]
    provider_name = "gemini"
    default_model = "gemini-2.0-flash"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.default_model = settings.GEMINI_MODEL

    async def _request(
        self,
        prompt: str,
        system_instruction: str | None,
        model: str,
        generation_config: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Gemini is not configured")
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if generation_config:
            body["generationConfig"] = generation_config
        if tools:
            declarations = []
            for tool in tools:
                declarations.append(
                    {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                    }
                )
            body["tools"] = [{"functionDeclarations": declarations}]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": self.api_key},
                json=body,
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    def _to_response(self, body: dict[str, Any], model: str) -> LLMResponse:
        parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        content = "".join(str(part.get("text", "")) for part in parts)
        tool_calls = [
            ToolCallRequest(
                id=f"call_{uuid.uuid4().hex[:12]}",
                tool_name=str(part["functionCall"]["name"]),
                arguments=dict(part["functionCall"].get("args", {})),
            )
            for part in parts
            if "functionCall" in part
        ]
        usage = body.get("usageMetadata", {})
        prompt_tokens = int(usage.get("promptTokenCount", 0))
        completion_tokens = int(usage.get("candidatesTokenCount", 0))
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
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
        selected = model or self.default_model
        return self._to_response(
            await self._request(prompt, system_instruction, selected), selected
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> tuple[T, LLMResponse]:
        selected = model or self.default_model
        body = await self._request(
            prompt,
            system_instruction,
            selected,
            generation_config={
                "responseMimeType": "application/json",
                "responseJsonSchema": response_schema.model_json_schema(),
            },
        )
        response = self._to_response(body, selected)
        parsed = response_schema.model_validate_json(response.content)
        response.structured_data = parsed.model_dump(mode="json")
        return parsed, response

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        selected = model or self.default_model
        return self._to_response(
            await self._request(prompt, system_instruction, selected, tools=tools), selected
        )
