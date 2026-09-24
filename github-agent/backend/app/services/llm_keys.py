from __future__ import annotations

import os

import httpx

from app.config import get_settings, read_env_keys_from_files
from app.constants.models import DEFAULT_OLLAMA_BASE_URL
from app.services.app_config import load_app_config

OLLAMA_PING_TIMEOUT_SEC = 2.0


def resolve_ollama_base_url(user_settings_url: str | None = None) -> str:
    user_url = (user_settings_url or "").strip()
    if user_url:
        return user_url.rstrip("/")

    config = load_app_config()
    from_config = (config.get("OLLAMA_BASE_URL") or "").strip()
    if from_config:
        return from_config.rstrip("/")

    from_settings = get_settings().ollama_base_url.strip()
    if from_settings:
        return from_settings.rstrip("/")

    from_env = (os.environ.get("OLLAMA_BASE_URL") or "").strip()
    if from_env:
        return from_env.rstrip("/")

    from_file = read_env_keys_from_files(("OLLAMA_BASE_URL",))
    if from_file:
        return from_file.rstrip("/")

    return DEFAULT_OLLAMA_BASE_URL


def ollama_is_reachable(base_url: str | None = None) -> bool:
    url = resolve_ollama_base_url(base_url)
    try:
        response = httpx.get(f"{url}/api/tags", timeout=OLLAMA_PING_TIMEOUT_SEC)
        return response.status_code < 500
    except Exception:
        return False


def llm_provider_configured(ollama_base_url: str | None = None) -> bool:
    return ollama_is_reachable(ollama_base_url)


def apply_keys_to_llm_settings(settings, user_settings=None):
    from app.models.chat import LLMSettings

    merged = settings or LLMSettings()
    user_ollama = (
        getattr(user_settings, "ollama_base_url", None) if user_settings is not None else None
    )
    merged.ollama_base_url = resolve_ollama_base_url(
        user_ollama or merged.ollama_base_url
    )
    return merged
