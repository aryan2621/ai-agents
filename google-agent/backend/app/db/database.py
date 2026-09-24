import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
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


async def init_db() -> None:
    from app.db import models  # noqa: F401
    from app.db.migrate import run_alembic_upgrade

    try:
        await asyncio.wait_for(asyncio.to_thread(run_alembic_upgrade), timeout=30)
    except TimeoutError:
        logger.warning("Alembic upgrade timed out; continuing with schema patches")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE user_settings "
                "ADD COLUMN IF NOT EXISTS theme VARCHAR(8) DEFAULT 'system'"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE oauth_tokens "
                "ADD COLUMN IF NOT EXISTS granted_scopes TEXT DEFAULT ''"
            )
        )
        workspace_type = _workspace_context_type()
        await conn.execute(
            text(
                f"ALTER TABLE conversations "
                f"ADD COLUMN IF NOT EXISTS workspace_context {workspace_type} DEFAULT '{{}}'"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE user_settings "
                "ADD COLUMN IF NOT EXISTS debug_mode BOOLEAN DEFAULT false"
            )
        )
        await conn.execute(
            text(
                f"ALTER TABLE turn_traces "
                f"ADD COLUMN IF NOT EXISTS ai_messages {workspace_type} DEFAULT '[]'"
            )
        )
        await conn.execute(
            text(
                f"ALTER TABLE turn_traces "
                f"ADD COLUMN IF NOT EXISTS turn_timeline {workspace_type} DEFAULT '[]'"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE user_settings "
                "ADD COLUMN IF NOT EXISTS tavily_search_api_key VARCHAR(255) DEFAULT ''"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE user_settings "
                "ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT false"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE user_settings "
                "ADD COLUMN IF NOT EXISTS gemini_api_key VARCHAR(255) DEFAULT ''"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE user_settings "
                "ADD COLUMN IF NOT EXISTS groq_api_key VARCHAR(255) DEFAULT ''"
            )
        )
