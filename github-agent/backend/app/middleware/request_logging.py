import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.api")

SKIP_PATHS = frozenset({"/health"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """One line per request. Streams pass straight through (their time is time to first byte)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS" or request.url.path in SKIP_PATHS:
            return await call_next(request)
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        log = logger.warning if response.status_code >= 500 else logger.info
        log("%s %s %s %.0fms", request.method, request.url.path, response.status_code, duration_ms)
        return response
