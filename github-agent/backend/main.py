import logging
import os

import uvicorn

from app.config import get_settings
from app.main import app, configure_logging

if __name__ == "__main__":
    debug = os.environ.get("DEBUG", "").lower() in {"1", "true", "yes"}
    configure_logging()

    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="debug" if debug else "warning",
        access_log=False,
        reload=debug,
    )
