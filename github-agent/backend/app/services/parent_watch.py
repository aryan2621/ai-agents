"""Shuts the backend down when the app that started it is gone.

The app stops the backend when it quits, but if the app crashes or is force-quit nothing does, and
the backend would keep running (holding port and model) with no window. So it watches its parent:
once that process is gone, macOS hands the backend to launchd and its parent id changes.
"""

import logging
import os
import signal
import threading
import time

from app.services import local_llm

logger = logging.getLogger(__name__)


def start() -> None:
    parent = os.getppid()
    if parent <= 1:
        return  # already detached (started by launchd): nothing to watch

    def watch() -> None:
        while os.getppid() == parent:
            time.sleep(1)
        logger.warning("GitHub Agent is gone; shutting down the backend and its AI model")
        local_llm._kill_at_exit()
        os.kill(os.getpid(), signal.SIGTERM)  # uvicorn's normal shutdown
        time.sleep(5)
        os._exit(0)  # if that shutdown hangs

    threading.Thread(target=watch, name="parent-watch", daemon=True).start()
