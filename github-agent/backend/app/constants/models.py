# "" means automatic: the recommended installed built-in model (app.services.local_llm).
DEFAULT_LLM_MODEL = ""
SPECIALIST_MAX_TOKENS = 4096
SPECIALIST_LLM_TEMPERATURE = 0.1


def normalize_llm_model(model: str) -> str:
    """A built-in model id, or "" (automatic). Names from older versions (Ollama tags, cloud
    models) map to automatic."""
    from app.services.local_llm import model as catalog_model

    name = (model or "").strip()
    return name if catalog_model(name) is not None else ""
