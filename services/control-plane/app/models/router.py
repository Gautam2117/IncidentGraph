from typing import Literal

from app.models.fake_provider import FakeModelProvider
from app.models.fallback import FallbackProvider
from app.models.gemini_provider import GeminiProvider
from app.models.model_base import ModelProvider
from app.models.ollama_provider import OllamaProvider

TaskTier = Literal["triage", "investigation", "rca", "verification"]

MODEL_ROUTING_POLICY: dict[TaskTier, str] = {
    "triage": "gemini-1.5-flash",
    "investigation": "gemini-1.5-flash",
    "rca": "gemini-1.5-pro",
    "verification": "gemini-1.5-flash",
}


class ModelRouter:
    def __init__(self, provider: ModelProvider | None = None) -> None:
        self.provider = provider or FallbackProvider(
            [
                GeminiProvider(),
                OllamaProvider(),
                FakeModelProvider(),
            ]
        )

    def select_model(self, tier: TaskTier) -> str:
        return MODEL_ROUTING_POLICY.get(tier, "gemini-1.5-flash")

    def get_provider_for_tier(self, tier: TaskTier) -> tuple[ModelProvider, str]:
        target_model = self.select_model(tier)
        return self.provider, target_model
