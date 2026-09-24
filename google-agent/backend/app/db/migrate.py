from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_alembic_upgrade() -> None:
    """Apply Alembic migrations when running from source (not PyInstaller)."""
    if getattr(sys, "frozen", False):
        return

    try:
        from alembic import command
        from alembic.config import Config

        from app.config import get_settings

        backend_dir = Path(__file__).resolve().parent.parent.parent
        alembic_ini = backend_dir / "alembic.ini"
        if not alembic_ini.is_file():
            logger.warning("alembic.ini not found at %s", alembic_ini)
            return

        settings = get_settings()
        sync_url = settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg://"
        ).replace("sqlite+aiosqlite:///", "sqlite:///")

        cfg = Config(str(alembic_ini))
        cfg.set_main_option("script_location", str(backend_dir / "alembic"))
        cfg.set_main_option("sqlalchemy.url", sync_url)
        command.upgrade(cfg, "head")
        logger.info("Database migrations applied")
    except Exception as exc:
        logger.warning("Alembic migration failed (schema patches will still run): %s", exc)
