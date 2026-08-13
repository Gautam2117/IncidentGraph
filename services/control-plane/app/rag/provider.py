import abc
import asyncio
from typing import Any, cast

import httpx

from app.core.config import settings
from app.rag.embedder import generate_embedding as deterministic_test_embedding


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_dimension(self) -> int:
        raise NotImplementedError


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic adapter allowed only in tests and explicitly offline runs."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    async def embed_text(self, text: str) -> list[float]:
        return [float(value) for value in deterministic_test_embedding(text, dim=self.dim)]

    def get_dimension(self) -> int:
        return self.dim


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model_name: str, dim: int = 384) -> None:
        if not api_key or api_key.startswith("mock-"):
            raise ValueError("A real OpenAI API key is required for live embeddings")
        self.api_key = api_key
        self.model_name = model_name
        self.dim = dim

    async def embed_text(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model_name, "input": text, "dimensions": self.dim},
            )
            response.raise_for_status()
            body = cast(dict[str, Any], response.json())
        vector = body.get("data", [{}])[0].get("embedding")
        if not isinstance(vector, list) or len(vector) != self.dim:
            raise RuntimeError("Embedding provider returned an unexpected vector dimension")
        return [float(value) for value in vector]

    def get_dimension(self) -> int:
        return self.dim


class FastEmbedProvider(EmbeddingProvider):
    """CPU-efficient local ONNX embedding provider for self-contained deployments."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=model_name)
        self.dimension = 384

    async def embed_text(self, text: str) -> list[float]:
        vectors = await asyncio.to_thread(lambda: list(self.model.embed([text])))
        if not vectors:
            raise RuntimeError("Local embedding provider returned no vector")
        values = [float(value) for value in vectors[0].tolist()]
        if len(values) != self.dimension:
            raise RuntimeError("Local embedding provider returned an unexpected dimension")
        return values

    def get_dimension(self) -> int:
        return self.dimension


def create_embedding_provider() -> EmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER.lower()
    key = settings.OPENAI_API_KEY
    if provider == "openai" and key and not key.startswith("mock-"):
        return OpenAIEmbeddingProvider(key, settings.EMBEDDING_MODEL)
    if provider in {"fastembed", "local"}:
        return FastEmbedProvider(settings.EMBEDDING_MODEL)
    if settings.ENVIRONMENT.lower() != "production":
        return FakeEmbeddingProvider()
    raise RuntimeError(
        "Live embedding provider is not configured; deterministic embeddings are disabled in production"
    )
