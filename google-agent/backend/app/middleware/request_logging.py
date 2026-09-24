import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import Message

logger = logging.getLogger("app.api")

SKIP_PATHS = frozenset({"/health"})


def _log_request(method: str, path: str, status: int, duration_ms: float) -> None:
    line = "%s %s %s %.0fms" % (method, path, status, duration_ms)
    if status >= 500:
        logger.warning(line)
    else:
        logger.info(line)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.method == "OPTIONS" or request.url.path in SKIP_PATHS:
            return await call_next(request)

        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        started = time.perf_counter()
        body_bytes = await request.body()

        async def receive() -> Message:
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request = Request(request.scope, receive)
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 1)

        _log_request(request.method, request.url.path, response.status_code, duration_ms)

        if isinstance(response, StreamingResponse):
            headers = dict(response.headers)
            headers["X-Request-ID"] = request_id
            return StreamingResponse(
                response.body_iterator,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )

        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        headers = dict(response.headers)
        headers["X-Request-ID"] = request_id
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
