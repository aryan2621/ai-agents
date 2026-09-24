import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings, is_sqlite_url


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings = get_settings()
_connect_args: dict = {}
if is_sqlite_url(settings.database_url):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, echo=False, connect_args=_connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


def _workspace_context_type() -> str:
    return "JSON" if is_sqlite_url(settings.database_url) else "JSONB"


async def _ensure_columns(conn, table: str, columns: list[tuple[str, str]]) -> None:
    """Add missing columns. SQLite has no ADD COLUMN IF NOT EXISTS."""

    def _existing(sync_conn) -> set[str]:
        inspector = inspect(sync_conn)
        if not inspector.has_table(table):
            return set()
        return {col["name"] for col in inspector.get_columns(table)}

    existing = await conn.run_sync(_existing)
    for name, ddl in columns:
        if name in existing:
            continue
        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


async def init_db() -> None:
    from app.db import models  # noqa: F401
    from app.db.migrate import run_alembic_upgrade

    try:
        await asyncio.wait_for(asyncio.to_thread(run_alembic_upgrade), timeout=30)
    except TimeoutError:
        logger.warning("Alembic upgrade timed out; continuing with schema patches")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        workspace_type = _workspace_context_type()
        await _ensure_columns(
            conn,
            "user_settings",
            [
                ("theme", "theme VARCHAR(8) DEFAULT 'system'"),
                ("debug_mode", "debug_mode BOOLEAN DEFAULT false"),
                ("tavily_search_api_key", "tavily_search_api_key VARCHAR(255) DEFAULT ''"),
                ("onboarding_completed", "onboarding_completed BOOLEAN DEFAULT false"),
                ("gemini_api_key", "gemini_api_key VARCHAR(255) DEFAULT ''"),
                ("groq_api_key", "groq_api_key VARCHAR(255) DEFAULT ''"),
            ],
        )
        await _ensure_columns(
            conn,
            "oauth_tokens",
            [("granted_scopes", "granted_scopes TEXT DEFAULT ''")],
        )
        await _ensure_columns(
            conn,
            "conversations",
            [("workspace_context", f"workspace_context {workspace_type} DEFAULT '{{}}'")],
        )
        await _ensure_columns(
            conn,
            "turn_traces",
            [
                ("ai_messages", f"ai_messages {workspace_type} DEFAULT '[]'"),
                ("turn_timeline", f"turn_timeline {workspace_type} DEFAULT '[]'"),
            ],
        )
