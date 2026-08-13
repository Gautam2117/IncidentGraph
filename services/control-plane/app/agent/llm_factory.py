"""
LLM Factory — centralised chat model creation for agent nodes.

Replaces the scattered `if not settings.OPENAI_API_KEY` checks spread across
nodes.py with a single factory that returns the appropriate BaseChatModel.

Provider priority
-----------------
1. OpenAI (ChatOpenAI)     — when OPENAI_API_KEY is set and not "mock-*"
2. FakeListChatModel       — only when the explicit test/offline adapter is enabled

All callers in nodes.py should use ``get_chat_model()`` rather than
instantiating ChatOpenAI directly. This makes swapping in Gemini, Anthropic,
or a local model a one-line change in this file.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel, SecretStr

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_mock_mode() -> bool:
    """Return whether the explicitly enabled offline adapter should be used."""
    if not settings.ENABLE_OFFLINE_MODEL_ADAPTER:
        return False
    return not _has_live_configuration()


def _has_live_configuration() -> bool:
    """Return whether the selected provider has usable live configuration."""
    provider = settings.PRIMARY_LLM_PROVIDER.lower()
    if provider == "ollama":
        return True
    if provider == "gemini":
        return bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("mock-"))
    key = settings.OPENAI_API_KEY
    return bool(key and not key.startswith("mock-"))


def get_chat_model(temperature: float = 0) -> BaseChatModel:
    """Return the configured chat model for agent nodes.

    In live mode returns a ChatOpenAI instance.
    In mock mode returns LangChain's FakeListChatModel with a sentinel reply
    so tests can detect that the real model was NOT called.

    Parameters
    ----------
    temperature:
        Model temperature (ignored by FakeListChatModel).
    """
    if is_mock_mode():
        from langchain_community.chat_models.fake import (
            FakeListChatModel,
        )

        logger.debug("LLM factory: no real API key — returning FakeListChatModel (mock mode)")
        return FakeListChatModel(
            responses=['{"content": "MOCK_LLM_RESPONSE — set OPENAI_API_KEY for real inference"}']
        )

    if not _has_live_configuration():
        raise RuntimeError(
            "No live model credentials are configured. Set the selected provider credentials "
            "or explicitly enable ENABLE_OFFLINE_MODEL_ADAPTER for test-only execution."
        )

    from langchain_openai import ChatOpenAI

    provider = settings.PRIMARY_LLM_PROVIDER.lower()
    if provider == "gemini":
        logger.debug("LLM factory: using Gemini model=%s", settings.GEMINI_MODEL)
        return ChatOpenAI(
            model=settings.GEMINI_MODEL,
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=temperature,
        )
    if provider == "ollama":
        logger.debug("LLM factory: using Ollama model=%s", settings.OLLAMA_MODEL)
        return ChatOpenAI(
            model=settings.OLLAMA_MODEL,
            api_key=SecretStr("ollama"),
            base_url=f"{settings.OLLAMA_URL.rstrip('/')}/v1",
            temperature=temperature,
        )
    if provider != "openai":
        raise RuntimeError(f"Unsupported PRIMARY_LLM_PROVIDER: {provider}")
    logger.debug("LLM factory: using OpenAI model=%s", settings.OPENAI_MODEL)
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=temperature,
    )


def get_structured_chat_model(
    response_schema: type[BaseModel], temperature: float = 0
) -> Runnable[Any, Any]:
    """Return a chat model wired to emit structured output matching ``response_schema``.

    Only valid for live mode — mock mode raises LangChain's FakeListChatModel
    which does not support ``with_structured_output``.  Callers should guard
    with ``is_mock_mode()`` before calling this.
    """
    if is_mock_mode():
        raise RuntimeError(
            "get_structured_chat_model() called in mock mode. "
            "Guard with is_mock_mode() and fall back to heuristic path."
        )
    return get_chat_model(temperature).with_structured_output(response_schema)
