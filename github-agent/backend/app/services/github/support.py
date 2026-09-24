from __future__ import annotations

import logging
import types
from functools import wraps

import httpx

from app.services.scope_registry import InsufficientScopeError
from app.utils.format import linked_action_summary, list_text
from app.utils.tools import tool_error, tool_result

logger = logging.getLogger("app.github")

MAX_LOG_CHARS = 2000
GITHUB_HTTP_TIMEOUT_SEC = 30
GITHUB_API_VERSION = "2022-11-28"


def truncate_log(text: str, max_len: int = MAX_LOG_CHARS) -> str:
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}... [truncated {len(text) - max_len} chars]"


def logged_public_method(fn: types.FunctionType) -> types.FunctionType:
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        logger.info("GitHub API %s input args=%r kwargs=%r", fn.__name__, args, kwargs)
        try:
            result = fn(self, *args, **kwargs)
            logger.info("GitHub API %s output=%s", fn.__name__, truncate_log(str(result)))
            return result
        except InsufficientScopeError:
            raise
        except Exception as exc:
            logger.exception("GitHub API %s error=%s", fn.__name__, exc)
            raise

    return wrapper  # type: ignore[return-value]


def repo_url(owner: str, repo: str) -> str:
    return f"https://github.com/{owner}/{repo}"


def issue_url(owner: str, repo: str, number: int | str) -> str:
    return f"https://github.com/{owner}/{repo}/issues/{number}"


def pull_url(owner: str, repo: str, number: int | str) -> str:
    return f"https://github.com/{owner}/{repo}/pull/{number}"


def resolve_repo(
    owner: str,
    repo: str,
    workspace_context: dict[str, str] | None = None,
) -> tuple[str, str]:
    ctx = workspace_context or {}
    resolved_owner = (owner or ctx.get("owner") or "").strip()
    resolved_repo = (repo or ctx.get("repo") or "").strip()
    if "/" in resolved_repo and not resolved_owner:
        parts = resolved_repo.split("/", 1)
        resolved_owner, resolved_repo = parts[0], parts[1]
    if not resolved_owner or not resolved_repo:
        raise ValueError("owner and repo are required. List or search repos first.")
    return resolved_owner, resolved_repo


def github_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("message"):
            return str(payload["message"])
    except Exception:
        pass
    return response.text or f"HTTP {response.status_code}"


__all__ = [
    "GITHUB_API_VERSION",
    "GITHUB_HTTP_TIMEOUT_SEC",
    "InsufficientScopeError",
    "github_error_message",
    "issue_url",
    "linked_action_summary",
    "list_text",
    "logged_public_method",
    "pull_url",
    "repo_url",
    "resolve_repo",
    "tool_error",
    "tool_result",
]
