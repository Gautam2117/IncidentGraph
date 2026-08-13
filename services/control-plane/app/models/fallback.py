import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from app.models.model_base import LLMResponse, ModelProvider

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class FallbackProvider(ModelProvider):  # type: ignore[misc]
    provider_name = "fallback_chain"

    def __init__(self, providers: list[ModelProvider]) -> None:
        if not providers:
            raise ValueError("FallbackProvider requires at least one provider in chain")
        self.providers = providers
        self.default_model = providers[0].default_model

    async def generate(
        self, prompt: str, system_instruction: str | None = None, model: str | None = None
    ) -> LLMResponse:
        errors = []
        for provider in self.providers:
            try:
                return await provider.generate(prompt, system_instruction, model)
            except Exception as e:
                logger.warning(
                    f"Provider '{provider.provider_name}' failed: {e}. Trying next provider in fallback chain..."
                )
                errors.append(f"{provider.provider_name}: {e}")

        raise RuntimeError(f"All providers in fallback chain failed: {'; '.join(errors)}")

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> tuple[T, LLMResponse]:
        errors = []
        for provider in self.providers:
            try:
                res_obj, res_llm = await provider.generate_structured(
                    prompt, response_schema, system_instruction, model
                )
                return res_obj, res_llm
            except Exception as e:
                logger.warning(
                    f"Provider '{provider.provider_name}' failed: {e}. Trying next provider..."
                )
                errors.append(f"{provider.provider_name}: {e}")

        raise RuntimeError(f"All providers in fallback chain failed: {'; '.join(errors)}")

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        errors = []
        for provider in self.providers:
            try:
                return await provider.generate_with_tools(prompt, tools, system_instruction, model)
            except Exception as e:
                logger.warning(
                    f"Provider '{provider.provider_name}' failed: {e}. Trying next provider..."
                )
                errors.append(f"{provider.provider_name}: {e}")

        raise RuntimeError(f"All providers in fallback chain failed: {'; '.join(errors)}")
