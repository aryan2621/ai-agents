import os

import httpx

from app.config import _app_data_dir
from app.services.platform import local_llm
from app.services.platform.app_config import oauth_is_configured
from app.services.platform.llm_keys import llm_provider_configured
from app.services.platform.tavily_search import resolve_tavily_api_key

BACKEND_BUILD_ID = "builtin-llm-v1"


def check_storage() -> bool:
    """Chats and settings are JSON files in the data folder; it must be writable."""
    try:
        path = _app_data_dir()
        return path.is_dir() and os.access(path, os.W_OK)
    except OSError:
        return False


async def check_network() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.head("https://www.googleapis.com/")
            return response.status_code < 500
    except Exception:
        return False


async def health_status() -> dict:
    storage_ok = check_storage()
    network_ok = await check_network()
    llm_ok = llm_provider_configured()

    issues: list[dict[str, str]] = []

    if not storage_ok:
        issues.append(
            {
                "code": "database",
                "message": "Chats and settings can't be saved.",
                "remediation": f"Check that {_app_data_dir()} exists and is writable, then restart the app.",
            }
        )
    if not network_ok:
        issues.append(
            {
                "code": "network",
                "message": "No internet connection.",
                "remediation": "Connect to the internet — Google Workspace requires network access.",
            }
        )
    if not llm_ok:
        runtime_missing = local_llm.server_binary() is None
        issues.append(
            {
                "code": "llm",
                "message": (
                    "The built-in AI runtime is missing from this build."
                    if runtime_missing
                    else "No AI model is downloaded yet."
                ),
                "remediation": (
                    "Reinstall the app."
                    if runtime_missing
                    else "Download a model in Settings → Models (it runs on this Mac)."
                ),
            }
        )

    ready = not issues
    status = "ok" if ready else ("unhealthy" if not storage_ok else "degraded")

    return {
        "status": status,
        "ready": ready,
        "issues": issues,
        "capabilities": ["llama.cpp"],
        "web_search_configured": bool(resolve_tavily_api_key()),
        "oauth_configured": oauth_is_configured(),
        "llm_configured": llm_ok,
        "build_id": BACKEND_BUILD_ID,
        "checks": {
            "database": "ok" if storage_ok else "error",
            "network": "ok" if network_ok else "error",
            "llm": "ok" if llm_ok else "error",
        },
    }
