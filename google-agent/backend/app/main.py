from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, init_db
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routes import auth, chat, conversations, health, settings, setup, speech

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
        "sqlalchemy.engine",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger("app.api").setLevel(logging.DEBUG if debug else logging.INFO)
    logging.getLogger("app.tools").setLevel(logging.INFO)
    logging.getLogger("app.google").setLevel(logging.INFO)
    logging.getLogger("app.graph").setLevel(logging.INFO)
    logging.getLogger("app.chat").setLevel(logging.INFO)


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Google Agent backend started")
    await init_db()
    logger.info("Database initialized")
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Google Agent Backend", version="1.0.0", lifespan=lifespan)

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
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
    app.include_router(chat.router)
    app.include_router(speech.router)

    return app


app = create_app()
