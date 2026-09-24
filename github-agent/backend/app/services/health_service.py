import httpx
from sqlalchemy import text

from app.config import get_settings, is_sqlite_url
from app.services.tavily_search import resolve_tavily_api_key
from app.services.app_config import oauth_is_configured
from app.services.llm_keys import (
    llm_provider_configured,
    resolve_ollama_base_url,
    ollama_is_reachable,
)
from app.db.database import async_session

BACKEND_BUILD_ID = "ollama-only-v8"


async def check_database() -> bool:
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_network() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.head("https://api.github.com/")
            return response.status_code < 500
    except Exception:
        return False


async def health_status(
    user_ollama_url: str | None = None,
) -> dict:
    db_ok = await check_database()
    network_ok = await check_network()
    ollama_url = resolve_ollama_base_url(user_ollama_url)
    ollama_ok = ollama_is_reachable(ollama_url)
    llm_ok = llm_provider_configured(ollama_url)

    issues: list[dict[str, str]] = []

    if not db_ok:
        settings = get_settings()
        if is_sqlite_url(settings.database_url):
            remediation = "The local database could not be opened. Restart the app or check disk permissions."
            message = "Local database is not available."
        else:
            remediation = "Start PostgreSQL and verify DATABASE_URL in backend/.env, or remove DATABASE_URL to use embedded SQLite."
            message = "PostgreSQL is not reachable."
        issues.append(
            {
                "code": "database",
                "message": message,
                "remediation": remediation,
            }
        )
    if not network_ok:
        issues.append(
            {
                "code": "network",
                "message": "No internet connection.",
                "remediation": "Connect to the internet — GitHub requires network access.",
            }
        )
    if not llm_ok:
        issues.append(
            {
                "code": "llm",
                "message": "Ollama is not running.",
                "remediation": (
                    f"Start Ollama at {ollama_url} and pull a model (e.g. ollama pull ministral-3:8b)."
                ),
            }
        )

    ready = not issues
    status = "ok" if ready else ("unhealthy" if not db_ok else "degraded")

    return {
        "status": status,
        "ready": ready,
        "issues": issues,
        "capabilities": [
            "ollama",
        ],
        "web_search_configured": bool(resolve_tavily_api_key()),
        "oauth_configured": oauth_is_configured(),
        "llm_configured": llm_ok,
        "ollama_configured": ollama_ok,
        "ollama_base_url": ollama_url,
        "build_id": BACKEND_BUILD_ID,
        "checks": {
            "database": "ok" if db_ok else "error",
            "network": "ok" if network_ok else "error",
            "llm": "ok" if llm_ok else "error",
            "ollama": "ok" if ollama_ok else "error",
        },
    }
