from collections.abc import Callable
from typing import Any, TypeVar

from googleapiclient.errors import HttpError

from app.services.auth.scope_registry import (
    AGENT_LABELS,
    InsufficientScopeError,
    agent_scope,
    detect_agent_from_error,
)
from app.utils.tools import tool_error

F = TypeVar("F", bound=Callable[..., str])


def wrap_google_tool(fn: F, tool_name: str) -> F:
    def run(*args: Any, **kwargs: Any) -> str:
        try:
            return fn(*args, **kwargs)
        except HttpError as exc:
            if exc.resp.status in (401, 403):
                agent = detect_agent_from_error(str(exc)) or tool_name.split("_")[0]
                scope = agent_scope(agent) or ""
                label = AGENT_LABELS.get(agent, agent)
                raise InsufficientScopeError(agent, scope, label) from exc
            return tool_error(
                f"Google API error ({exc.resp.status if exc.resp else 'unknown'}): {exc}",
                next_step="Retry with valid parameters or call a list/search tool first.",
            )
        except InsufficientScopeError:
            raise
        except Exception as exc:
            if isinstance(exc, TimeoutError):
                return tool_error(
                    "Google API request timed out. Check your network connection and retry.",
                    next_step="Retry the request. If it keeps failing, check VPN/firewall or Google service status.",
                )
            return tool_error(str(exc))

    run.__name__ = getattr(fn, "__name__", tool_name)
    run.__doc__ = getattr(fn, "__doc__", None)
    run.__annotations__ = getattr(fn, "__annotations__", {})
    return run  # type: ignore[return-value]
