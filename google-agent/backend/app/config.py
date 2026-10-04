import json
import os
import sys
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.constants.models import DEFAULT_LLM_MODEL


APP_DIR_NAME = "Google Agent"


def _ports() -> dict[str, int]:
    """The app's ports, from ports.json at the project root: the one place they are set (the
    Tauri shell, the window's CSP check, the frontend and the dev scripts read it too). Bundled
    into the PyInstaller build."""
    base = Path(getattr(sys, "_MEIPASS", "") or Path(__file__).resolve().parents[2])
    return json.loads((base / "ports.json").read_text(encoding="utf-8"))


PORTS = _ports()
# Where the backend listens. Fixed (the OAuth redirect URI registered with Google names it), and
# deliberately not read from HOST/PORT, which other tools often set.
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = PORTS["backend"]


def _app_data_dir() -> Path:
    """Where chats, settings and models live: the user's app-data folder, outside the app bundle
    so reinstalling or updating the app keeps them. GOOGLE_AGENT_DATA_DIR overrides it."""
    override = os.environ.get("GOOGLE_AGENT_DATA_DIR", "").strip()
    if override:
        path = Path(override).expanduser()
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    elif sys.platform == "win32":
        path = Path(os.environ.get("APPDATA", Path.home())) / APP_DIR_NAME
    else:
        base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
        path = Path(base) / "google-agent"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _env_file_candidates() -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / ".env")
    backend_dir = Path(__file__).resolve().parent.parent
    candidates.extend(
        [
            backend_dir / ".env",
            Path.cwd() / ".env",
            Path.cwd() / "backend" / ".env",
        ]
    )
    unique: list[Path] = []
    for path in candidates:
        if path not in unique:
            unique.append(path)
    return unique


def _resolve_env_file() -> Path:
    for path in _env_file_candidates():
        if path.is_file():
            return path
    return Path(__file__).resolve().parent.parent / ".env"


def read_env_keys_from_files(names: tuple[str, ...]) -> str:
    wanted = set(names)
    for key in names:
        value = (os.environ.get(key) or "").strip()
        if value:
            return value
    for path in _env_file_candidates():
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            if key not in wanted:
                continue
            value = value.strip().strip('"').strip("'")
            if value:
                return value
    return ""


def read_tavily_api_key_from_env_files() -> str:
    return read_env_keys_from_files(("TAVILY_API_KEY", "TAVILY_SEARCH_API_KEY"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_resolve_env_file()),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_client_id: str = ""
    google_client_secret: str = ""
    default_model: str = DEFAULT_LLM_MODEL
    # The dev UI's port (next dev, see scripts/dev.sh); the backend accepts requests from it.
    ui_port: int = Field(default=PORTS["ui"], validation_alias="GOOGLE_AGENT_UI_PORT")
    tavily_search_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("TAVILY_SEARCH_API_KEY", "TAVILY_API_KEY"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
