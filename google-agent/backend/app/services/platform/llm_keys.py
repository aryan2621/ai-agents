from __future__ import annotations

from app.services.platform import local_llm


def llm_provider_configured() -> bool:
    """The built-in AI can answer: a model is downloaded and the llama.cpp runtime is present."""
    return bool(local_llm.installed()) and local_llm.server_binary() is not None
