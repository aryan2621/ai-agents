import logging
import os

import uvicorn

from app.config import BACKEND_HOST, BACKEND_PORT
from app.main import app, configure_logging

if __name__ == "__main__":
    debug = os.environ.get("DEBUG", "").lower() in {"1", "true", "yes"}
    configure_logging()

    uvicorn.run(
        app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level="debug" if debug else "warning",
        access_log=False,
        reload=debug,
    )
