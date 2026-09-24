import os
import sys
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.constants.models import DEFAULT_LLM_MODEL, DEFAULT_OLLAMA_BASE_URL


def _app_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parent.parent / "data"


def _default_sqlite_url() -> str:
    data_dir = _app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "google_agent.db"
    return f"sqlite+aiosqlite:///{db_path}"


def _default_database_url() -> str:
    if os.environ.get("DATABASE_URL", "").strip():
        return os.environ["DATABASE_URL"].strip()
    return _default_sqlite_url()


def is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite")


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
    database_url: str = _default_database_url()
    default_model: str = DEFAULT_LLM_MODEL
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    host: str = "127.0.0.1"
    port: int = 8000
    tavily_search_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("TAVILY_SEARCH_API_KEY", "TAVILY_API_KEY"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
