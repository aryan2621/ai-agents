from __future__ import annotations

import logging
from typing import Any

from app.constants.models import DEFAULT_LLM_TEMPERATURE, normalize_llm_model
from app.models.chat import LLMSettings
from app.types.agents import AgentName

logger = logging.getLogger("app.llm")

OLLAMA_REQUEST_TIMEOUT_SEC = 120.0
NO_LLM_CONFIGURED = (
    "Ollama is not available. Start Ollama locally and pull a model in Settings → Models."
)


def resolve_llm_sampling(
    settings: LLMSettings | None,
    agent_name: AgentName | None = None,
    temperature_override: float | None = None,
) -> tuple[float, float, float | None]:
    del settings, agent_name
    from app.constants.models import (
        SPECIALIST_LLM_TEMPERATURE,
        SPECIALIST_LLM_TOP_P,
        SPECIALIST_REPEAT_PENALTY,
    )

    if temperature_override is not None:
        temperature = max(0.0, min(2.0, temperature_override))
    else:
        temperature = SPECIALIST_LLM_TEMPERATURE

    return temperature, SPECIALIST_LLM_TOP_P, SPECIALIST_REPEAT_PENALTY


def _resolve_ollama_url(settings: LLMSettings | None) -> str:
    from app.services.llm_keys import resolve_ollama_base_url

    return resolve_ollama_base_url(settings.ollama_base_url if settings else None)


def active_model_name(
    settings: LLMSettings | None,
    agent_model: str | None = None,
) -> str:
    return resolve_active_model_name(settings, agent_model)


def resolve_active_model_name(
    settings: LLMSettings | None,
    agent_model: str | None = None,
) -> str:
    requested = (agent_model or (settings.default_model if settings else "") or "").strip()
    return normalize_llm_model(requested)


def _build_ollama(base_url: str, model: str, temperature: float, max_tokens: int) -> Any:
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        num_predict=max_tokens,
        timeout=OLLAMA_REQUEST_TIMEOUT_SEC,
        reasoning=False,
    )


def build_chat_model(
    settings: LLMSettings | None,
    agent_model: str | None = None,
    agent_name: AgentName | None = None,
    temperature_override: float | None = None,
    max_tokens_override: int | None = None,
    validate_model_on_init: bool = True,
) -> Any:
    del validate_model_on_init
    from app.config import get_settings
    from app.constants.models import SPECIALIST_MAX_TOKENS
    from app.services.llm_keys import ollama_is_reachable

    app_settings = get_settings()
    llm = settings or LLMSettings(
        default_model=app_settings.default_model,
        temperature=DEFAULT_LLM_TEMPERATURE,
    )
    temperature, _top_p, _repeat_penalty = resolve_llm_sampling(
        llm,
        agent_name=agent_name,
        temperature_override=temperature_override,
    )

    if max_tokens_override is not None:
        num_predict = max_tokens_override
    else:
        num_predict = SPECIALIST_MAX_TOKENS

    ollama_url = _resolve_ollama_url(llm)
    if not ollama_is_reachable(ollama_url):
        raise RuntimeError(NO_LLM_CONFIGURED)

    model_name = resolve_active_model_name(llm, agent_model)
    return _build_ollama(ollama_url, model_name, temperature, num_predict)
