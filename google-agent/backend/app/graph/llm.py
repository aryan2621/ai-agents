from __future__ import annotations

from typing import Any

from app.constants.models import SPECIALIST_LLM_TEMPERATURE, SPECIALIST_MAX_TOKENS, normalize_llm_model
from app.models.chat import LLMSettings

LLM_REQUEST_TIMEOUT_SEC = 120.0
NO_LLM_CONFIGURED = (
    "No AI model is downloaded yet. Download one in Settings → Models."
)


def _active_model_name(settings: LLMSettings | None) -> str:
    return normalize_llm_model(settings.default_model if settings else "")


async def ensure_model_running(settings: LLMSettings | None) -> None:
    """Load the chosen built-in model before build_chat_model is called."""
    from app.services.platform.local_llm import ensure_running

    await ensure_running(_active_model_name(settings))


def build_chat_model(
    settings: LLMSettings | None,
    temperature: float = SPECIALIST_LLM_TEMPERATURE,
    max_tokens: int = SPECIALIST_MAX_TOKENS,
) -> Any:
    from langchain_openai import ChatOpenAI

    from app.services.platform.local_llm import running

    del settings  # the running server already has the chosen model loaded
    current = running()
    if current is None:
        raise RuntimeError(NO_LLM_CONFIGURED)
    base_url, api_key, model_name = current
    # llama-server speaks the OpenAI chat API, tool calls included (--jinja).
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=LLM_REQUEST_TIMEOUT_SEC,
        max_retries=0,
        streaming=True,
    )
