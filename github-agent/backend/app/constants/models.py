OLLAMA_DEFAULT_MODEL = "ministral-3:8b"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"

DEFAULT_LLM_MODEL = OLLAMA_DEFAULT_MODEL
ROUTER_LLM_MODEL = OLLAMA_DEFAULT_MODEL
SPECIALIST_LLM_MODEL = OLLAMA_DEFAULT_MODEL
ROUTER_MAX_TOKENS = 512
ROUTER_LLM_TEMPERATURE = 0.1
SPECIALIST_MAX_TOKENS = 4096
DEFAULT_LLM_TEMPERATURE = 0.4
SPECIALIST_LLM_TEMPERATURE = 0.1
SPECIALIST_LLM_TOP_P = 0.85
SPECIALIST_REPEAT_PENALTY = 1.15

_LEGACY_CLOUD_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash",
    "llama-3.3-70b-versatile",
    "llama-3.3-70b",
}
_LEGACY_LOCAL_MODELS = {
    "qwen2.5:7b": OLLAMA_DEFAULT_MODEL,
}


def normalize_llm_model(model: str) -> str:
    name = model.strip()
    if not name or name.lower().startswith("gemini") or name.lower() in _LEGACY_CLOUD_MODELS:
        return DEFAULT_LLM_MODEL
    return _LEGACY_LOCAL_MODELS.get(name, name)
