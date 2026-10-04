from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import _app_data_dir, _env_file_candidates, get_settings

logger = logging.getLogger(__name__)


def _config_path() -> Path:
    for candidate in _env_file_candidates():
        if candidate.is_file():
            return candidate.parent / "app_config.json"
    return _app_data_dir() / "app_config.json"


def load_app_config() -> dict[str, str]:
    path = _config_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: str(v) for k, v in data.items() if isinstance(v, str)}
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read app config: %s", exc)
        return {}


def save_oauth_credentials(client_id: str, client_secret: str) -> Path:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_app_config()
    existing["GITHUB_CLIENT_ID"] = client_id.strip()
    existing["GITHUB_CLIENT_SECRET"] = client_secret.strip()
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return path


def resolve_github_credentials() -> tuple[str, str]:
    config = load_app_config()
    settings = get_settings()
    client_id = (config.get("GITHUB_CLIENT_ID") or settings.github_client_id or "").strip()
    client_secret = (
        config.get("GITHUB_CLIENT_SECRET") or settings.github_client_secret or ""
    ).strip()
    return client_id, client_secret


def oauth_is_configured() -> bool:
    client_id, client_secret = resolve_github_credentials()
    return bool(client_id and client_secret)
