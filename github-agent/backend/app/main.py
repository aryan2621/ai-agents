import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import get_store
from app.services import local_llm, parent_watch
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routes import auth, chat, conversations, health, models, settings, setup, speech

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return

    debug = os.environ.get("DEBUG", "").lower() in {"1", "true", "yes"}
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )
    for name in (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "httpx",
        "httpcore",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger("app.api").setLevel(logging.DEBUG if debug else logging.INFO)
    logging.getLogger("app.tools").setLevel(logging.INFO)
    logging.getLogger("app.github").setLevel(logging.INFO)
    logging.getLogger("app.graph").setLevel(logging.INFO)
    logging.getLogger("app.chat").setLevel(logging.INFO)


configure_logging()


async def _warm_model() -> None:
    """Load the model the user selected, and nothing else (no automatic pick)."""
    chosen = next((s.default_model for s in get_store().settings.values() if s.default_model), "")
    if not chosen or local_llm.model_path(chosen) is None:
        return
    try:
        await local_llm.ensure_running(chosen)
    except Exception as exc:  # chat will try again (and report) when it's used
        logger.warning("Could not preload the AI model: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("GitHub Agent backend started")
    get_store()
    logger.info("Storage ready")
    parent_watch.start()
    # Load the AI model now, so the first message doesn't wait for it.
    warmup = asyncio.create_task(_warm_model())
    yield
    warmup.cancel()
    await local_llm.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="GitHub Agent Backend", version="1.0.0", lifespan=lifespan)

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{get_settings().ui_port}",  # next dev
            f"http://127.0.0.1:{get_settings().ui_port}",
            "tauri://localhost",
            "https://tauri.localhost",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(setup.router)
    app.include_router(auth.router)
    app.include_router(conversations.router)
    app.include_router(settings.router)
    app.include_router(models.router)
    app.include_router(chat.router)
    app.include_router(speech.router)

    return app


app = create_app()
