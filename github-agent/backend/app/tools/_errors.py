from collections.abc import Callable
from typing import Any, TypeVar

import httpx

from app.services.scope_registry import (
    AGENT_LABELS,
    InsufficientScopeError,
    agent_scope,
    detect_agent_from_error,
)
from app.utils.tools import tool_error

F = TypeVar("F", bound=Callable[..., str])


def wrap_github_tool(fn: F, tool_name: str) -> F:
    def run(*args: Any, **kwargs: Any) -> str:
        try:
            return fn(*args, **kwargs)
        except InsufficientScopeError:
            raise
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status in (401, 403):
                agent = detect_agent_from_error(str(exc)) or "repos"
                scope = agent_scope(agent) or "repo"
                label = AGENT_LABELS.get(agent, agent)
                raise InsufficientScopeError(agent, scope, label) from exc
            return tool_error(
                f"GitHub API error ({status or 'unknown'}): {exc}",
                next_step="Retry with valid owner/repo or call a list/search tool first.",
            )
        except FileNotFoundError as exc:
            return tool_error(
                str(exc),
                next_step="List or search first, then retry with a valid owner, repo, or number.",
            )
        except Exception as exc:
            if isinstance(exc, TimeoutError) or isinstance(exc, httpx.TimeoutException):
                return tool_error(
                    "GitHub API request timed out. Check your network connection and retry.",
                    next_step="Retry the request. If it keeps failing, check VPN/firewall or GitHub status.",
                )
            return tool_error(str(exc))

    run.__name__ = getattr(fn, "__name__", tool_name)
    run.__doc__ = getattr(fn, "__doc__", None)
    run.__annotations__ = getattr(fn, "__annotations__", {})
    return run  # type: ignore[return-value]
